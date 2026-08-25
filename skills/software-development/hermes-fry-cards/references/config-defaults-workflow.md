# 把当前配置设为默认值

## 背景

用户要求"把我现在的值设置为默认值"，让新装用户开箱即用就是当前这套配置。

## 正确流程

### 1. 对照当前值与代码默认值

```bash
# 读取当前 config.yaml 的实际值
cat ~/.hermes/config.yaml

# 读取 config.py 中各属性的默认值
grep -n "return.*get.*False\|return.*get.*True" hermes_fry_cards/config.py
```

### 2. 找出不一致的属性

| 配置项 | 当前值 | 代码默认值 | 需要改 |
|--------|--------|-----------|--------|
| `streaming.enabled` | true | false | ✅ |
| `streaming.header.enabled` | true | false | ✅ |
| `streaming.footer.enabled` | false | true | ✅ |
| `footer.fields` | status,elapsed,model,context | status,elapsed,context,model | ✅ |
| `truncate_model_name` | true | false | ✅ |
| `show_reasoning` | true | false | ✅ |

### 3. 用 targeted patch 修改 config.py

```python
# streaming.enabled: False → True
return bool(sec.get("enabled", True))  # was False

# header.enabled: False → True
return bool(header.get("enabled", True))  # was False

# footer.enabled: True → False
return bool(footer.get("enabled", False))  # was True

# truncate_model_name: False → True
return bool(feishu.get("truncate_model_name", True))  # was False

# footer.fields 顺序
return [["status", "elapsed", "model", "context"]]  # was [["status", "elapsed", "context", "model"]]
```

### 4. 同步更新 tests/test_config.py

**必须做**，否则会新增 13+ 测试失败。

找到对应的测试方法，修改断言：

```python
# test_enabled_defaults_false_when_missing → test_enabled_defaults_true_when_missing
def test_enabled_defaults_true_when_missing(self, raw):
    cfg = _make_config(raw)
    assert cfg.enabled is True  # was False

# test_header_enabled_defaults_false_when_missing → test_header_enabled_defaults_true_when_missing
def test_header_enabled_defaults_true_when_missing(self, raw):
    cfg = _make_config(raw)
    assert cfg.header_enabled is True  # was False

# test_footer_enabled_defaults_true_when_missing → test_footer_enabled_defaults_false_when_missing
def test_footer_enabled_defaults_false_when_missing(self, raw):
    cfg = _make_config(raw)
    assert cfg.footer_enabled is False  # was True

# test_default_false → test_default_true (show_reasoning)
def test_default_true(self, raw):
    cfg = self._make_reasoning_config({})
    assert cfg.show_reasoning is True  # was False

# footer_fields 默认顺序
assert cfg.footer_fields == [["status", "elapsed", "model", "context"]]
```

### 5. 更新 README

- 配置项一览表默认值列
- 配置示例代码块
- 版本徽章（如 rc6 → rc7）

### 6. 更新 CHANGELOG

```markdown
## [0.1.0-rc7] - 2026-08-22

### 变更
- **默认值对齐当前推荐配置** — 新装用户开箱即用即为此套样式
  - `streaming.enabled` 默认 `true`
  - `streaming.header.enabled` 默认 `true`
  - `streaming.footer.enabled` 默认 `false`
  - `footer.fields` 默认顺序 `status → elapsed → model → context`
  - `truncate_model_name` 默认 `true`
- README 配置示例 / 默认值表同步更新
```

### 7. 提交、推送、创建 release

```bash
git add -A
git commit -m "Release v0.1.0-rc7: 默认值对齐当前推荐配置"
git tag v0.1.0-rc7
git push origin main v0.1.0-rc7
gh release create v0.1.0-rc7 --prerelease
gh release upload v0.1.0-rc7 INSTALL.md hermes-fry-cards-skill.md
```

## 验证

```bash
# 验证默认值正确
python3 -c "
from hermes_fry_cards.config import Config
cfg = Config()
print('enabled:', cfg.enabled)
print('header_enabled:', cfg.header_enabled)
print('footer_enabled:', cfg.footer_enabled)
print('truncate_model_name:', cfg.truncate_model_name)
print('footer_fields:', cfg.footer_fields)
"
```

## 关键注意

1. **最小改动原则**：永远不要重写文件，只做 targeted patch
2. **测试同步**：改默认值必须同步修改 `tests/test_config.py` 中对应断言
3. **不影响已有用户**：已有 config.yaml 显式配置的用户不受影响
4. **热更新 vs 重启**：改默认值只影响"未显式配置的新用户"，已有用户继续用显式配置
