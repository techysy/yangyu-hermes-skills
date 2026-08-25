# Feishu Card API Notes

## 发送独立卡片

```python
from hermes_fry_cards.config import Config
from hermes_fry_cards.feishu import FeishuClient, FeishuClientConfig
from hermes_fry_cards.cardkit.builder import build_cron_card

cfg = Config()
client = FeishuClient(FeishuClientConfig(
    app_id=cfg.feishu_app_id, app_secret=cfg.feishu_app_secret, base_url=cfg.feishu_base_url
))
card = build_cron_card(content, task_name="标题")
await client.send_card_to_chat("oc_xxxx", card)
```

chat_id 从 `~/.hermes/sessions/sessions.json` 查 `feishu:dm:oc_xxx`。

## CardKit Merge 语义

- `cardkit_update`（aupdate）：全量替换 body，但元素级 ID 去重是 merge-style
- `cardkit_batch_update`（abatch_update）：局部增量更新，同 ID 更新，不同 ID 追加
- 已删除 ID 残留（不会自动清理）

## 元素 ID 黄金法则

1. 流式阶段和完成态**必须复用同一组 element_id**
2. 绝不用固定默认 ID（如 `reasoning_text`），否则 Duplicate ID
3. fallback 用带索引唯一 ID：`reasoning_text_{i}`
