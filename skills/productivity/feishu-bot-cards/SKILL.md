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

- **Schema 2.0 卡片必须“裸发”，不要用 `{"type":"card","data":<card>}` 套壳。** 套壳会被 API 拒收
  （`230099` / `11310 content's type illegal`）。两层编码仍然存在——外层是 msg 的 `content` 字符串，
  内层就是卡片对象本身：`{"receive_id":..., "msg_type":"interactive", "content": json.dumps(card, ensure_ascii=False)}`。
  拿不准时先发一张最小卡 DM 探一下（`code == 0`）再发全量。
- **Schema read from history is a visual reference, NOT necessarily sendable.** If the user says “参考之前的发布卡片”, retrieve that exact historical message through the Feishu message API, parse its `body.content`, and reuse its **section order, separators, button placement, and text conventions** — but do NOT assume its top-level schema still sends. The send API now rejects the legacy top-level `title` + `elements` schema (both flat and row-array forms) with `230099`, **even a byte-identical resend of a card that was successfully sent in the past** — read-back shows what was accepted THEN, not what is accepted NOW. Always prove sendability with a DM probe (`code == 0`) before drafting the full card; on `230099`, rebuild the same visual layout in the header schema below rather than re-editing content (content was never the problem).
- **Sendable baseline schema** (DM-probe verified): `{"config":{"wide_screen_mode":true},"header":{"title":{"tag":"plain_text","content":"…"},"template":"blue"},"elements":[…]}` with flat elements: `div` (`text` MUST be object `{"tag":"lark_md","content":"…"}`), `hr`, `markdown`. Buttons go inside `{"tag":"action","actions":[…]}` where each button is `{"tag":"button","text":{"tag":"plain_text","content":"…"},"type":"primary","url":"…"}` — a bare button row as a top-level element (legacy style) is rejected.
- **Card header subtitle 副标题规范**：副标题必须放在 `header.subtitle`（`"header": {"title": {"tag":"plain_text","content":"..."}, "subtitle": {"tag":"plain_text","content":"一句话概述/升级指引"}, "template":"blue"}`）。正文第一行不要重复写冗长概述，副标题负责单行说明（如“网关 + 运营两侧同日同号发布，覆盖安装即可、无迁移要求”），正文直接开门见山进核心要点。
- **⚠️ `collapsible_panel` 静默丢弃陷阱**：顶层 `elements` 中放 `collapsible_panel` 在部分卡片交互/客户端下会被**静默剔除**——API 返回 `code: 0 success`，但读回消息或客户端渲染时面板连同内部文字完全消失，用户端根本没有展开能力。发版卡片核心要点**必须直接作为可见 markdown 段落平铺输出**（可以精炼但不要折叠）；不要依赖 `collapsible_panel` 隐藏变更明细。
- **Locating a `230099`:** the error's `index N` is a **UTF-8 byte offset into the card JSON**. Walk cumulative `len(json.dumps(row, ensure_ascii=False).encode('utf-8')) + 1` per element to land on the offending row — much faster than eyeballing the snippet, whose caret math is easy to misread when multibyte characters precede it.
- **`unsupported type of html tag` (HTTP 400, `ErrorValue: code`) = inline code.** Backticks inside a `lark_md` `content` render as `<code>`, which the card parser refuses. Strip them: plain text or `**bold**` instead. Raw `<…>` placeholders (`<NAS_IP>`) parse as HTML tags too — write `NAS_IP` / `http://NAS_IP:28000`. The rejection only fires when the offending characters are present, so **probe with the real body text**, not a placeholder card — an empty probe proving `code == 0` proves nothing about the content you will actually send.
- **`collapsible_panel` is DM-probe verified and is the home for long sections** (user wants verbose detail collapsed, never inline): `{"tag":"collapsible_panel","expanded":false,"header":{"title":{"tag":"div","text":{"tag":"lark_md","content":"标题"}}},"elements":[{"tag":"div","text":{"tag":"lark_md","content":"正文"}}]}` — note `elements` is a **sibling of `header`** (three closing braces after the title text), not nested inside it. `expanded:false` keeps it shut by default — upgrade notes / release-detail walls go here.
- **Schema 2.0 不支持的标签：`note` 与 `title`。** 以 `{"tag":"note",…}` 结尾的卡片会被拒收 `230099`，报
  `cards of schema V2 no longer support this capability; unsupported tag note`。页脚/落款改用 markdown +
  灰色字体：`{"tag":"markdown","content":"<font color='grey'>采集于 … </font>"}`。同理 `schema: "2.0"` 时不支持
  的 legacy 标签都应先换掉再重试，不要反复改内容——错误信息里的 `ErrPath`/`ErrMsg` 直接点名了标签名。
