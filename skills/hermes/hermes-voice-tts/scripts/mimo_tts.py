#!/usr/bin/env python3
"""
小米 MiMo TTS — Hermes 自定义 command provider 脚本

Hermes tts.providers.mimo (type: command) 调用入口：
  python3 mimo_tts.py --input {input_path} --output {output_path} --format {format} --voice {voice}

API: POST https://api.xiaomimimo.com/v1/chat/completions (chat + audio modality)
文档: https://mimo.mi.com/static/docs/quick-start/usage-guide/audio/speech-synthesis-v2.5.md
关键: 文本必须放 role: assistant; 支持 wav/mp3/pcm/pcm16(不支持ogg);
      音色: mimo_default/冰糖/茉莉/苏打/白桦/Mia/Chloe/Milo/Dean
Telegram 语音气泡: --format ogg 时内部用 libopus 编码(48000Hz mono), Vorbis 会播放速度异常
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
DEFAULT_VOICE = "mimo_default"
AVAILABLE_VOICES = ["mimo_default", "冰糖", "茉莉", "苏打", "白桦", "Mia", "Chloe", "Milo", "Dean"]
# 小米 API 支持的格式
API_FORMATS = {"mp3", "wav", "pcm", "pcm16"}
# 本地可转换的输出格式 (Telegram 语音气泡需要 ogg/opus)
LOCAL_FORMATS = {"ogg", "opus", "flac"}


def get_api_key() -> str:
    """从 .env 读取 XIAOMI_API_KEY（Hermes 环境变量或 .env 文件）。"""
    key = os.environ.get("XIAOMI_API_KEY", "")
    if key:
        return key.strip()
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        try:
            with open(env_path, encoding="utf-8") as f:
                m = re.search(r"^XIAOMI_API_KEY=(.+)$", f.read(), re.M)
                if m:
                    return m.group(1).strip()
        except OSError:
            pass
    raise RuntimeError("XIAOMI_API_KEY not found in env or ~/.hermes/.env")


def synthesize(text: str, voice: str, fmt: str) -> bytes:
    """调用小米 TTS，返回音频字节。"""
    if voice not in AVAILABLE_VOICES:
        voice = DEFAULT_VOICE
    payload = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "user", "content": "用自然、清晰的中文朗读以下内容。"},
            {"role": "assistant", "content": text},
        ],
        "audio": {"format": fmt, "voice": voice},
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"MiMo TTS HTTP {e.code}: {body}") from e

    try:
        audio_b64 = data["choices"][0]["message"]["audio"]["data"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"MiMo TTS unexpected response: {json.dumps(data, ensure_ascii=False)[:300]}") from e

    return base64.b64decode(audio_b64)


def main() -> int:
    parser = argparse.ArgumentParser(description="Xiaomi MiMo TTS command provider")
    parser.add_argument("--input", required=True, help="输入文本文件路径")
    parser.add_argument("--output", required=True, help="输出音频文件路径")
    parser.add_argument("--format", default="mp3", help="输出格式: mp3/wav/ogg/opus/flac")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        raise RuntimeError("empty input text")

    fmt = args.format.lower()
    # 本地格式 (ogg/opus/flac): 先从 API 拿 mp3, 再 ffmpeg 转换
    # 注意: Telegram 语音消息要求 Opus 编码 (Vorbis 会导致播放速度异常)
    if fmt in LOCAL_FORMATS:
        tmp_out = args.output + ".tmp.mp3"
        audio = synthesize(text, args.voice, "mp3")
        with open(tmp_out, "wb") as f:
            f.write(audio)
        try:
            if fmt in ("ogg", "opus"):
                # Opus 编码, 48kHz 单声道 (Telegram 语音消息标准)
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_out,
                     "-c:a", "libopus", "-b:a", "32k", "-ar", "48000", "-ac", "1",
                     "-f", "ogg", args.output],
                    capture_output=True, check=True, timeout=120,
                )
            else:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_out, "-f", fmt, args.output],
                    capture_output=True, check=True, timeout=120,
                )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(f"ffmpeg convert to {fmt} failed: {e}") from e
        finally:
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)
    elif fmt in API_FORMATS:
        audio = synthesize(text, args.voice, fmt)
        with open(args.output, "wb") as f:
            f.write(audio)
    else:
        raise RuntimeError(f"unsupported format: {args.format}")

    if not os.path.exists(args.output) or os.path.getsize(args.output) == 0:
        raise RuntimeError("MiMo TTS produced no output")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"MiMo TTS error: {e}", file=sys.stderr)
        sys.exit(1)
