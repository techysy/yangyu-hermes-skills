---
name: hermes-plugin-i18n
description: "为 Hermes 插件添加 i18n 汉化支持——前端 zh.ts + 后端 plugin_api.py 双层翻译。"
version: 1.0.0
author: techysy
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, i18n, localization, chinese, zh-cn, plugin, dashboard]
---

# Hermes 插件 i18n 汉化

为 Hermes dashboard 插件添加中文（或其他语言）支持。采用前端 zh.ts + 后端 plugin_api.py 双层翻译模式。

## 架构概览

Hermes 插件的 i18n 分两层：

1. **前端 UI 壳翻译**（`web/src/i18n/zh.ts`）— 按钮、标签、状态文本等
2. **后端内容翻译**（`plugins/<name>/dashboard/plugin_api.py`）— 插件特有的内容数据

## 前端翻译（zh.ts）

Dashboard 使用 `useI18n()` hook 提供翻译。插件通过 `tx(t, "key", "fallback")` 访问。

### 添加翻译 key

在 `web/src/i18n/zh.ts` 的对应插件 section 下添加翻译：

```typescript
// web/src/i18n/zh.ts
export const zh: Translations = {
  // ...
  myPlugin: {
    hero: {
      title: "中文标题",
      subtitle: "中文副标题",
    },
    actions: {
      submit: "提交",
    },
  },
};
```

### 前端使用翻译

插件的 `index.js` 中：

```javascript
const { t } = useI18n();  // 或 SDK.useI18n()

// 使用 tx() helper
tx(t, "myPlugin.hero.title", "Fallback English")

// 或直接访问
t.myPlugin?.hero?.title
```

## 后端内容翻译（plugin_api.py）

当插件有动态内容（如成就名称、描述）需要翻译时，在后端添加翻译字典。

### 添加翻译字典

在 `plugin_api.py` 中添加：

```python
# ── i18n: zh-CN translations ──────────────────
_ZH_NAMES: Dict[str, str] = {
    "item_id_1": "中文名称1",
    "item_id_2": "中文名称2",
}

_ZH_DESCRIPTIONS: Dict[str, str] = {
    "item_id_1": "中文描述1",
    "item_id_2": "中文描述2",
}

_ZH_CATEGORIES: Dict[str, str] = {
    "Category Name": "分类名称",
}
```

### 添加 locale 检测

```python
def _detect_locale(accept_language: Optional[str] = None) -> str:
    """从 Accept-Language 或 query 参数检测语言。"""
    if accept_language:
        al = accept_language.lower()
        if al.startswith("zh"):
            return "zh"
    return "en"
```

### 添加翻译函数

```python
def _translate_item(item: Dict[str, Any], locale: str) -> Dict[str, Any]:
    """应用 locale 翻译到单个内容项。"""
    if locale != "zh":
        return item
    result = dict(item)
    iid = result.get("id", "")
    if iid in _ZH_NAMES:
        result["name"] = _ZH_NAMES[iid]
    if iid in _ZH_DESCRIPTIONS:
        result["description"] = _ZH_DESCRIPTIONS[iid]
    cat = result.get("category", "")
    if cat in _ZH_CATEGORIES:
        result["category"] = _ZH_CATEGORIES[cat]
    return result
```

### 修改 API 端点

```python
@router.get("/items")
async def items(request: "Request" = None):
    data = get_data()
    # 检测 locale
    locale = "en"
    if request is not None:
        locale_param = request.query_params.get("locale")
        if locale_param:
            locale = _detect_locale(locale_param)
        else:
            accept_lang = request.headers.get("accept-language")
            locale = _detect_locale(accept_lang)
    # 应用翻译
    if locale == "zh" and "items" in data:
        data["items"] = [_translate_item(i, locale) for i in data["items"]]
    return data
```

### 前端传递 locale

在插件的 `index.js` 中修改 `api()` 函数：

```javascript
function api(path, options, locale) {
  let url = "/api/plugins/my-plugin" + path;
  if (locale) {
    url += (url.includes("?") ? "&" : "?") + "locale=" + encodeURIComponent(locale);
  }
  return SDK.fetchJSON(url, options);
}

// 在组件中
function MyPage() {
  const { t, locale } = useI18n();
  // ...
  api("/items", undefined, locale)
}
```

## ⚠️ 注意事项

- **hermes update 后需重新应用**：后端 plugin_api.py 的改动会被覆盖
- **前端改动也会被覆盖**：zh.ts 和 index.js 的改动需要在 update 后重新应用
- **考虑创建 patch 脚本**：类似 hermes-core-zh-localization 的 patch.py，方便 update 后重新应用
- **Tier 名称通常保留英文**：Copper/Silver/Gold/Diamond/Olympian 是品牌名
- **中文引号问题**：Python 字符串中避免使用 `"..."`（中文引号），用 `「...」` 替代

## 与 hermes-core-zh-localization 的区别

| 特性 | hermes-core-zh-localization | hermes-plugin-i18n |
|---|---|---|
| 目标 | 网关/代理核心消息 | 插件内容数据 |
| 方式 | patch.py 替换硬编码字符串 | 后端 i18n 字典 + API locale 参数 |
| 前端 | 不涉及 | zh.ts 翻译 |
| update 后 | 需重新运行 patch.py | 需重新应用改动 |
| 语言检测 | 不需要 | Accept-Language / query 参数 |
