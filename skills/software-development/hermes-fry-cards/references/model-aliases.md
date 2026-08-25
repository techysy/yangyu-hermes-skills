# 模型别名功能（2026-08-24，v0.1.1+，commit f7e5775）

用户需求：模型名显示自定义别名（如 LongCat → 哈基米、Gemini → 哈基米），而非完整路径。

## 设计决策

- **独立 JSON 文件** `~/.hermes/model_aliases.json`（用户明确要求 JSON 文件配置，不塞 config.yaml）
- **子串匹配**：key 对完整模型名做大小写不敏感的子串匹配（`longcat` 命中 `or/lc/LongCat-2.0`）
- **别名优先于截断**：命中显示别名；未命中回落 `truncate_model_name` 的 `⇲last-segment` 截断
- **热更新**：每次渲染从磁盘重读（与 show_reasoning 等 display 类配置同一机制），改文件即生效无需重启网关

## 实现

- `config.py` → `Config.model_aliases()`：JSON 惰性读取；文件缺失/坏 JSON/非 dict 一律安全回落空 map（不抛异常，卡片渲染永不因配置文件挂掉）
- `cardkit/builder.py` → `_display_model(name)`：统一模型显示名决策函数。原两处调用点（footer fields + 统一面板 header）各自 inline 判断截断，已收敛到这一处——新增显示逻辑只改这一个函数
- 测试：`tests/test_model_aliases.py`（11 个）

## 踩坑：_display_model 测试中 hermes_home 不跟随 tmp_path

`_display_model` 内部用无参 `Config()`，走 `hermes_home()`（HERMES_HOME env 或 ~/.hermes）。测试里给 `Config(home=tmp_path)` 传 home 无效——必须 monkeypatch：

```python
monkeypatch.setenv("HERMES_HOME", str(tmp_path))
monkeypatch.setattr("hermes_fry_cards.config.hermes_home", lambda: tmp_path)
```

或像现有测试一样：直接测 Config 层（可传 home），builder 层只测纯函数 `_truncate_model`。

## 用户偏好

- 示例值用真实长模型名 `nvidia/moonshotai/kimi-k3`（比旧的 `or/lc/LongCat-2.0` 更直观展示截断效果）
