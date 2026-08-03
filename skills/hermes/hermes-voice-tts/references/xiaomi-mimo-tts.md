# Xiaomi MiMo TTS API 细节

> 来源：https://mimo.mi.com/static/docs/quick-start/usage-guide/audio/speech-synthesis-v2.5.md（2026-07-31 实测验证）
> 模型：mimo-v2.5-tts / mimo-v2.5-tts-voiceclone / mimo-v2.5-tts-voicedesign（限时免费）

## 端点与格式

- **端点**：`POST https://api.xiaomimimo.com/v1/chat/completions`
- **不是** OpenAI 标准 `/audio/speech`（该路径 404）
- 认证：`Authorization: Bearer <XIAOMI_API_KEY>`（或 `api-key` header）

## 请求体

```json
{
  "model": "mimo-v2.5-tts",
  "messages": [
    {"role": "user", "content": "风格指令（可选，不出声）"},
    {"role": "assistant", "content": "要合成的文本（必填）"}
  ],
  "audio": {"format": "mp3", "voice": "Chloe"}
}
```

### 硬性规则（实测踩坑）

1. **文本必须放 `role: assistant`**。放 user 会报：`messages must contain an assistant role for TTS model`
2. **voice 必须来自列表**。`"default"` 会报：`Unknown voice: default. Available voices: [mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean]`
3. 支持格式：`mp3 / wav / pcm / pcm16`。**不支持 ogg**（报 `Unsupported audio format: ogg`）

## 响应

```json
{
  "choices": [{
    "message": {
      "audio": {"id": "...", "data": "<base64 音频>", "expires_at": 0, "transcript": null}
    }
  }]
}
```

- 音频在 `choices[0].message.audio.data`，base64 编码，解码即文件

## 模型差异

| 模型 | 功能 | 限制 |
|---|---|---|
| mimo-v2.5-tts | 内置音色合成 | 支持歌唱模式；不支持音色设计/克隆 |
| mimo-v2.5-tts-voicedesign | 文本描述生成音色 | 不支持内置音色/歌唱/克隆 |
| mimo-v2.5-tts-voiceclone | 音频样本克隆音色 | 不支持内置音色/歌唱/设计 |

## 风格控制

- **自然语言控制** → 放 user content（一句话描述语气/速度/情绪）
- **标签控制** → 放 assistant content 文本内（`(style)` 起始标签 + 细粒度标签）
- 支持导演模式（角色/场景/指导 三维描述）

## 流式

- 低延迟流式输出已恢复；流式时指定 `pcm16` 格式便于拼接
- 非流式（本脚本用的方式）直接拿完整 base64

## 相关链接

- llms.txt：https://mimo.mi.com/llms.txt（AI 可读文档索引）
- 平台后台（余额/用量）：https://platform.xiaomimimo.com
- 注意：MiMo-V2 系列 2026.6.30 已下线，模型名用 V2.5
