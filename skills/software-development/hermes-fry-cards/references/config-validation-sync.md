# 配置校验白名单与渲染能力不同步 → 静默回落默认值

## 现象

用户配置 `context_display_mode: block`，但 header 里只显示 `55.6k/1.0m (5%)` 文本（默认 text），**没有进度条图形**——看起来像「面板消失了」。

日志/代码层面：`builder.py` 渲染 `block`/`block_text` 都支持，但 `Config.context_display_mode` 的校验白名单只有 `("text","bar","text_bar")`，`block` 被拒绝 → **静默回落默认 `text`**。

## 根因（一类 bug）

给渲染层（builder.py）加新模式/选项时，**忘了同步 config.py 的校验白名单**。渲染层支持但校验层不认识 → 用户配置被丢弃、静默回落到默认值，界面表现「功能没生效」。

这不是一次性 bug，是**每次加新枚举值都可能踩的坑**。

## 诊断方法

- 用户说「面板/功能没了」但日志正常、无报错 → 先怀疑配置被白名单拒绝回落默认
- 直接验证：`Config().context_display_mode` 是否返回你配置的值，还是回落默认
  ```python
  from hermes_fry_cards.config import Config
  print(Config().context_display_mode)  # 配置 block 却返回 text → 白名单漏了
  ```

## 修复模式

把白名单收敛成常量，渲染层支持什么校验层就放行什么：

```python
_VALID_MODES = ("text", "bar", "text_bar", "block", "block_text")
if mode in _VALID_MODES:
    return mode
```

**教训**：新增任何 `enum`/模式/选项时，同步检查三处——渲染层(builder.py)、校验层(config.py 白名单)、文档(README 配置表)。改完用 `Config().<field>` 实测确认返回期望值。