- **`code=0` 不等于卡片能显示——两层验收核对（静默降级 + 内容完整）**：
  1. **静默降级检测**：若客户端不支持当前 schema，服务端仍回 `code: 0`，但用户看到的是 *"请升级至最新版本客户端，以查看内容"*。读回消息检查是否有该占位文字；若有，回退为稳定 schema 1.0 元素重发。
  2. **关键内容抽样检测**：部分不兼容 tag（如未生效的折叠面板）会被静默丢弃而不报错。发送后读回消息必须确认**核心关键字（如版本号、关键特性名）确实存在于读回的 `body.content` 中**，防止内容半截丢失。
- **`schema: "2.0"` 的卡片结构：`header` 与 `body` 是同级，元素装在 `body.elements` 里。**
  写 `{"schema":"2.0","config":{"update_multi":true},"header":{…},"body":{"elements":[…]}}`。
  把 `elements` 直接放在顶层（旧版写法）会被当成缺元素而报结构错。标题对象是
  `{"tag":"plain_text","content":"…"}`，副标题另用 `subtitle`（不是塞进 title 里）。
  `body.elements` 里可直接用 `markdown` 与 `hr` 两种 tag（这两者在 2.0 里是支持的，不要因为 `note` 被拒就以为整类都不行）。
- **`230099` 的 `ErrMsg` 就是诊断结论，不要先怀疑内容。** 错误带 `ErrPath`（如 `ROOT -> body -> elements -> [7](tag: note)`）
  直接点名**第几个元素 + 哪个 tag 不支持**。看到它就去换那个 tag，不要反复重写文案、也不要重发同样的 payload 试运气。
- 行内窄列并排用 `column_set`：`{"tag":"column_set","columns":[{"tag":"column","width":"weighted","weight":1,"elements":[…]}],"flex_mode":"none"}`。
- Emoji is fine inside card body/content (unlike release *titles* — see conventions below).

## Error codes

| Code | Meaning | Fix |
|------|---------|-----|
| `230002` | Bot/User can NOT be out of the chat | Add the bot to the target group (group settings → 群机器人 → add). API `POST /im/v1/chats/{chat_id}/members` only works for group admins and needs `im:member` — manual add is simplest. |
| `232033` | No authority to manage **external chats** | The target is a cross-tenant/external group. App needs enterprise-admin-granted external-group permission in developer console, **or switch to custom-robot webhook**. |
| `230099` | Card JSON schema error | First suspect: **schema 2.0 card wrapped in a `{"type":"card","data":…}` envelope** (bootstrap style) — send the card object bare. Next: legacy top-level `title` schema (rejected outright — rebuild in header schema). Otherwise check `fields[].text` object-vs-string, button wrapped in `action`, double-encoding of content. Use the byte-offset technique above to pinpoint the row. |
| `11310` (`content's type illegal`) | Sent a `type`/`data` enveloped card | Strip the envelope, send the card object itself as the message `content` string. |
| `10003` | invalid param (token call) | App secret has quotes — strip them (see Credentials). |

## Reusable script

`scripts/release_notify.py` — GitHub release notes (+ optional README) → Feishu card → group.
Supports `--repo X --tag Y --chat oc_xxx [--readme]`. Adapt or copy for any card-notify need.

