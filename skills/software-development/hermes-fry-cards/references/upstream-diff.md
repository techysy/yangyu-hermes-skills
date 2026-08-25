# 上游差异：Cheerwhy/hermes-lark-streaming v0.12.0 vs fry-cards 0.1.1

2026-08-24 实测对比结论。上游独立演进（v0.12.0，2026-07-31），fry-cards 基于其早期快照独立开发。

## 对比方法

```bash
git clone --depth 1 https://github.com/Cheerwhy/hermes-lark-streaming.git /tmp/upstream-lark
diff -rq /tmp/upstream-lark/hermes_lark_streaming hermes_fry_cards
# 配置项差集：直接比 config.py 的 property 名
grep -o "def [a-z_]*" /tmp/upstream-lark/hermes_lark_streaming/config.py
```

注意包名不同（`hermes_lark_streaming` vs `hermes_fry_cards`），但模块结构一一对应，可逐文件 diff。

## 新功能（fry-cards 有、上游没有）

| 功能 | 配置项 | 说明 |
|---|---|---|
| 统一面板 | `unified_panel_min_duration`=5 | 推理+工具合并到底部统一面板；无工具且耗时 ≤ 阈值不显示 |
| 上下文进度条 | `show_context` + `context_display_mode` | text/bar/text_bar 渐变阴影三模式，智能单位 k/m。上游仅 footer 纯文本百分比、无独立开关 |
| 推理面板上限 | `max_reasoning_panels`=3 | 兼容不分段思考模型（deepseek-v4-flash 等），防 300305 元素溢出 |
| 模型名截断 | `truncate_model_name`=true | `or/lc/LongCat-2.0` → `⇲LongCat-2.0`，修移动端换行 |

## 行为差异

- `show_reasoning` 默认 **true**（上游默认 false）

## 关键修复（上游存在的坑）

- **300305 元素超限强制拆卡**：封印旧卡、未创建 segment 迁移新卡续流，不再永久卡「处理中」（rc5/rc6）
- **远程图片 URL 过滤**：CardKit 拒绝远程 URL 作 image key（`200570 invalid image keys`），无法上传路径的文本先 strip 引用并包代码围栏
- **完成态 Duplicate ID 体系修复**：text_el_id 全链路复用 + 带索引唯一 ID 兜底（上游 builder 用固定 `reasoning_text`，merge-style update 下会撞 Code 1001 导致卡片卡 loading）
- **seal/complete 失败删除 loading 图标**：卡片不残留处理中状态

## 工程化（0.1.1 稳定性重构）

- session 生命周期统一入口 `_register_session`/`_dispose_session`，清理幂等，interrupt 后不误删新映射，同 message_id 终态可重建
- FlushController 竞态修复：完成态快照防误重刷、立即 flush 先取消遗留 timer 防双刷
- `mark_failed(reason=)` 可追溯 + 日志事件标准化 + `_yield_to_gateway(reason=...)` 单一回落决策点
- 测试 15 个文件（上游 12），含 9 个稳定性回归测试
