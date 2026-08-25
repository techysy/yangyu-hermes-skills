# 模型别名子串重叠陷阱（2026-08-24）

## 问题

当多个别名 key 存在子串包含关系时，JSON 顺序决定匹配结果——先写的先命中。

## 实际案例

用户配置了三个 DeepSeek 别名：
- `deepseek-v4-flash` → 梁文谷
- `deepseek-v4-pro` → 梁文锋  
- `deepseek-v4-flash-vision-exp` → 大眼鲸

`deepseek-v4-flash-vision-exp` 包含 `deepseek-v4-flash` 子串，如果 flash 排在 vision 前面，vision 模型会被误判为"梁文谷"。

## 解决方案

**更长的 key 必须排在 JSON 前面**：

```json
{
  "deepseek-v4-flash-vision-exp": "大眼鲸",
  "deepseek-v4-flash": "梁文谷",
  "deepseek-v4-pro": "梁文锋",
  "longcat": "送外卖的",
  "gemini": "哈基米",
  "x-preview-f-free": "🐂来"
}
```

## 通用规则

当 key A 是 key B 的子串时：
- 如果希望 B 单独匹配 → B 排在 A 前面
- 匹配逻辑：`for key, alias in aliases.items(): if key in lowered: return alias`（首个命中即返回）

## 验证方法

```bash
HERMES_PYTHON=~/.hermes/hermes-agent/venv/bin/python3
$HERMES_PYTHON -c "
from hermes_fry_cards.cardkit.builder import _display_model
print(_display_model('bai/deepseek-v4-flash-vision-exp'))  # 应显示大眼鲸
print(_display_model('cbcn/deepseek-v4-flash'))            # 应显示梁文谷
print(_display_model('osf/deepseek-ai/DeepSeek-V4-Pro'))   # 应显示梁文锋
"
```
