# 卡片元素溢出（300305）— 不支持分段思考的模型

## 现象

工具执行 20+ 步后卡片溢出，日志反复报：
```
CardKit batch update failed: cardkit_batch_update: code=300305, msg=ErrMsg: element exceeds the limit;
card=... seq=1355 split=0 elements=98 new=[reasoning_49_panel] add=[reasoning_49_panel]
```

## 根因

「不支持分段思考」的模型（如 deepseek-v4-flash）在 thinking 和 tool 之间频繁切换。`on_reasoning_delta` 只在末尾是 reasoning 时追加，跨类型（reasoning→tool→reasoning）会**新建独立 reasoning panel**。实测一个卡片产生 49 个 reasoning panel，每个估算 4 元素 → 49×4=196，加其他元素超过飞书硬上限 200。

## 为什么拆卡没提前触发

`session.element_count` 严重低估实际元素数（日志 `elements=98` 而实际已 200+）。部分 add 失败导致 element_count 没同步，且 `estimate_tool_elements`/`estimate_segment_elements` 对每步/每面板的估算偏低。所以 `_maybe_rollover_tool_segment` 和拆卡阈值判断（180）永远不触发，直到飞书端拒绝。

## 诊断方法

看溢出日志的 `new=[reasoning_N_panel]` — N 越大说明 reasoning 面板被拆得越多（N=49 就是 49 个独立面板）。溢出的是 reasoning 面板，不是 tool。

## 修复

新增配置 `display.platforms.feishu.max_reasoning_panels`（默认 3）。在 `SegmentState.on_reasoning_delta` 里，当已有 reasoning 面板数达到上限时，不再新建面板，而是把新文本**合并进最后一个 reasoning 面板**：

```python
reasoning_count = sum(1 for s in self.segments if s.type == SegmentType.REASONING)
if reasoning_count >= self.max_reasoning_panels:
    for seg in reversed(self.segments):
        if seg.type == SegmentType.REASONING:
            seg.text += text
            seg.dirty = True
            return
self._new_reasoning(text)
```

元素从 49×4=196 封顶到 3×4=12。

## 注意

`SegmentState()` 有三处实例化（controller.py `_do_create_card`、`_do_clarify_split`、session.py），都要传入 `max_reasoning_panels=self._cfg.max_reasoning_panels`。

## 教训

cardkit 元素计数跟「分段思考模型能否产生 segment 边界」强相关。不支持的模型会因频繁 thinking/tool 交替产生海量 reasoning 面板 → 溢出的不是 tool 而是 reasoning。排查溢出先看 `new=[...]` 是哪种 segment。