### 常用项目 (发布通知群)

```bash
# dsh
python3 scripts/release_notify.py --repo techysy/deepseek-harness-fnos --tag 0.1.0-rc.7 --chat oc_ee1b7f03464e3c4f80772afb958f47cc --readme
# 10Router
python3 scripts/release_notify.py --repo techysy/10router --tag v1.0.0 --chat oc_d1341c474b7641ccc48c4e85c9b690b4
# mihomo-core
python3 scripts/release_notify.py --repo techysy/mihomo-core-fnos --tag v1.1.2 --chat oc_ee1b7f03464e3c4f80772afb958f47cc
```

> ⚠️ 本机直连 api.github.com 会失败（"release not found"），必须走代理。当前 31.31 本机 mihomo 已停用（7890 释放），代理改用 NAS 101：
> `HTTPS_PROXY=http://<PROXY_HOST>:<PROXY_PORT> python3 scripts/release_notify.py ...`
> （飞书 API 域名是 CN 直连，不受影响；脚本内对两个域名统一用 urllib，设了代理变量即可）
>
> `gh` 查 release 直接加环境变量前缀即可（Go 程序读 HTTPS_PROXY，实测可用）：
> `HTTPS_PROXY=http://<PROXY_HOST>:<PROXY_PORT> gh release list --repo <repo> --limit 3`。
> 若仍连不上再退 git 级代理 `git -c http.proxy=http://<PROXY_HOST>:<PROXY_PORT> gh ...`。

### 目标群与发送渠道

- 发布通知群 / fnOS 发布群：`oc_ee1b7f03464e3c4f80772afb958f47cc`（群名 `fnOS App Development`，Hermes Agent 机器人已入群，外部群权限已开通）——**发普通卡片消息**（该群公告已升级为 docx 类型，API 不可写，见下）
- 10Router 群：`oc_d1341c474b7641ccc48c4e85c9b690b4`（群名 `9+1 Router`）——发普通卡片消息
- 当前会话 DM 测试：`oc_37febfd71b7fa298f9b60a5b72beb470`
- 用户手动触发才发（不自动定时）；用户说「发发布卡片/通知群/新版本卡片」即触发
- 用户说「同步发到当前聊天框和两个发布群」时，目标 = 当前 DM `oc_37febfd71b7fa298f9b60a5b72beb470` + 两个发布群，三处都发
- **硬闸门：任何群卡片都必须先发 DM 预览并得到用户明确确认；禁止先发群再补预览。** 若用户说“参考之前的卡片”，先通过 Feishu 消息 API 或会话历史取得那张实际卡片的完整 `body.content`，再复用其视觉结构；不要凭记忆重建。
- 预览必须先验证 API `code == 0`，再让用户检查实际显示效果；用户报告“文本丢失/格式不对”时，停止群发送，先读取并对比历史卡片 schema 和当前 payload，修复结构后重新发预览。「不要未经用户同意改 schema」约束的是**视觉设计变更**（分区增删、样式重排）；若旧 schema 已被 API 拒收，为使卡片能发出去的**结构转换不是重设计**，照原视觉转即可，但要在回复里说明转了什么。
- **预览的验收标准是「读回消息 + 用户确认」两件事，不是 `code == 0` 一件。** 客户端不认当前 schema 时服务端照样回 `code: 0`，用户侧却是 "请升级至最新版本客户端，以查看内容"——所以 `code == 0` 之后还要 `GET /im/v1/messages/<id>` 读回 `body.content`，确认 `elements` 里是真实卡片结构而非降级占位（判别方法见上文 schema 2.0 静默降级条）。两条都过了再让用户审视觉。

### 生成卡片前先核对事实来源，不要凭记忆排字段

除了 release tag 和下载直链（见下），**卡片里每一个字段都是一次事实声明，都要现查**：硬件型号、盘位数、卷容量、
虚拟机数量、已装应用、端口号——尤其做「配置卡／信息卡」而非发版卡时，整张卡没有一项来自 release，全部要现查。

