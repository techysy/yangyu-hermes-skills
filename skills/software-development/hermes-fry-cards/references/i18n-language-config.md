# i18n 与系统语言配置

> fry-cards 卡片语言 vs Hermes 系统语言的联动可行性（2026-08-24）

## 两层语言配置

| 层级 | 配置位置 | 控制内容 |
|------|----------|----------|
| **系统层** | `~/.hermes/config.yaml` → `language` | TTS、CLI 提示、补丁安装拦截 |
| **补丁层** | `hermes-core-zh-localization` skill → `patch.py` | 源码硬编码状态消息（静态替换） |
| **插件层** | fry-cards 文案（当前硬编码中文） | 卡片状态提示、错误回退文本 |

## 补丁安装时的语言校验

`patch.py install` 会读 `config.yaml` 的 `language`：

- `zh` / `zh-cn` / `zh-tw` / `auto` → 允许安装
- `en` / 其他非中文 → 拒绝并提示先改 `zh`

源码位置：`skills/hermes-core-zh-localization/scripts/patch.py` → `_check_language_config()`

## fry-cards i18n 可行方案

```
config.yaml (language: zh)
    ↓
fry-cards config.py → language 属性（默认跟系统，可独立覆盖）
    ↓
文案字典 _I18N = {"zh": {...}, "en": {...}}
    ↓
所有用户可见字符串 → t("key")
```

改动量：~30-50 条文案，`config.py` 加 1 属性 + 1 翻译函数，不改逻辑。

**当前状态**：文案全部硬编码中文，`language: en` 不影响卡片层（但系统层会冲突）。
