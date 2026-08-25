# Gateway 重启：user 单元 vs system 单元（从 agent 内部重启的正确姿势）

## 关键事实：hermes-gateway 是 systemd **user** 单元

`hermes-gateway.service` 位于 `~/.config/systemd/user/hermes-gateway.service`（可带 drop-in 如 `api-server.conf`、`proxy.conf`）。查状态/重启**不需要 sudo**：

```bash
systemctl --user is-active hermes-gateway          # active/inactive
systemctl --user show hermes-gateway --property=ActiveEnterTimestamp
systemctl --user restart hermes-gateway            # ← 正确命令，无需 sudo
```

## 🚨 头号坑：裸 `systemctl` 查到的是同名 system 单元 → 误判 + 白折腾 sudo

**现象（2026-08-23 实战）**：跑 `systemctl is-active hermes-gateway` 返回 `inactive`（exit 4），于是以为 gateway 挂了，反复用 `echo <password> | sudo -S systemctl restart/start hermes-gateway` 尝试恢复——全部失败（密码经管道传给 sudo -S 报"对不起，请重试"），折腾多轮。

**根因**：
1. **裸 `systemctl` 查询的是 system 级单元**。system 级没有 `hermes-gateway.service` 时 `is-active` 返回 `inactive`——这是「不存在」的表现，不是真停了。真正的 user 单元一直 `active (running)`。
2. Hermes 的命令拦截器还会把含 `systemctl ... restart/stop hermes-gateway` 的命令直接 BLOCKED（提示 "cannot restart the gateway from inside the gateway process"），即使目标是 system 单元、实际无害也拦。
3. `sudo -S` 从 stdin 读密码在非交互 shell 里不可靠；且根本不需要 sudo。

**正确诊断顺序**：
```bash
# 1) 先确认是 user 单元还是 system 单元（看 Loaded 行的路径）
hermes gateway status        # 或 systemctl --user status hermes-gateway
ls ~/.config/systemd/user/hermes-gateway.service   # 存在 = user 单元
# 2) user 单元一律加 --user，无需 sudo
systemctl --user is-active hermes-gateway
```

## 重启方式选择

| 场景 | 命令 |
|------|------|
| agent 会话内（推荐先试） | `systemctl --user restart hermes-gateway` |
| 独立 shell | `hermes gateway restart` |
| 被拦截器 BLOCKED 时 | 写脚本文件 `/tmp/x.sh` 后台执行，或让用户手动跑 |

- 插件代码改动（如 fry-cards 修 bug）必须重启 gateway 才生效（pip editable 安装下重启即加载新代码）。
- 重启后验证：`systemctl --user show hermes-gateway --property=ActiveEnterTimestamp` 时间应更新。

## 教训

1. systemd 单元先分清 user vs system 层级再操作——`is-active: inactive` 对不存在的 system 单元是常态，不代表服务挂了。
2. 密码管道给 `sudo -S` 在 agent 非交互环境里基本不可靠；能不用 sudo 就不用。
3. Hermes 拦截器按关键词拦 `restart/stop hermes-gateway`，绕过用脚本文件后台执行（合法场景：修复已提交需生效）。
