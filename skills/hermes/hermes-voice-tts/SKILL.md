---
name: hermes-voice-tts
description: "Configure TTS providers in Hermes and deliver voice messages across messaging platforms. Covers custom command providers (tts.providers.<name>), Xiaomi MiMo TTS API, Telegram voice bubbles (Opus-encoded ogg + [[audio_as_voice]] directive), Feishu audio messages, WeChat text-only. Use when setting up TTS, adding a provider, or fixing voice delivery (file vs bubble, playback speed)."
platforms: [linux, macos]
---

# Hermes TTS & 渠道语音投递

配置 Hermes 的 TTS 提供商，并把语音正确投递到各消息平台。

## 触发场景
- 配置/更换 TTS 提供商（小米 MiMo、edge、自定义 API）
- 语音在 Telegram/飞书/微信上显示不对（变成文件、播放速度异常）
- 新增自定义 command provider

## 渠道语音支持矩阵（2026-07-31 实测）

| 渠道 | 语音形式 | 关键要求 |
|---|---|---|
| Telegram | ✅ 原生语音气泡 | **Opus 编码** ogg + 消息带 `[[audio_as_voice]]` |
| 飞书 | ✅ 音频消息（可播放） | `.ogg`/`.opus` 自动按 audio 类型上传，无需指令 |
| 微信 | ❌ 只用文字 | `send_voice` 是文件附件兜底（上游未验证气泡），播放不了 |

## 自定义 command provider

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
```

- Placeholders：`{input_path}` `{output_path}` `{format}` `{voice}` `{model}` `{speed}`
- 合法 `output_format`：`mp3/wav/ogg/flac`（`COMMAND_TTS_OUTPUT_FORMATS`）；输出路径扩展名自动按此生成（`.ogg` → Telegram 适配器识别为语音）
- 内置 provider 名（edge/openai/elevenlabs/minimax/xai/mistral/gemini/neutts/kittentts/piper）不能被 shadow
- `text_to_speech` 工具输出 `.ogg` 时 `voice_compatible=false` 属正常，不影响投递

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

## 小米 MiMo TTS

- API 是 **chat/completions + audio modality**，不是 OpenAI 标准 `/audio/speech`（404）
- 合成文本必须放 `role: assistant` 的 content（user 可放风格指令，不出声）
- 支持格式：`mp3/wav/pcm/pcm16`，**不支持 ogg** → 需本地 ffmpeg 转
- 音色：`mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean`
- 现成脚本：`scripts/mimo_tts.py`（支持 mp3/wav/ogg/opus/flac 输出）；完整 API 细节：`references/xiaomi-mimo-tts.md`

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
