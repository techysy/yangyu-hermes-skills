# navi-bookmarks-chrome 审计记录

> 审计时间：本次会话
> 项目地址：https://github.com/techysy/navi-bookmarks-chrome
> 项目类型：Chrome MV3 新标签页扩展（vanilla JS + i18n）

## 仓库结构速览

```
.
├── README.md
├── CHANGELOG.md
├── .gitignore
├── Zoigê - 3k.JPG          # 根目录大图片
├── navi-bookmarks-chrome/  # 扩展源码目录
│   ├── manifest.json
│   ├── newtab.html
│   ├── newtab.js
│   ├── newtab.css
│   ├── popup.html
│   ├── popup.js
│   ├── _locales/           # 10 种语言包
│   └── ...
├── navi-bookmarks-chrome.crx
├── navi-bookmarks-chrome.zip
├── navi-bookmarks-v1.3.1.zip
└── old/                    # 旧版 Web 项目
```

## 发现的问题（按优先级）

### 🔴 严重：manifest.json 版本号未同步

- `README.md` / `CHANGELOG.md` 均声称最新版为 **v1.3.1**
- 但 `navi-bookmarks-chrome/manifest.json` 中仍是 `"version": "1.3.0"`
- 这会导致 Chrome 不识别为新版本，扩展商店/手动加载都看不到更新。

**修复**：把 `manifest.json` 的 `version` 改为 `1.3.1`，并重打包所有发布产物。

### 🔴 严重：发布产物与源码不一致

- 根目录的 `navi-bookmarks-chrome.zip` 和 `navi-bookmarks-v1.3.1.zip` 里的 `manifest.json` 仍然是 `1.3.0`
- 解压后的 `newtab.js` 与源码 `newtab.js` 行数/内容不一致（缺少小红书搜索引擎等 1.3.1 功能）
- **用户从 GitHub 下载 zip 安装，得到的其实是旧版本**

**修复**：删除旧 zip/crx，用当前源码重新打包；后续把发布产物放到 GitHub Releases，不要提交到 git 历史。

### 🔴 严重：`navi-bookmarks-v1.3.1.zip` 使用反斜杠路径

- `unzip -l` 可见条目为 `navi-bookmarks-chrome\manifest.json` 等反斜杠分隔
- Chrome 加载 unpacked 扩展只认正斜杠，会导致**直接加载失败**

**修复**：用 Linux/macOS 或 `zip -r` 在类 Unix 环境下打包；Windows 下可用 PowerShell `Compress-Archive` 后再用 7z 修正路径。

### 🟡 中等：i18n 语言包缺 key

- 除 `en` / `zh_CN` 外，其余 8 个语言包（`zh_TW`, `ja`, `ko`, `de`, `fr`, `vi`, `th`, `ms`）均缺少：
  - `hintDragToCategory`
  - `alertBookmarkMoved`
- 缺 key 时不会报错，只显示空白文案。

**修复**：给 8 个语言包补齐对应翻译。

### 🟡 中等：`host_permissions` 未覆盖搜索建议域名

`manifest.json` 声明的 host_permissions：

```json
[
  "https://icon.horse/*",
  "https://favicon.im/*",
  "https://www.google.com/*",
  "https://www.google.com.hk/*"
]
```

但 `newtab.js` 里 `fetchSearchSuggestions()` 实际请求：

- `suggestqueries.google.com`
- `suggestion.baidu.com`
- `api.bing.com`
- `duckduckgo.com`
- `xiaohongshu.com`（搜索跳转）

这些域名都没有在 `host_permissions` 中声明，MV3 环境下可能无法获取搜索建议。

**修复**：要么补齐 `host_permissions`，要么改用后台 service worker 处理跨域请求，或移除搜索建议功能。

### 🟡 中等：默认搜索引擎选项不一致

- 顶部搜索下拉 `searchEngineDropdown` 有 `xiaohongshu`
- 设置面板 `#defaultEngineSelect` 只有 google/baidu/bing/duckduckgo，没有小红书
- 用户无法在设置里把小红书设为默认搜索引擎

**修复**：两处选项保持一致。

### 🟡 中等：HTML `lang` 和 fallback 文案硬编码中文

- `<html lang="zh-CN">` 固定为中文
- 大量 `data-i18n` 的 fallback 文本是中文
- 切换语言后，浏览器仍认为页面是中文；翻译失败时会显示中文 fallback

**修复**：`applyI18n()` 中根据 `activeLocale` 动态设置 `document.documentElement.lang`；fallback 用英文或留空。

### 🟡 中等：自定义弹窗存在 XSS 注入面

多处把用户数据/书签数据直接拼接到 `innerHTML`：

```js
bubble.innerHTML = '<div class="bubble-message">' + message + '</div>'
```

导入成功提示、书签名称、分类名等都可能进入 `message`。虽然扩展环境相对封闭，但仍建议转义。

**修复**：统一用 `textContent` 替换，或加 HTML 转义函数。

### 🟡 中等：URL 协议处理不够安全

```js
if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'http://' + url;
}
```

- 默认使用不安全的 `http://`
- 未拦截 `javascript:`、`data:` 等伪协议

**修复**：默认 `https://`，正则白名单 `/^https?:\/\//i`，拒绝其它 scheme。

### 🟢 小问题：README 缺少关键信息

- 没有系统要求（Chrome 88+ / MV3）
- 没有 .crx 安装说明
- 没有隐私/数据存储说明
- 没有功能截图
- 没有贡献指南 / Issue 模板
- 仓库根目录同时放 zip / crx / 大图，结构较乱

**修复**：
- README 加 "Requirements"、"Privacy"、"Screenshots"、"Contributing" 等节
- 把发布产物移到 `releases/` 或 GitHub Releases
- 根目录加 `LICENSE` 文件（README 写了 MIT 但仓库没有）

### 🟢 小问题：popup.js 与 newtab.js 重复代码

两者都有 favicon 抓取、i18n 加载、分类 label 映射等逻辑。

**修复**：抽取 `common.js` / `utils.js` 共享代码，减少维护成本。

### 🟢 小问题：favicon 抓取鲁棒性

依赖 `icon.horse`、`favicon.im`、`google.com/s2/favicons`，这些服务在不同网络下不稳定；抓取的 base64 没有大小限制。

**修复**：增加超时、失败降级到 emoji、限制图标尺寸、README 注明依赖外部网络。

## 建议修复优先级

1. 同步 `manifest.json` 版本号为 `1.3.1`
2. 重新打包 zip/crx，确保与源码一致，路径用正斜杠
3. 补齐 8 个语言包的 `hintDragToCategory` 和 `alertBookmarkMoved`
4. 修正 `host_permissions` 或搜索建议实现
5. 统一默认搜索引擎选项（加小红书）
6. 修复 URL 协议默认与伪协议校验
7. 清理自定义弹窗 XSS 风险点
8. README 补系统要求 / 隐私说明 / 截图 / 贡献指南
9. 根目录加 LICENSE 文件
10. 整理仓库结构，发布产物走 GitHub Releases
