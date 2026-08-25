# 用一次性脚本向飞书发送自定义卡片

当需要把一段内容（天气、攻略、报告等）作为飞书卡片主动推送到用户聊天，而不是走流式回复时，用这个方法。

## 关键 API

- `hermes_fry_cards.cardkit.builder.build_cron_card(content, task_name=...)` — 构建 schema 2.0 静态卡片（header + markdown 正文，自动分块）
- `hermes_fry_cards.feishu.FeishuClient` + `FeishuClientConfig(app_id, app_secret, base_url)` — 飞书客户端
- `await client.send_card_to_chat(chat_id, card)` — 发送到聊天（`receive_id_type="chat_id"`），返回 message_id

凭证从 `Config()` 的 `feishu_app_id` / `feishu_app_secret` / `feishu_base_url` 读取（内部走 `.env` 的 `FEISHU_APP_ID/SECRET/BASE_URL`）。

## 找用户飞书 DM chat_id

读 `~/.hermes/sessions/sessions.json`，键形如：
```
agent:main:feishu:dm:oc_37febfd71b7fa298f9b60a5b72beb470
```
`oc_...` 那段就是 DM 的 chat_id。多实例时取最近有消息的那个。

## 脚本骨架

```python
import asyncio, os
from pathlib import Path

# 先把 ~/.hermes/.env 加载进环境（脚本不继承 gateway 的环境）
env_path = Path.home() / ".hermes" / ".env"
for line in env_path.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from hermes_fry_cards.cardkit.builder import build_cron_card
from hermes_fry_cards.config import Config
from hermes_fry_cards.feishu import FeishuClient, FeishuClientConfig

CHAT_ID = "oc_..."  # 从 sessions.json 拿

CONTENT = "**标题**\n\n正文 markdown"

async def main():
    cfg = Config()
    client = FeishuClient(FeishuClientConfig(
        app_id=cfg.feishu_app_id, app_secret=cfg.feishu_app_secret,
        base_url=cfg.feishu_base_url,
    ))
    card = build_cron_card(CONTENT, task_name="🍟 标题")
    msg_id = await client.send_card_to_chat(CHAT_ID, card)
    print(f"OK message_id={msg_id}")

asyncio.run(main())
```

运行（必须用 Hermes venv，因为依赖 lark_oapi）：
```bash
HERMES_PYTHON=~/.hermes/hermes-agent/venv/bin/python3
$HERMES_PYTHON /tmp/send_card.py
```

## 注意事项

- 别把 `app_secret` 明文打进输出/日志（凭据走 Config 自动从 `.env` 读，不要 print）。
- `build_cron_card` 的正文 markdown 支持表格/加粗，适合结构化内容。
- 这是主动推送卡片，不是流式回复；若用户想要的是流式卡片，走正常对话让插件 hook 渲染。