- 事实的**来源要写进卡里**（如 `<font color='grey'>实测采集 <date> · <来源 IP></font>`），用户才知道这张卡的时效。
- 采集命令与方法见 `lan-device-troubleshooting` skill 的 `references/nas-hardware-inventory.md`。
- **读不到的字段就留白或说不确定，不要补一个像样的数字。** 用户说「可以就这样吧」「不用查了直接做」时，仍然不要编 —— 
  直接告诉他缺哪几项、缺了做出来就是错的；要样图就先做一张明确标注 **SAMPLE／示例数据** 的，不冒充真实配置。
- 「应用场景」这类主观字段是从**已装应用归纳**出来的，属于推断：写进卡后要告诉用户这是归纳的，请他改。
- 容量类字段带上**已用/剩余百分比**：池子长期高水位（如 ZFS >90%）会让卡片从「信息」升级为「该关注了」，值得单独提一句。

### 标点方案不确定就直接问（域名撞名场景）

用户给的域名/产品名可能与**另一个同名不同业务**的服务撞名（例：`minimax.io` 既是 AI 公司也是监控软件品牌）。改代理规则、加白名单、写文案时如果只按字面走，可能把无关业务也路由错。
做法：列出你打算覆盖的域名清单 + 说明哪些按行业判断**没加**及原因（例：`*.com` 那条属安防软件，不进 AI 组），让用户一次确认。

### 拟发版卡片前检查 README 是否过时

用户说「发版卡片」时，**不仅拟卡片，还要扫一眼项目 README**——尤其是功能列表、插件说明、版本号、徽章等章节。如果 README 内容与当前版本实际能力不符（比如插件已支持新数据源但 README 只写了旧的），**主动告知用户并一起更新**，不要等用户发现后反问「你是不是没用拉最新的」。

检查清单：
- badges 版本号是否与最新 release 一致
- 功能/特性描述是否覆盖当前版本新增内容
- 安装说明、端口、路径等是否过时
- 相关插件章节是否反映最新能力

### 拟发版卡片前必须查实最新 Release tag（不能用会话里提到的版本号）

拟写多项目或单项目发版卡片时，**切忌沿用记忆或历史消息里的旧版本号**——用户当前消息里说的版本号也可能是旧的（用户在对话中提过某版本，实际线上已发了下一个版本）。同理，用户可能一次给出多个项目让“都发一下”，而其中每个项目的最新 tag 各不同。

固定动作（每个 repo 各跑一次，不要凭记忆写）：
```bash
HTTPS_PROXY=http://<PROXY_HOST>:<PROXY_PORT> gh release list --repo <repo> --limit 3
```
以 GitHub 上**真实存在的最新 release** 为准起草文案；版本号对不上时先告诉用户实际最新版是什么，再拟稿。

**发布是真在动的 —— 拟稿期间会冒出更新的 tag。** 拟卡到用户审完/发出之间可能隔很久（用户去看卡、去开会），期间对方可能又推了一个版本。所以：拉过 release 之后、**在真正发送前重新拉一次** `gh release list --limit 3`；若出现了更新的 tag，不要默默发旧版，也不要自作主张改成新版 —— **告诉用户「你卡的区间之后又发了 X，要不要把卡改成覆盖到 X」**，由用户拍。区间卡片（「包含 X 之后所有更新」）尤其容易被这一下打穿：卡刚写完，区间终点就过期了。

`gh release view <tag> --json` 的合法字段是固定的（`tagName/name/publishedAt/assets/body/url/...`），**传 `isLatest` 之类不存在的字段会整体报错并打印可用字段列表**——要判断「是不是最新」用 `gh release list --limit 3` 看 Latest 标记，或比较首行 tagName，不要往 `--json` 里猜字段名。

