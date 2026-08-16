---
name: hermes-voice-tts
description: "Configure TTS/STT providers in Hermes and deliver voice messages across messaging platforms. Covers custom command providers (tts/stt.providers.<name>), Xiaomi MiMo TTS+ASR API (chat/completions+audio, non-standard), Telegram voice bubbles (Opus-encoded ogg + [[audio_as_voice]] directive), Feishu audio messages, WeChat text-only. Use when setting up TTS/STT, adding a provider, fixing voice delivery (file vs bubble, playback speed), or troubleshooting MiMo 402/400."
version: 2.0.0
platforms: [linux, macos]
---

# Hermes TTS/STT & 渠道语音投递

配置 Hermes 的 TTS/STT 提供商，并把语音正确投递到各消息平台。已合并原 `xiaomi-mimo-audio`（小米 MiMo TTS+ASR 专项）的全部内容。

## 触发场景
- 配置/更换 TTS/STT 提供商（小米 MiMo、edge、自定义 API）
- 语音在 Telegram/飞书/微信上显示不对（变成文件、播放速度异常）
- 新增自定义 command provider
- 排查 MiMo 402 / 400 / ASR 识别问题

## 渠道语音支持矩阵（2026-07-31 实测）

| 渠道 | 语音形式 | 关键要求 |
|---|---|---|
| Telegram | ✅ 原生语音气泡 | **Opus 编码** ogg + 消息带 `[[audio_as_voice]]` |
| 飞书 | ✅ 音频消息（可播放） | `.ogg`/`.opus` 自动按 audio 类型上传，无需指令 |
| 微信 | ❌ 只用文字 | `send_voice` 是文件附件兜底（上游未验证气泡），播放不了 |

## 自定义 command provider（通用机制）

config.yaml 配置（`BUILTIN_TTS_PROVIDERS` 之外的名字都是自定义 provider）：

```yaml
tts:
  provider: mimo
  providers:
    mimo:
      type: command
      command: "python3 ~/.hermes/scripts/mimo_tts.py --input {input_path} --output {output_path} --format {format} --voice {voice}"
      output_format: ogg
      voice: mimo_default
      max_text_length: 2000

stt:
  provider: mimo
  providers:
    mimo:
      type: command
      command: "python3 ~/.hermes/scripts/mimo_stt.py --input {input_path} --output {output_path} --language {language} --model {model}"
      language: auto
      timeout: 120
```

- Placeholders：`{input_path}` `{output_path}` `{format}` `{voice}` `{model}` `{speed}` `{language}`
- 合法 `output_format`：`mp3/wav/ogg/flac`；输出路径扩展名自动按此生成（`.ogg` → Telegram 适配器识别为语音）
- 内置 provider 名（edge/openai/elevenlabs/minimax/xai/mistral/gemini/neutts/kittentts/piper）不能被 shadow
- `text_to_speech` 工具输出 `.ogg` 时 `voice_compatible=false` 属正常，不影响投递

## 小米 MiMo 语音 API（已合并 xiaomi-mimo-audio）

小米 MiMo 的 TTS 和 ASR **都不走 OpenAI 标准端点**（`/audio/speech`、`/audio/transcriptions` 均 404），而是走 **`/v1/chat/completions` + audio modality**。官方文档（llms.txt 可读）：https://mimo.mi.com/llms.txt

### 快速结论

| 模型 | 用途 | API 形态 |
|---|---|---|
| `mimo-v2.5-tts` | 内置音色合成 | chat/completions + `audio` 字段 |
| `mimo-v2.5-tts-voicedesign` | 文字描述造音色 | 同上，user 指令必填 |
| `mimo-v2.5-tts-voiceclone` | 音频样本克隆 | 同上 |
| `mimo-v2.5-asr` | 语音转文字 | chat/completions + `input_audio` |

TTS 系列 **限时免费**（2026-07-31 确认）。ASR（mimo-v2.5-asr）定价 **¥0.5/小时**（音频时长计费，非 token）。Hermes 卡片 cost 只追踪 LLM chat 费用，STT/TTS 费用不显示；查 ASR 消费需去小米后台。LLM 定价见 Hermes `agent/usage_pricing.py` 内置表（手动补齐，`hermes update` 会覆盖）。

### TTS API 细节

```
POST https://api.xiaomimimo.com/v1/chat/completions
{
  "model": "mimo-v2.5-tts",
  "messages": [
    {"role": "user", "content": "风格指令(可选)"},
    {"role": "assistant", "content": "要合成的文本"}   ← 文本必须放 assistant！
  ],
  "audio": {"format": "mp3", "voice": "mimo_default"}
}
# 响应: choices[0].message.audio.data (base64)
```

