---
name: feishu-bot-cards
description: Send Feishu/Lark cards via bot API or custom-robot webhook.
category: productivity
---

# Feishu / Lark Card & Message Sending (Bot API + Webhook)

Use when sending a Feishu **interactive card** or message to a user/group programmatically:
release notifications, alerts, scheduled broadcasts, bot announcements.

## Two send paths

| Path | When | Credential | Group constraints |
|------|------|-----------|-------------------|
| **Bot API** | Hermes bot is/will be a member of the target chat | `FEISHU_APP_ID` + `FEISHU_APP_SECRET` in `~/.hermes/.env` | Bot must be **in the chat**; **external (cross-tenant) groups** need app-level external-group permission |
| **Custom-robot Webhook** | Quick, no group-member requirement, bypasses external-group permission entirely | Webhook URL `https://open.feishu.cn/open-apis/bot/v2/hook/xxx` | None — add custom robot in group settings and copy webhook |

**For release/announcement bots on external groups, prefer the webhook path** — the bot-API path
requires enterprise-admin approval of external-group permissions (developer cannot self-grant).

## Credentials (bot API)

`.env` values are **single-quoted** (`FEISHU_APP_SECRET='xxx'`) — strip quotes or the token call
fails with `code 10003 invalid param`:

```bash
APP_ID=$(grep '^FEISHU_APP_ID' ~/.hermes/.env | cut -d= -f2- | tr -d "'")
APP_SECRET=$(grep '^FEISHU_APP_SECRET' ~/.hermes/.env | cut -d= -f2- | tr -d "'")
```

## Bot API flow

```bash
# 1. tenant_access_token
TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"${APP_ID}\",\"app_secret\":\"${APP_SECRET}\"}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["tenant_access_token"])')

# 2. send card (receive_id_type=chat_id for groups; user_id/open_id for individuals)
curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id" \
  -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
  -d '{"receive_id":"oc_xxx","msg_type":"interactive","content":"<JSON-string of card>"}'
```

`content` is a **JSON-encoded string** (double-encoded) — `json.dumps(card, ensure_ascii=False)`,
not a raw object.

## Card JSON schema — critical pitfalls

- **`div` `fields[].text` MUST be an object** `{"tag":"lark_md","content":"**bold** …"}`, **NOT a plain
  string**. Plain string → `230099 parse card json err` (`ErrorValue: with value string … mismatched type`).
- `header.title` = `{"tag":"plain_text","content":"…"}`.
- Emoji is fine inside card body/content (unlike release *titles* — see conventions below).
- Full v2 card schema: `config{wide_screen_mode}`, `header{title,template}`,
  `elements[{tag:div,fields|text},{tag:markdown,content},{tag:hr}]`.
- Card body is markdown-ish (`**bold**`), but element tags differ: `div`+`lark_md` for short/fields,
  `markdown` for long blocks. Don't mix up `plain_text` vs `lark_md` inside `text`.

## Error codes

| Code | Meaning | Fix |
|------|---------|-----|
| `230002` | Bot/User can NOT be out of the chat | Add the bot to the target group (group settings → 群机器人 → add). API `POST /im/v1/chats/{chat_id}/members` only works for group admins and needs `im:member` — manual add is simplest. |
| `232033` | No authority to manage **external chats** | The target is a cross-tenant/external group. App needs enterprise-admin-granted external-group permission in developer console, **or switch to custom-robot webhook**. |
| `230099` | Card JSON schema error | Check `fields[].text` object-vs-string, header title tag, double-encoding of content. |
| `10003` | invalid param (token call) | App secret has quotes — strip them (see Credentials). |

## Reusable script

`scripts/release_notify.py` — GitHub release notes (+ optional README) → Feishu card → group.
Supports `--repo X --tag Y --chat oc_xxx [--readme]`. Adapt or copy for any card-notify need.

### 常用项目 (发布通知群)

```bash
# dsh
python3 scripts/release_notify.py --repo techysy/deepseek-harness-fnos --tag 0.1.0-rc.7 --chat oc_ee1b7f03464e3c4f80772afb958f47cc --readme
# 9Router
python3 scripts/release_notify.py --repo techysy/9router-fnos --tag v0.5.55 --chat oc_ee1b7f03464e3c4f80772afb958f47cc --readme
# mihomo-core
python3 scripts/release_notify.py --repo techysy/mihomo-core-fnos --tag v1.1.2 --chat oc_ee1b7f03464e3c4f80772afb958f47cc
```

> ⚠️ 本机直连 api.github.com 会失败（"release not found"），必须走代理：
> `HTTPS_PROXY=http://127.0.0.1:7890 python3 scripts/release_notify.py ...`
> （飞书 API 域名是 CN 直连，不受影响；脚本内对两个域名统一用 urllib，设了代理变量即可）

### 目标群

- 发布通知群：`oc_ee1b7f03464e3c4f80772afb958f47cc`（Hermes Agent 机器人已入群，外部群权限已开通）
- 当前会话 DM 测试：`oc_37febfd71b7fa298f9b60a5b72beb470`
- 用户手动触发才发（不自动定时）；用户说「发发布卡片/通知群/新版本卡片」即触发

## 发版通知完整流程（mihomo-core / fpk 类应用，2026-08 固化）

以 mihomo-core v1.1.2 实战为模板。**通知卡片文案必须先给用户审核，回复"发"才发送。**

### 全流程清单