**卡片里的下载直链必须取自 release 的真实资产**（`gh release view <tag> --json assets` 取
`assets[].url`），禁止按命名规律手工拼 `releases/download/...` URL——同一 release 内资产命名风格常不统一
（如并存 `10Router.Setup.1.1.3.exe` / `10Router-Portable-1.1.3.exe` / `10Router-Web-Setup-1.1.3.exe`），
拼错即 404。同理卡片里的文件名、端口等事实先从仓库/资产核一遍再写。

**卡片里要写「本版 N 个提交」时**：`git rev-list --count <上一个已发布tag>..<本tag>`——区间起点必须是**上一个已发布 tag**（不是更早的 tag，也不是 `origin/main`；起点用错会把上一版的提交算进来，而发版后 main 往往又领先 tag 几个 commit，两个方向都会算错）。按类型分布另跑 `git log --format=%s <range>` 后按 `^(\w+)` 归类计数。

统计「issue/PR 关联了多少提交」以 **GitHub 口径**为准：
`gh api repos/<o>/<r>/issues/<N>/timeline --paginate` 数 `event == "referenced"` 的去重 `commit_id`。
提交正文 grep 只做交叉验证——正文提到才算的会漏、编号相近的 issue（#9 vs #91）会误命中，
要用 `#9([^0-9]|$)` 这类边界正则。techysy/10router 这类仓库还有上游快照 ref（`refs/tmp/up*`），
`git log --all` 会把上游提交算进来——报「我们打了多少个补丁」前先
`git for-each-ref --contains <sha>`，落在 `refs/tmp/up*` 的是上游提交要剔除。「提交是否已发布」另跑 `git tag --contains <sha>`，空 = 未发布。

### 多项目发布必须分卡

不同项目或插件默认分别制作、分别发送，不能合并成一张卡片。即使它们在同一生态、同一批次发布（例如 10Router 与 hermes-fry-cards），也必须各自使用独立标题、独立文案、独立 Release 链接和独立预览；只有用户明确要求合并时才合并。这样用户才能分别转发、审核和定位版本。

### 目标群要按项目确认，不能默认同一个群

同一个用户的多个项目，发版卡片的目标群**是分开的**（fnOS 类应用发 fnOS 发布群、路由器类发它自己的群）。用户会逐条给指令（「dsh 发版在 fnos app 群」「10r 发 9+1 群」），也可能一句带过。**不要把一个项目的群套到另一个项目上**；不确定就先问或先发 DM 预览让用户指群。

发卡片是**双闸门**：① 文案先发 DM 预览给用户审核；② 目标群不明确时等用户指群。不要因“上一张发过了”就默认本次同群——卡片文案与目标群各自独立确认。

### 通道/生态适配类插件发版必须明写上游适配情况

若插件定位为上游官方通道或生态组件的替代/适配（如 OpenClaw 通道插件替代停更的官方 `@larksuite/openclaw-lark`），卡片正文开头必须单列小节写明：
- 适配的上游版本区间（如 OpenClaw ≥ 2026.5.4、2.0 SDK）与运行环境（如 Node.js ≥ 22）
- 替代/兼容的官方组件及核心底层变动适配（如 SDK 导出重构、会话存储迁移 SQLite）
- 绝不能只列插件自身新特性，必须先交代与官方体系的兼容与迁移关系。

### 用审核过的精简文案建卡片，别自动拉 GitHub release body

**卡片发送顺序（必须遵守）**：查实 release → 检查 README → 提炼文案 → 根据历史参考或用户要求选择并复刻卡片 schema → 用 Python 构造卡片 → 发 DM 预览 → 用户确认 → 再发目标群。即使用户直接说“发吧”，如果本轮还没有成功的 DM 预览，也要先补 DM 预览，不得跳过审核闸门。

`release_notify.py` 会把 **GitHub release 的完整 body** 转成卡片——对 10Router 这类版本号同号但内容多、含大量技术子项（如"上游 v0.5.69 择优移植：①…②…③…"）的发布，全文直发又长又硬核，用户几乎总会要求精简。正确流程：

