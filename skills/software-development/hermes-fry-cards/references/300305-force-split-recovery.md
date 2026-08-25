# 300305 元素超限的「强制拆卡」恢复（element_count 失真根因）

## 现象

`errors.log` 报 `cardkit_batch_update: code=300305 element exceeds the limit`，且 `elements=` 读数很低仍被飞书拒绝：

```
cardkit_batch_update: code=300305 element exceeds the limit;
seq=2107 elements=17 new=[answer_14] tool_updates=[tool_panel,tool_panel] add=[answer_14]
```

消息永久卡「处理中」，`_do_flush` 每次 batch_update 都失败后直接 return。

## 与 reasoning 面板溢出的区别

- card-element-overflow.md：`new=[reasoning_N_panel]` 且 N 很大（如 49），是「不支持分段思考」的模型产生海量 reasoning 面板 → **max_reasoning_panels 合并**解决。
- 本文：`elements=` 接近/低于 180 仍报 300305，`new=[answer_N]` 正常 → **element_count 追踪失真，卡片真实元素数已顶到飞书硬上限 200** → 强制拆卡恢复。

`tool_updates=[tool_panel,tool_panel]` 是多个 dirty tool segment 更新同一共享面板，属正常，非根因。

## 根因

1. `session.element_count` 严重低估实际元素数（部分 add 失败未同步、估算偏低）。
2. **`_handle_flush_error` 只识别 `230099`+`11310` 子码，从不识别独立的 `300305` 码** → batch_update 失败→`_do_flush` return→卡片已满、后续每次 flush 都失败→永久卡死，没有任何拆卡/恢复路径。

## 修复

`feishu.py` + `streaming/controller.py`：

1. 新增常量：
```python
CARDKIT_ELEMENT_LIMIT_TOTAL = 300305  # 独立码: 卡片元素总数超限
```
2. `_handle_flush_error` 识别 300305 并告警。
3. `_do_batch_update` 的 except 分支：捕获 300305 且 `not session.split_disabled` 时调用 `_force_split_on_element_limit(session)`，然后返回 False。
4. 新增方法 `_force_split_on_element_limit(session)`：
   - 封印当前卡（`_seal_current_card`，含已创建 segment）
   - `_create_streaming_card` 建新卡；失败则 `split_disabled=True` 降级继续写当前卡
   - `session.set_card` 切到新卡，`element_count=1`、`sequence=1`、重置 tool_panel 标志
   - 未创建的 segment 标 `created=False; dirty=True` 迁移到新卡，下一轮 flush 重新 add

## 部署注意

插件是 **editable install + AST 注入 gateway/run.py**。改完源码必须 `hermes gateway restart` 才加载新代码。

## 验证

- `pytest tests/ -q` 应保持 490 通过 / 4 基线失败（4 个失败为历史遗留，git stash 验证与本改动无关）。
- 确认 `CARDKIT_ELEMENT_LIMIT_TOTAL == 300305`、`StreamingController` 有 `_force_split_on_element_limit` 方法。