```text
1. 可行性报告   → 项目 docs/FEASIBILITY-vX.Y.Z.md（需求分析 + 实测链路）
2. 实施         → 改代码 + 版本号三处同步 + CHANGELOG + README 中英
3. 测试         → 完整测试（UI/API/功能/包完整性/连通性），输出 docs/TEST-REPORT-vX.Y.Z.md
4. 使用说明     → docs/USER-GUIDE.md（新功能时更新）
5. 打包         → 同步代码到 NAS 构建目录 → fnpack build 双版本（url+iframe）
6. 交付         → fpk/<app>/ 只留新版，旧包迁 old_fpk/<app>/
7. 文档提交     → git push（CHANGELOG/README/docs）
8. GitHub Release → gh release create vX.Y.Z <双fpk> --title/--notes（tag 纯版本号无 emoji，notes 可 emoji）
9. 群通知       → 拟卡片给用户审核 → 用户确认后 release_notify.py 发发布通知群
```

### mihomo-core 具体命令

```bash
# 3a. 版本号三处同步
sed -i 's/^version               = X.Y.Z-old/version               = X.Y.Z/' manifest
sed -i "s/MIHOMO_APP_VERSION\", \"old\"/MIHOMO_APP_VERSION\", \"new\"/" app/status_server.py
sed -i "s/MIHOMO_APP_VERSION:-old/MIHOMO_APP_VERSION:-new/" cmd/main

# 5a. 同步到构建目录（NAS: /vol1/1000/fnOS Dev/mihomo-core-fnos，二进制不入库保留原有内核+geoip）
tar czf - cmd app/status_server.py manifest wizard config LICENSE | \
  ssh yangyu@192.168.31.101 "cd '/vol1/1000/fnOS Dev/mihomo-core-fnos/' && tar xzf - && chmod +x cmd/* app/*.py"

# 5b. 双版本打包（在构建目录；先 iframe 后 url）
python3 -c "import json;p='app/ui/config';d=json.load(open(p));d['.url']['mihomo-core.Application']['type']='iframe';json.dump(d,open(p,'w'),ensure_ascii=False,indent=2)"
fnpack build && mv mihomo-core.fpk mihomo-core-X.Y.Z-iframe.fpk
python3 -c "import json;p='app/ui/config';d=json.load(open(p));d['.url']['mihomo-core.Application']['type']='url';json.dump(d,open(p,'w'),ensure_ascii=False,indent=2)"
fnpack build && mv mihomo-core.fpk mihomo-core-X.Y.Z.fpk

# 6. 交付 + 归档
cp -f mihomo-core-X.Y.Z*.fpk '/vol1/1000/fnOS App/fpk/mihomo-core/'
mv <旧版>.fpk '/vol1/1000/fnOS App/old_fpk/mihomo-core/'

# 8. Release
gh release create vX.Y.Z mihomo-core-X.Y.Z.fpk mihomo-core-X.Y.Z-iframe.fpk \
  --title "mihomo-core vX.Y.Z" --notes "<从 CHANGELOG 提炼>"

# 9. 群通知（先审核后发送；GitHub API 走代理）
HTTPS_PROXY=http://127.0.0.1:7890 python3 ~/.hermes/skills/productivity/feishu-bot-cards/scripts/release_notify.py \
  --repo techysy/mihomo-core-fnos --tag vX.Y.Z --chat oc_ee1b7f03464e3c4f80772afb958f47cc
```

### 状态页热修（免重装的紧急修复路径）

改 status_server.py 后可不经重装直接生效：

```bash
# 覆盖运行目录文件 → 杀进程（status.pid 里的 pid 可能不准，按精确路径 pkill）→ 重启
scp app/status_server.py nas:/vol4/@appcenter/mihomo-core/
sudo kill $(cat /vol4/@appdata/mihomo-core/status.pid)   # 不行就 pkill -f 'python3 /vol4/@appcenter/mihomo-core/status_server.py'
sudo setsid bash -c 'cd /vol4/@appcenter/mihomo-core && sudo -u mihomo-core env MIHOMO_APP_VERSION=X.Y.Z MIHOMO_STATUS_PORT=9092 MIHOMO_DATA_DIR=/vol4/@appdata/mihomo-core nohup /usr/bin/python3 status_server.py >> /vol4/@appdata/mihomo-core/mihomo.log 2>&1 & echo $! > /vol4/@appdata/mihomo-core/status.pid'
```

坑：`sudo bash -c "... & echo $!"` 里 `$!` 取到的是 bash 的 pid 不是 python 的——重启前先 `ps aux | grep status_server` 确认旧进程真死了。

### v1.1.2 踩坑记录

| 坑 | 教训 |
|---|---|
| JS 字符串里写 `\n` 被 Python 解释成真实换行 | PAGE 渲染后 JS 语法错误、整页卡死——JS 内换行一律用单行文案或 `\n` 双转义 |
| Clash API version 已带 `v` 前缀 | 前端不要再拼 `'v' +` |
| alert 弹窗在嵌入式 iframe 页面体感差 | 结果就地显示在触发行，3 秒后自动恢复 |
| GitHub releases API 直连失败误报"release not found" | 脚本跑之前设 HTTPS_PROXY |
| yaml.dump 重写 config.yaml 丢注释 | Hermes/NAS 配置一律行编辑或精准 patch，禁整文件 dump |
| fnOS 向导只在全新安装出现 | 数据目录残留会跳过向导——文档里写清常规配置入口（App Center 应用设置） |

## Conventions (user preference, applies to their projects)

- GitHub **release tag & title: NO emoji** (tag = pure version). **Body/notes: emoji OK**.
- README: **badges + emoji OK**.
- Wrapper apps around upstream releases: **version aligned to upstream**, no cosmetic suffix
  (e.g. keep `0.1.0-rc.7`, do not add `-pnpm`).
