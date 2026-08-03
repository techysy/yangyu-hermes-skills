---
name: hermes-cost-management
description: "Manage Hermes API costs — check provider account balances (DeepSeek etc.) and configure model pricing (built-in pricing table, CNY↔USD, ¥ cost display in cards). Use when user asks about balance, 余额, 定价, cost display, or model pricing."
version: 1.0.0
platforms: [linux, macos]
---

# Hermes 成本管理（余额查询 + 模型定价）

管理 Hermes 的 API 成本：查询各提供商账户余额、配置模型定价、控制卡片费用显示。

## 一、查询 API 余额

### DeepSeek

余额端点：`https://api.deepseek.com/user/balance`

```bash
# 加载凭据后调用
export $(grep -v '^#' ~/.hermes/.env | xargs)
curl -s https://api.deepseek.com/user/balance \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

返回示例：
```json
{
  "is_available": true,
  "balance_infos": [{"currency": "CNY", "total_balance": "6.53", "granted_balance": "0.00", "topped_up_balance": "6.53"}]
}
```

- `total_balance` = `granted_balance`（赠送）+ `topped_up_balance`（充值）
- 输出给用户时只需余额数字（如 `6.53 元`），不必展示完整 JSON 或过程

### Xiaomi MiMo

**无公开余额查询 API**。已测试 `/user/balance`、`/v1/user/balance`、`/account/balance`、`/billing/balance` 等十余个端点全部返回 404。API 本身可用（`/v1/models` 正常），但无余额/用量接口。余额需登录后台手动查看：https://platform.xiaomimimo.com

### 限制
- DeepSeek **没有公开日用量 API**（`/user/usage`、`/dashboard/billing/usage` 等均 404），日用量需官网查看：https://platform.deepseek.com/usage
- 注意：`/v1/models` 返回 200 ≠ 有余额。**402 Insufficient account balance** = 余额不足（key 有效但没钱），只在真实 chat 请求时暴露

## 二、配置模型定价

### 定价解析链（get_pricing_entry 顺序）
1. `resolve_billing_route()` 按 provider/base_url 决定 billing_mode
2. `openrouter` → 实时拉 OpenRouter models API
3. **provider 有 base_url** → 拉 `/v1/models`，**仅当响应含 `pricing` 字段**才用
4. fallback → 内置表 `_OFFICIAL_DOCS_PRICING`（`agent/usage_pricing.py`）
5. 都没有 → `status=unknown, label=n/a`（卡片显示 n/a）

**关键事实**：DeepSeek 和 Xiaomi 的 `/v1/models` **都不返回 pricing 字段**（只有 id/object/owned_by），所以实际全靠内置表。内置表没有的模型显示 n/a，直到手动补条目。

### 给内置表加/改定价

编辑 `agent/usage_pricing.py` 的 `_OFFICIAL_DOCS_PRICING`，key 是 `(provider名, 模型名)` 二元组：

```python
(
    "xiaomi",
    "mimo-v2.5",
): PricingEntry(
    input_cost_per_million=Decimal("1.00") / Decimal("7.2"),
    output_cost_per_million=Decimal("2.00") / Decimal("7.2"),
    cache_read_cost_per_million=Decimal("0.02") / Decimal("7.2"),
    source="official_docs_snapshot",
    source_url="https://platform.xiaomimimo.com",
    pricing_version="xiaomi-mimo-pricing",
),
```

- 单位是 **USD / 百万 tokens**。中国厂商官网价是 CNY，**÷7.2 折算成 USD 存储**，显示层乘回 → 精确人民币价
- `cache_read_cost_per_million` = "输入(命中缓存)" 价；未命中 = `input_cost_per_million`
- 不要设 `cache_write` 除非厂商明确有写缓存价（DeepSeek/MiMo 都没有）

### 卡片 footer 显示人民币（飞书）
若用 hermes-lark-streaming 插件显示卡片 cost：
- 插件 config `hermes_lark_streaming.usd_to_cny_rate: 7.2`（显示层 × 汇率；设为 0 恢复美元）
- 需要插件实现 cost 字段的 USD→CNY 换算与 `¥` 符号

## 陷阱
- **`hermes update` 会覆盖 `usage_pricing.py` 的改动** — 更新后必须重新补条目。维护定价快照（见 references/）照抄即可
- **改插件代码 ≠ 生效**：`config reload` 只重读 config.yaml，**不重载插件代码**。改 .py 后必须清 `__pycache__` + 重启网关
- **⚠️ 绝不 `yaml.safe_dump` 重写 config.yaml**：会**删光所有注释**。正确姿势：`hermes config set` 单键修改；复杂块用行级编辑（保留注释）；编辑前先备份。改完验证注释数 > 0

## 参考
- `references/pricing-snapshot.md` — DeepSeek V4 / Xiaomi MiMo 官方定价快照
- 渠道连通性诊断 → `llm-api-channel-health` 技能
- provider 配置/auxiliary provider 坑 → `custom-llm-provider` 技能