- **文本必须放 `role: assistant`**，放 user 会 400 "messages must contain an assistant role for TTS model"
- 支持格式：`wav/mp3/pcm/pcm16`，**不支持 ogg/opus** → 需本地 ffmpeg 转
- 音色：`mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean`（未知 voice 会 400 并列出可用列表）
- 流式输出需 `pcm16` 格式自行拼接
- 现成脚本：`scripts/mimo_tts.py`（支持 mp3/wav/ogg/opus/flac 输出）

### ASR API 细节

```
POST https://api.xiaomimimo.com/v1/chat/completions
{
  "model": "mimo-v2.5-asr",
  "messages": [{"role": "user", "content": [{"type": "input_audio",
    "input_audio": {"data": "data:audio/mpeg;base64,..."}}]}],
  "asr_options": {"language": "auto"}   # auto/zh/en
}
# 响应: choices[0].message.content (纯文本)
```

- 仅支持 `wav` / `mp3`，base64 后 ≤10MB
- 支持方言（粤/吴/闽南/四川话）+ 中英混说 + 自动标点
- 现成脚本：`scripts/mimo_stt.py`

## Telegram 语音气泡（两个关键坑）

1. **编码必须 Opus**，ffmpeg 默认转出的是 Vorbis：
   ```bash
   ffmpeg -y -i in.mp3 -c:a libopus -b:a 32k -ar 48000 -ac 1 -f ogg out.ogg
   ```
   - Vorbis 编码的 ogg 在 Telegram 上**播放速度异常（快进）**
   - 验证：`file out.ogg` 必须显示 `Opus audio`，不是 `Vorbis audio`
2. **必须带 `[[audio_as_voice]]` 指令**，否则 ogg 走 send_document 显示为文件：
   - `extract_media` 只有检测到该指令才置 `is_voice=True`（防把普通音乐误当气泡）
   - 正确：`hermes send --to telegram:ID "[[audio_as_voice]] MEDIA:/path/x.ogg"`

## 飞书音频

- 适配器 `_FEISHU_OPUS_UPLOAD_EXTENSIONS = {".ogg", ".opus"}` → 上传为 audio 消息，客户端可播放
- 直接 `MEDIA:/path/x.ogg` 即可，无需指令

## 验证方法

```bash
# TTS 端到端（先写文本再合成）
echo "测试" > /tmp/t.txt && python3 ~/.hermes/scripts/mimo_tts.py --input /tmp/t.txt --output /tmp/t.ogg --format ogg
file /tmp/t.ogg   # 应显示 Ogg data, Opus audio

# ASR 端到端
python3 ~/.hermes/scripts/mimo_stt.py --input /tmp/t.mp3 --output /tmp/t.txt --language auto && cat /tmp/t.txt

# Hermes 全链路（agent 内）
from tools.transcription_tools import transcribe_audio
transcribe_audio('/tmp/t.mp3')   # → {success, transcript, provider: mimo}
```

## 改插件/代码后的生效（踩过）

- `/aowen config reload` 只重读 config.yaml，**不重载插件 Python 代码** → 必须重启网关
- 重启前清理：`find ~/.hermes/plugins/<plugin> -name "__pycache__" -type d -exec rm -rf {} +`
- 网关不能在网关进程内重启（SIGTERM 传播被拦截），需用户从外部 shell 执行 `hermes gateway restart`

## 费用显示（卡片 footer cost）

- Hermes cost 全 USD 记账，`usage_pricing.py` 硬编码 `~$X.XX`，**无官方 currency 配置项**
- 飞书卡片显示人民币：hermes-lark-streaming 插件 `hermes_lark_streaming.usd_to_cny_rate: 7.2`（显示层 × 汇率；设为 0 恢复美元）
- 模型显示 n/a：补 `_OFFICIAL_DOCS_PRICING` 内置表（官方 CNY 价 ÷ 7.2 存 USD 记账，显示层还原）；**`hermes update` 会覆盖此文件**，升级后需重补
- 注意：`/v1/models` 返回 200 不代表有 pricing 字段（DeepSeek/Xiaomi 的 models 响应只有 `{id, object, owned_by}`）

## API key 配置坑（402 排查）

- `HTTP 402 Insufficient account balance` = **余额不足**（key 有效但没钱），不是 key 失效
- **`.env` 的 `XIAOMI_API_KEY` 覆盖 `config.yaml` 的 `providers.xiaomi.api_key`**（网关启动时读 .env）。只改 config.yaml 不生效 → 两处同步 + 重启网关
- 改 `.env` 后必须重启网关（环境变量只在启动时加载一次）
- 排查 402 要发真实 chat 请求测，**`/v1/models` 200 不能证明有余额**

## 陷阱

- **改 config.yaml 用 sed/纯文本编辑，绝不用 `yaml.safe_dump` 回写**——会丢全部注释。用 `python` 逐行处理保留注释，或用 `hermes config set`（官方入口）
- 改完配置需**重启网关**生效（`/aowen config reload` 只重读 config.yaml，不重载代码/脚本）