1. **先查最新 tag**：批量或重新拟卡前，一律先 `HTTPS_PROXY=... gh release list --repo <repo> --limit 3` 确认最新 release，切忌盲目复用会话历史中提及过的旧版本号。
2. 从 `public/i18n/changelog/<locale>.md` 或 `gh release view` 提炼发布要点草拟卡片（领头的用户可感知新功能优先；**长技术子项压成一行带过**，如多条上游修复合并为"稳定性与体验优化（同步上游）：…等"）。**release notes 只有一行占位**（workflow 自动生成的模板句）时，改从 `gh api repos/<o>/<r>/compare/<上一个已发布tag>...<本tag> --jq '.commits[].commit.message'` 取提交列表 + README 功能节提炼——不要拿占位句当文案来源，也不要因为 notes 空就不敢拟稿。
3. **草稿先给用户审核**，用户点名要删/压的条目（如"上游 v0.5.69 择优移植 简单带过"）按指示精简，再确认。
4. **审核通过后**用审核版文案手写卡片 JSON，**schema 必须用 DM probe 验证过能发的那一种**（历史 legacy 卡片的 top-level `title`/row arrays 多半已被 API 拒收——读回历史只取视觉结构，发送一律用 header schema），直接 POST 发送——不要回头跑 `release_notify.py` 让它抓回冗长 release body 覆盖你精炼的内容。
5. 卡里加 Release 详情 / GitHub 仓库链接即可，不必塞全文。

发送多目标时循环各 chat_id 打同一 card JSON（content 双层编码不变），逐个打印 code==0 确认。

### 手写卡片 JSON 必须用 Python 脚本发，不要 bash 拼 JSON

卡片内容含中文、换行、emoji 时，**禁止在 bash `curl -d` 里手拼 JSON 字符串**——shell 转义（引号嵌套、`\n`）几乎必然产生 230099 parse card json err 或内容被截断。正确做法：整个发送逻辑写成一段 `python3 << 'PYEOF'`（heredoc 内构造 dict → `json.dumps(card, ensure_ascii=False)` 双层编码 → urllib POST），一次成型。飞书 API 域名 CN 直连无需代理。

### 群公告 API 的限制（docx 型公告不可写）

- `PUT/GET /im/v1/chats/{chat_id}/announcement` 对**已升级为 docx 文档类型的群公告**返回 `232097 Unable to operate docx type chat announcement`——飞书未开放此类公告的写 API，机器人改不了。
- 遇到该错误直接改发**普通卡片消息**到群里代替公告，并告知用户公告需手动编辑。用户指定某群走公告、某群走卡片时，公告群不可用就按用户选项回落到卡片（先说明原因）。
- 用户会指定各群发送形式（如「A 群用公告、B 群正常卡片」）——发前按群确认渠道，不要默认两群同形式。

### 一张卡片覆盖一个发布区间（用户说「包含 X 之后所有更新」）

用户会说「发版卡片包含 <某版本> 之后所有更新内容」—— 这**不是**只写最新那个 tag，而是把区间内**每个 release 的要点合成一张卡**。做法：

1. 定区间起点：**上一个已发布 tag**（`gh release list --limit 5` 看；同号重打包/构建段系列时，起点是那个基线 tag，不是系列里的第一个）
2. 拉每个 release 的正文：`gh release view <tag> --json body --jq .body`，逐个读完
3. 标题用**最新 tag**；领头写清区间与规模：`<起点> → <最新>` + `git rev-list --count <起点>..<最新>` 个提交 + 平台/资产数
4. 正文按**主题合并**，不按 release 顺序罗列 —— 多个小版本里的同类改动（如三个 rc 都在改下载体验）合成一条，长技术细节压成一行或塞进 `collapsible_panel`
5. 若有版本号策略变化（如「fpk 版本 = 上游 + 构建段」），必须在卡里单列一条：用户要据此理解为什么版本号是这个形状
6. 下载直链按**最新 tag** 的真实 assets 取（`gh release view <最新tag> --json assets`），区间内旧版本的资产链接不要出现在卡里

