#!/usr/bin/env python3
"""
小米 MiMo STT (ASR) — Hermes 自定义 command provider 脚本

Hermes stt.providers.mimo (type: command) 调用入口：
  python3 mimo_stt.py --input {input_path} --output {output_path} --language {language} --model {model}

API: POST https://api.xiaomimimo.com/v1/chat/completions (chat + input_audio)
文档: https://mimo.mi.com/static/docs/quick-start/usage-guide/audio/Speech-Recognition.md
支持: wav / mp3 (base64 ≤10MB), 语言 auto/zh/en (含方言)
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB


def get_api_key() -> str:
    """从环境变量或 ~/.hermes/.env 读取 XIAOMI_API_KEY。"""
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


def mime_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav":
        return "audio/wav"
    return "audio/mpeg"  # mp3 及其他


def transcribe(audio_path: str, language: str = "auto") -> str:
    """调用小米 ASR，返回识别文本。"""
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise RuntimeError(
            f"audio {len(audio_bytes)} bytes exceeds 10MB limit — convert/split first"
        )
    audio_b64 = base64.b64encode(audio_bytes).decode()

    payload = {
        "model": "mimo-v2.5-asr",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": f"data:{mime_for(audio_path)};base64,{audio_b64}"
                        },
                    }
                ],
            }
        ],
        "asr_options": {"language": language},
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"MiMo ASR HTTP {e.code}: {body}") from e

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"MiMo ASR unexpected response: {json.dumps(data, ensure_ascii=False)[:300]}"
        ) from e
    return text or ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Xiaomi MiMo ASR command provider")
    parser.add_argument("--input", required=True, help="输入音频文件路径 (wav/mp3)")
    parser.add_argument("--output", required=True, help="输出文本文件路径")
    parser.add_argument("--language", default="auto", help="auto/zh/en")
    parser.add_argument("--model", default="mimo-v2.5-asr")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise RuntimeError(f"audio file not found: {args.input}")

    text = transcribe(args.input, args.language)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"MiMo STT error: {e}", file=sys.stderr)
        sys.exit(1)
