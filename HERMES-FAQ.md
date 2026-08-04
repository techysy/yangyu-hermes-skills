# 🐛 yangyu-skills-hub — Hermes 使用 FAQ / FAQ

> 记录日常使用 Hermes Agent 遇到的问题和解决方案，持续更新。
> 适用于 Hermes v0.19.0 + Arch VM + 飞书/钉钉/微信网关环境。

---

## 1. 模型与 API 配置

### 1.1 Auxiliary 任务报 400 "The supported API model names are..."

**现象**：飞书话题标题生成失败，日志报 `HTTP 400: The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed mimo-v2.5`

**原因**：`config.yaml` 中 `auxiliary.title_generation.provider: custom`（**无后缀**）会解析到 DeepSeek API，但 `model: mimo-v2.5` 不是 DeepSeek 支持的模型。

**解决**：
```bash
# 方案 A：所有 auxiliary 走 auto（推荐，当前状态）
hermes config set auxiliary.title_generation.provider auto
hermes config set auxiliary.web_extract.provider auto
hermes config set auxiliary.curator.provider auto

# 方案 B：显式指定 provider 后缀（需自定义 provider 存在）
# hermes config set auxiliary.title_generation.provider custom:mimo
```

**要点**：`provider: custom` 和 `provider: custom:mimo` 是**两个不同的东西**——前者是"自定义默认"，后者是"名为 mimo 的自定义 provider"。无后缀的 `custom` 会 fallback 到主 provider 的 base_url。

### 1.2 402 Insufficient account balance 但 key 明明换过

**现象**：重启网关后仍报 `HTTP 402: Insufficient account balance model=mimo-v2.5`，调试 ID 每次不同。

**原因**：`.env` 和 `config.yaml` 里有两份 API key！网关优先读 **`.env` 的 `XIAOMI_API_KEY`**，`config.yaml` 的 `providers.xiaomi.api_key` 只在部分路径生效。用户只改了 config.yaml，`.env` 还是旧 key（余额耗尽）。

**排查**：
```bash
# 对比两个 key 是否一致
grep '^XIAOMI_API_KEY=' ~/.hermes/.env | sed 's/=.*/=***/'
python3 -c "import yaml; print(yaml.safe_load(open('$HOME/.hermes/config.yaml'))['providers']['xiaomi']['api_key'][:10])"

# 直接测 key 是否能用（发真实 chat 请求，不是 /models！）
# /models 返回 200 ≠ 有余额，402 只在 chat/completions 时暴露
```

**解决**：把 `.env` 的 key 同步成 config.yaml 的新 key，然后**重启网关**（.env 只在启动时加载）。

**教训**：改 key 后必须重启网关；`/models` 200 只能证明 key 有效，不能证明有余额。

### 1.3 修改 .env 后不生效

**现象**：改了 `~/.hermes/.env` 里的 API key，但行为不变。

**原因**：`.env` 环境变量只在**网关启动时**加载一次，运行中修改不生效。

**解决**：`hermes gateway restart`（注意从**网关外部**执行，见 §2.1）。

---

## 2. 网关与插件

### 2.1 "cannot restart or stop the gateway from inside the gateway process"

**现象**：在飞书/终端里执行 `hermes gateway restart` 报 `Blocked: cannot restart or stop the gateway from inside the gateway process`。

**原因**：Hermes 安全机制——从网关进程内重启会 SIGTERM 自己，导致命令永远无法完成。`systemctl --user restart hermes-gateway` 也一样被拦截。

**解决**：**必须从网关外部**的终端执行：
```bash
hermes gateway restart
# 或
systemctl --user restart hermes-gateway
```
Agent 会话内无法完成此操作，需要用户手动执行。

### 2.2 修改插件代码后不生效

**现象**：改了 `~/.hermes/plugins/hermes-lark-streaming/` 下的 `.py` 文件，发 `/aowen config reload` 后行为没变。

**原因**：`/aowen config reload` **只重读 config.yaml，不重载插件 Python 代码**。插件代码在网关启动时 import 一次，之后常驻内存。

**解决**：
```bash
# 1. 清理字节码缓存（可选，保险）
find ~/.hermes/plugins/hermes-lark-streaming -name "__pycache__" -type d -exec rm -rf {} +

# 2. 重启网关（外部执行）
hermes gateway restart
```

**验证**：`grep hermes_lark_streaming ~/.hermes/logs/agent.log | tail` 看加载时间戳。

### 2.3 飞书群聊 @ 消息被拦截

**现象**：飞书群聊里 @机器人 不响应，日志有拦截记录。

**原因**：v0.19.0 的群聊 DM 策略默认拦截非配对用户。

**解决**：`.env` 设置 `FEISHU_GROUP_POLICY=open`（当前环境已配）。

### 2.4 插件升级后行为异常

**现象**：`hermes plugins update hermes-lark-streaming` 后功能异常。

**原因**：插件是 git 安装的（`~/.hermes/plugins/`），update 会 git pull；本地未提交的修改可能冲突或被覆盖。

**解决**：
```bash
cd ~/.hermes/plugins/hermes-lark-streaming
git status          # 看本地修改
git stash           # 保留本地修改再更新
hermes plugins reload hermes-lark-streaming
hermes gateway restart
```

---

## 3. 费用显示与定价

### 3.1 卡片 cost 显示美元 $ 而不是人民币

**现象**：飞书卡片 footer 显示 `$0.021 (估算)`，想看人民币。

**原因**：Hermes 内核 `agent/usage_pricing.py` 硬编码 `label = f"~${amount:.2f}"`，cost 全部以 USD 记账。Hermes **没有**官方的 currency 配置项。

