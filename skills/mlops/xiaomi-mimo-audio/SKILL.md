---
name: xiaomi-mimo-audio
description: "Xiaomi MiMo 语音 API 接入（TTS 合成 / ASR 识别）——非标准 chat/completions+audio 端点、Hermes command provider 配置、Telegram 语音气泡（Opus 编码 + [[audio_as_voice]]）、渠道支持矩阵"
platforms: [linux, macos]
metadata:
  hermes:
    related_skills: [hermes-voice-tts]
---

# Xiaomi MiMo 语音 API 接入

小米 MiMo 的 TTS 和 ASR **都不走 OpenAI 标准端点**（`/audio/speech`、`/audio/transcriptions` 均 404），而是走 **`/v1/chat/completions` + audio modality**。官方文档（llms.txt 可读）：https://mimo.mi.com/llms.txt

## 快速结论

| 模型 | 用途 | API 形态 |
|---|---|---|
| `mimo-v2.5-tts` | 内置音色合成 | chat/completions + `audio` 字段 |
| `mimo-v2.5-tts-voicedesign` | 文字描述造音色 | 同上，user 指令必填 |
| `mimo-v2.5-tts-voiceclone` | 音频样本克隆 | 同上 |
| `mimo-v2.5-asr` | 语音转文字 | chat/completions + `input_audio` |

TTS 系列 **限时免费**（2026-07-31 确认）。ASR（mimo-v2.5-asr）定价 **¥0.5/小时**（音频时长计费，非 token）。Hermes 卡片 cost 只追踪 LLM chat 费用，STT/TTS 费用不显示；查 ASR 消费需去小米后台。LLM 定价（mimo-v2.5 等）见 Hermes `agent/usage_pricing.py` 内置表（手动补齐，`hermes update` 会覆盖）。

## Hermes 接入：command provider（零 Python 改核心）

`tts.providers.<name>: type: command` 和 `stt.providers.<name>: type: command` 是官方机制（同 PR #17843），占位符：`{input_path} {output_path} {format} {voice} {language} {model}`。

### config.yaml 配置

```yaml
tts:
  provider: mimo
  providers:
    mimo:
      type: command
      command: "python3 ~/.hermes/scripts/mimo_tts.py --input {input_path} --output {output_path} --format {format} --voice {voice}"
      output_format: ogg      # ogg 才能发 Telegram 语音气泡; mp3/wav 也行
      voice: mimo_default

stt:
  provider: mimo
  providers:
    mimo:
      type: command
      command: "python3 ~/.hermes/scripts/mimo_stt.py --input {input_path} --output {output_path} --language {language} --model {model}"
      language: auto
      timeout: 120
```

现成脚本：`scripts/mimo_tts.py`、`scripts/mimo_stt.py`（已部署在 `~/.hermes/scripts/`）。

## TTS API 细节

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
- 支持格式：`wav/mp3/pcm/pcm16`，**不支持 ogg/opus**
- 音色：`mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean`（未知 voice 会 400 并列出可用列表）
- 流式输出需 `pcm16` 格式自行拼接

## ASR API 细节

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

## Telegram 语音气泡（两个坑缺一不可）

1. **必须 Opus 编码**：ffmpeg 默认转出的 ogg 是 **Vorbis**，Telegram 播放速度会异常（快进）。正确命令：
   ```bash
   ffmpeg -y -i in.mp3 -c:a libopus -b:a 32k -ar 48000 -ac 1 -f ogg out.ogg
   ```
   验证：`file out.ogg` 应显示 `Opus audio` 而非 `Vorbis audio`
2. **必须带 `[[audio_as_voice]]` 指令**：Hermes 对 Telegram 的 .ogg 默认当普通附件发（防音乐误判，见 `should_send_media_as_audio`，只有 `is_voice=True` 才走 sendVoice）：
   ```bash
   hermes send --to telegram:CHAT_ID "[[audio_as_voice]] MEDIA:/path/x.ogg"
   ```
   TTS 工具返回的 MEDIA: 自带该指令，无需手加。

## 渠道支持矩阵（用户确认 2026-07-31）

| 渠道 | 语音 | 说明 |
|---|---|---|
| Telegram | ✅ 语音气泡 | 需 Opus ogg + `[[audio_as_voice]]` |
| 飞书 | ✅ 音频消息 | .ogg 直接可播（adapter 转 opus 上传） |
| 微信 | ❌ 只用文字 | 微信无语音气泡，附件播放不了；用户偏好微信一律文字 |

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

## 陷阱

- **改 config.yaml 用 sed/纯文本编辑，绝不用 `yaml.safe_dump` 回写**——会丢全部注释（本次踩过，靠备份恢复）。用 `python` 逐行处理保留注释，或用 `hermes config set`（官方入口）
- 改完配置需**重启网关**生效（`/aowen config reload` 只重读 config.yaml，不重载代码/脚本）
- 网关进程内不能 `hermes gateway restart`（SIGTERM 自杀），需外部终端执行
- .env 与 config.yaml 双份 key：网关优先读 `.env` 的 `XIAOMI_API_KEY`，两处必须同步；`/v1/models` 返回 200 ≠ 有余额（402 只在 chat 请求暴露）
