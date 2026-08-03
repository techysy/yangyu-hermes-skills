#!/usr/bin/env python3
"""Quick DeepSeek balance check — standalone, no special imports.
   Write this to /tmp, then `python3 /tmp/deepseek_balance.py`."""

import os, json, urllib.request

# Read key from .env (no source/subprocess needed)
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("DEEPSEEK_API_KEY=***            key = line.split("=", 1)[1].strip().strip("'\"").strip('"')
            break

req = urllib.request.Request(
    "https://api.deepseek.com/user/balance",
    headers={"Authorization": f"Bearer {key}"}
)
data = json.loads(urllib.request.urlopen(req).read())
b = data['balance_infos'][0]
print(f"余额：{b['total_balance']} 元（充值 {b['topped_up_balance']} 元，赠送 {b['granted_balance']} 元）")