**解决**：在 hermes-lark-streaming 插件做显示层换算：
- `config/reader.py` 加 `usd_to_cny_rate` 配置（默认 7.2）
- `cardkit/elements.py` cost 渲染时 × 汇率显示 `¥`
- `config.yaml`：`hermes_lark_streaming.usd_to_cny_rate: 7.2`

```bash
# 改汇率（不改代码）
hermes config set hermes_lark_streaming.usd_to_cny_rate 7.2
# 设为 0 恢复美元显示
```

### 3.2 模型显示 n/a 没有费用估算

**现象**：卡片 cost 显示 `n/a`，或日志 `cost_source: none, status: unknown`。

**原因**：该模型不在 Hermes 内置定价表（`agent/usage_pricing.py` 的 `_OFFICIAL_DOCS_PRICING`），且 provider 的 `/models` API 不返回 pricing 字段（DeepSeek / Xiaomi 都不返回）。

**解决**：手动补内置表（`agent/usage_pricing.py`）：
```python
("deepseek", "deepseek-v4-flash"): PricingEntry(
    input_cost_per_million=Decimal("1.00") / Decimal("7.2"),   # ¥1.00/M 未命中
    output_cost_per_million=Decimal("2.00") / Decimal("7.2"),  # ¥2.00/M
    cache_read_cost_per_million=Decimal("0.02") / Decimal("7.2"),  # ¥0.02/M 命中
    source="official_docs_snapshot",
    source_url="https://api-docs.deepseek.com/quick_start/pricing",
    pricing_version="deepseek-pricing-2026-07-31",
),
```

**要点**：
- 内置表以 **USD/M tokens** 记账，官方 CNY 定价 ÷ 7.2 存入，显示层再 × 7.2 还原，精确无误差
- **`hermes update` 会覆盖此文件**，升级后需要重新补
- `/models` 返回 200 不代表有 pricing 字段——DeepSeek/Xiaomi 的 models 响应只有 `{id, object, owned_by}`，无 pricing

### 3.3 定价表里没有的模型

2026-07-31 已手动补齐（官方价）：
| 模型 | 输入(未命中) | 输入(命中) | 输出 |
|------|-------------|-----------|------|
| deepseek-v4-flash | ¥1.00/M | ¥0.02/M | ¥2.00/M |
| deepseek-v4-pro | ¥3.00/M | ¥0.025/M | ¥6.00/M |
| mimo-v2.5 | ¥1.00/M | ¥0.02/M | ¥2.00/M |
| mimo-v2.5-pro | ¥3.00/M | ¥0.025/M | ¥6.00/M |

注意：内置表原 deepseek-v4-pro 的 `$1.74/$3.48` 是 2026-05-12 旧快照，已更新为官方最新价。

**TTS/语音（2026-07-31）**：小米 `mimo-v2.5-tts`、`mimo-v2.5-tts-voiceclone`、`mimo-v2.5-tts-voicedesign` **限时免费**。Hermes TTS 工具不做费用追踪（仅 LLM chat 计费），无需配定价表；STT 已配 `mimo-v2.5-asr`（走 xiaomi API），TTS 默认 edge（免费）。

**小米 TTS 接入要点（2026-07-31）：**
- API 是 **chat/completions + audio modality**，不是 OpenAI 标准 `/audio/speech` 端点（404）。文本必须放 `role: assistant` 的 content，user 可放风格指令
- 支持格式：`wav/mp3/pcm/pcm16`，**不支持 ogg**
- 音色：`mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean`
- 接入方式：Hermes `tts.providers.mimo` command provider + `~/.hermes/scripts/mimo_tts.py`
- **Telegram 语音气泡坑**：必须 **Opus 编码** ogg（`-c:a libopus -ar 48000 -ac 1`），ffmpeg 默认转出的 **Vorbis** ogg 播放速度会异常（快进）。验证：`file x.ogg` 应显示 `Opus audio` 而非 `Vorbis audio`
- **`[[audio_as_voice]]` 指令**：Telegram 对 .ogg 默认当普通附件发送（防音乐误判），消息必须带 `[[audio_as_voice]]` 指令才会走语音气泡：`hermes send --to telegram "[[audio_as_voice]] MEDIA:/path/x.ogg"`。TTS 工具返回的 MEDIA: 自带该指令
- STT 价格：mimo-v2.5-asr ¥0.5/小时（音频时长计费，非 token）
- 渠道支持：Telegram✅ 语音气泡（需 `[[audio_as_voice]]` + Opus ogg）、飞书✅ 音频消息（ogg 直接可播）、微信❌ 只用文字

---

## 4. 会话与话题

### 4.1 飞书话题的模型切换不生效/重置

**现象**：在飞书话题里 `/model` 切换模型，但重启网关后变回默认。

**事实**：Hermes 按会话存储模型（`state.db` sessions 表 `model` 字段），**重启网关不会重置**。每个话题的 `/model` 只影响该会话，新话题用 config 默认模型。

**排查**：
```bash
sqlite3 ~/.hermes/state.db "SELECT id, model FROM sessions ORDER BY started_at DESC LIMIT 5;"
```

---

## 5. 其他

### 5.1 群聊/钉钉消息格式

**偏好**：一屏内显示完，单行 20~25 字，不提冗余指标。不用 Pillow 做中文图。技术讨论简洁直接。

### 5.2 飞书表格渲染

`feishu-table-render` skill：飞书 Markdown 表格需 `post+md` 渲染，`final_response_markdown` 必须放在 `display:` 配置节下。

---

## 更新记录

- 2026-07-31：初版，整理模型/API key/网关/插件/定价/话题 5 类 12 条
