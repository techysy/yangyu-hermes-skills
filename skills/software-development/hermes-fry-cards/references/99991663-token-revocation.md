# 飞书 99991663 Invalid access token 排查

> 2026-08-24 实战案例。症状：卡片创建/更新报 `code=99991663 Invalid access token for authorization`，卡片卡 loading，回落纯文本同样失败（gateway 层也报同一错误）。

## 诊断链（按序执行，每步排除一个假设）

1. **验证凭据本身有效**：从 `~/.hermes/.env` 取 app_id/app_secret，直接 POST
   `https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal`
   - `code=0` → 凭据有效，问题在 token 缓存或被服务端吊销
   - `code=10003 invalid param` → 先检查 `.env` 值是否带引号未剥（`v.strip().strip("'\"")`），再怀疑凭据本身
2. **测 token 幂等性**：连续取两次 token 比较是否相同
   - 相同 → 同 secret 取 token 幂等、不互踢，**排除多实例互踢假设**
3. **检查代理绕过**：gateway 带 `http_proxy` 时，用
   `requests.utils.should_bypass_proxies(url, no_proxy=...)` 验证
   - requests 只认精确域名和 `.suffix` 后缀写法；`*.feishu.cn` 通配符不被识别，
     但 no_proxy 里同时列了精确域名 `open.feishu.cn` 即可兜底
4. **对比历史日志频率**：`grep -c 99991663 ~/.hermes/logs/agent.log*`
   - 历史为 0、今天突发 → 外部因素（飞书侧吊销），不是本地代码回归
5. **失效时距分析**：找最后一次 `card_created` 成功时间与首次 99991663 的间隔
   - 间隔远短于 7200s（如案例中的 4 分钟）→ token 被服务端提前吊销

## 根因结论

飞书开放平台后台的 app 配置变更（保存权限、发布版本、停用再启用）会**立即吊销所有已发出的 tenant_access_token**。SDK `lark-oapi` 的 `TokenManager` 用类级 `LocalCache` 缓存 token（提前 10 分钟过期），对服务端主动吊销无感知——缓存里的旧 token 会一直被使用直到自然过期。

## 兜底机制（已部署）

`~/.hermes/scripts/feishu-token-watchdog.sh` 以 no_agent cron 每 30 分钟运行：
扫 `journalctl --user -u hermes-gateway` 近 5 分钟内的 99991663，发现即
`systemctl --user restart hermes-gateway.service`。空窗最长约 30 分钟。

注意：agent 会话内不能触发 gateway 重启（SIGTERM 会杀死自身会话，terminal 工具也会拦截该命令）；watchdog 能做是因为它作为独立 cron 进程跑在 gateway 之外。

## 改进方向（已实施 — commit 7613f2e）

插件层捕获 99991663 后自动清 `lark_oapi.core.token.manager.TokenManager.cache` 并重试一次，空窗缩到秒级且无需重启网关。

实现位于 `hermes_fry_cards/feishu.py`：

```python
FEISHU_TOKEN_INVALID_CODE = 99991663

# _checked_call 中新增分支
if exc.code == FEISHU_TOKEN_INVALID_CODE:
    self.invalidate_token_cache()
    resp = await call()  # SDK 自动取新 token
    return resp

# 清缓存方法 — 兼容 LocalCache 和自定义 ICache
def invalidate_token_cache(self) -> None:
    from lark_oapi.core.token.manager import TokenManager
    cache = getattr(TokenManager, "cache", None)
    if cache is None:
        return
    key = f"self_tenant_token:{self.config.app_id}"
    inner = getattr(cache, "cache", None)
    if isinstance(inner, dict):
        inner.pop(key, None)
    elif hasattr(cache, "set"):
        cache.set(key, "", 0)
```

发版后若仍见连续 99991663 超过 1 分钟才需要人工介入。