**区间终点会过期，起点要在发送前重新核。** 拟稿期间用户可能又发了新版（构建段系列尤其快）——发送前重拉一次 `gh release list --limit 3`；出现新 tag 时**不要默默改卡也不要默默发旧版**，告诉用户「你卡的区间之后又发了 X，要不要把卡改成覆盖到 X」。

**区间内若有多个构建段/rc 被折叠，「覆盖全部内容」= 覆盖折叠后的那张聚合 Release。** 先把 Release 聚合完（见 `github-release-workflow`），再把卡写成覆盖到 carrier tag，两张产物（聚合 Release 正文 + 卡片）内容必须一致——别一边折了 Release、卡片还按旧的逐版本罗列，用户对着两边核对会当成发错。同理，**卡里的「本版 N 个提交」按聚合区间重算**，不是单个构建段的提交数（构建段往往只有一个 fix 提交）。

### Release list 标题对齐：改完历史还要堵源头

用户报「Release list 名字又没对齐」时，**只 `gh release edit` 是不够的** —— 那是历史快照，下一次 CI 还会再飘：

1. 先 `gh release list --limit 30 --json tagName,name` 横向比出所有异类（多前缀 emoji、多字、裸 tag 等），一次改完，不要只改最新那个
2. 对齐方向**必须先问用户**（补 emoji 对齐近版 vs 全部去 emoji），不要自己拍
3. 改完指出源头：`git ls-tree --name-only origin/main .github/workflows/` 列出所有 workflow，逐个 `git show origin/main:<file> | grep -n 'gh release'` 找出硬编码 `--title "🚀 ..."` 的那一行，告诉用户「不改这里，下次 CI 打包还会再飘一次」，并给出改法（一行）
4. 注意：只改**历史 release 记录**，绝不动 git tag

### 发布卡片必须显式写升级命令与「必须重跑 install」的警告

发布一个「新增了注入目标」的插件版本时，卡片正文的 📦 升级 区块必须带上完整命令序列
（`git pull` → `pip install -e .` → `uninstall` → `install` → `gateway restart`），并在卡片里点名
**本版新增了什么注入目标、因此 uninstall 不能省**。只写「升级到最新版」会让用户漏掉 install，
症状是「装了新版但行为没变」，会被误报成「发版没修好」。有新增 hook/patcher 的版本尤其要写。

### Release name/title 与 notes 是两个独立字段

`gh release edit --title X` 只改标题、`--notes-file` 只改正文。workflow 自动创建的 release 标题是裸 tag 名（如 `v1.1.0`），发版后记得 `gh release edit <tag> --title "<项目名> <tag>"` 与历史版本命名对齐；用 `gh release list` 横向对比确认。发布确认项：notes 非空且格式对齐上一版、标题带项目名、资产齐全——三者各验各的，改了 notes 不代表标题对。

### 跳版本号要在发布物料里记账

跳过某个版本号（如 1.0.9 直接发 1.1.0）时，**Release notes 和用户端更新日志（如 public/i18n/changelog/ 三语）都要加一句版本记账**：跳过的原因 + 跳过版本从未打 tag、无产物。不发记账，用户会问「为什么没有 X.Y 版」并怀疑漏更新。

## 发版通知完整流程（mihomo-core / fpk 类应用，2026-08 固化；⚠️ 2026-09 起用户端发版优先看 `github-release-workflow` skill，发布后群通知用本节）

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

### ⚠️ Release Notes 被 workflow 覆盖的坑

build-server.yml 的 `gh release create` 若没传 `--notes`，workflow 会用默认描述（"10Router standalone server package…"）**覆盖**你精心写的 Release Notes。

**修复**（tag 已推送后）：
```bash
gh release edit v1.0.0 --notes-file /tmp/10router-release-notes.md
```

**预防（已落地到 10router 三个 build workflow，可直接抄）**：在 upload/attach step **之前**插一个 ensure step——release 已存在则什么都不做（手工 notes 绝不动），不存在则 `gh release create <tag> --title "<项目名> <tag>" --notes "Release notes pending — see CHANGELOG"`。仅靠 `--notes ""` 占位不够：**多个 workflow 各自 attach 文件时，第一个跑完的会用空 body + 裸 tag 名创建 release**，后续 attach 只加文件不会补 notes——所以必须让任何一个 attach 之前 release 就带着标题和占位 body 存在。

### mihomo-core 具体命令

```bash
# 3a. 版本号三处同步
sed -i 's/^version               = X.Y.Z-old/version               = X.Y.Z/' manifest
sed -i "s/MIHOMO_APP_VERSION\", \"old\"/MIHOMO_APP_VERSION\", \"new\"/" app/status_server.py
sed -i "s/MIHOMO_APP_VERSION:-old/MIHOMO_APP_VERSION:-new/" cmd/main

# 5a. 同步到构建目录（NAS: /vol1/1000/fnOS Dev/mihomo-core-fnos，二进制不入库保留原有内核+geoip）
tar czf - cmd app/status_server.py manifest wizard config LICENSE | \
  ssh <USER>@<NAS_IP> "cd '/vol1/1000/fnOS Dev/mihomo-core-fnos/' && tar xzf - && chmod +x cmd/* app/*.py"

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
| Release Notes 被 workflow 默认描述覆盖 | build-server.yml 的 gh release create 必须显式传 --notes 或 --notes-file；已覆盖用 gh release edit 修复 |

## Conventions (user preference, applies to their projects)

- GitHub **release tag & title: NO emoji** (tag = pure version). **Body/notes: emoji OK**.
- **Card header title: NO emoji for 发版卡片** — the card header carries the project name + version (`Project 1.2.3 发布`), matching the release-title convention. Emoji belongs in the **body** (section bullets, `📦`/`⚠️`/`🔗` markers), never in the header. `scripts/release_notify.py` still hardcodes a `🚀 ` header prefix — when using it for these projects, pass the card through your own builder or strip the prefix; do not let its default leak into a real 发版卡片.
  - **非发版类卡片（配置卡／信息卡／播报卡）header 可用一个 emoji**（如 `🖥️ 我的 NAS · fnNAS`）——该约束来自「版本标题不带 emoji」的发版规范，不要外推到所有卡片。判断依据是卡片用途，不是「卡片」本身。
- README: **badges + emoji OK**.
- Wrapper apps around upstream releases: **version aligned to upstream**, no cosmetic suffix
  (e.g. keep `0.1.0-rc.7`, do not add `-pnpm`).
- README **badge order**: version → downloads-total → Docker/npm → License → stars (last). Remove `last-commit` badge — no decision value for installers.
- **协同卖点必须单列一行**：产品与用户其他项目能配合时（如 mimocode 配 10Router 用最新测试模型），发版卡片正文必须有这一行——用户主动补过的卖点，漏了会被返工。
- 用户发应用截图说「加进 README 当主图」= 把图提交进**仓库**（`docs/images/` + README 徽章后 `<p align="center">` 居中图）并 push，**不是**嵌进飞书卡片；先改 README 再回到卡片任务。
- 用户发二维码/截图说「加在 X 项目底部，对齐 Y 项目的 README」= 两步都要做：① 把图**提交进仓库**（`assets/`，按语义命名，与其他项目的同名资产区分开，如 `feishu-group-qr.jpg`）；② **照抄 Y 项目该段落的版式**（章节标题、引导句、`<div align="center"><img ... width="280">` 包裹、致谢小字格式），只换项目名/群名/链接。落位通常为「相关项目 → 交流群 → 贡献者致谢 → 许可证」。改完必须验证远端：`git show origin/main:README.md | grep <文件名>` + `curl -s -o /dev/null -w '%{http_code}' -L <blob URL>` 应为 200。
- **公开仓库放二维码前先读图核实**：名片类二维码常带「仅限企业内部成员」「N 年内有效」，群邀请码才是「永久有效、任何人可扫」。收图后先用视觉工具读出文字再决定用哪张；两者都收到时说明差异并告知选了哪个及原因。
