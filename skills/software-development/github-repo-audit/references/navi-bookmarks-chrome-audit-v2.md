# navi-bookmarks-chrome 审计记录 v2（修复后）

> 审计时间：本次会话后续修复阶段
> 项目地址：https://github.com/techysy/navi-bookmarks-chrome
> 项目类型：Chrome MV3 新标签页扩展（vanilla JS + i18n）

## 已完成的修复

本次会话在 v1 审计基础上做了完整修复与补强：

### 1. 版本号与发布产物
- `manifest.json` version 从 `1.3.0` 修正为 `1.3.1`
- 新增 `scripts/build.js` + `package.json`：用 `adm-zip` 自动打包，确保路径为正斜杠
- 新增 `dist/navi-bookmarks-chrome-v1.3.1.zip`
- 旧的 zip/crx 移到 `releases/`，不再提交进 git（已更新 `.gitignore`）

### 2. i18n 语言包
- 补齐 8 个语言包缺失的 `hintDragToCategory`、`alertBookmarkMoved`
- 新增 `alertInvalidUrl` 并同步翻译到 10 个语言包
- 新增 `scripts/validate-i18n.js`，`npm run lint:i18n` 可一键校验

### 3. `host_permissions` 与搜索引擎一致性
- `manifest.json` 补齐搜索建议实际请求的域名：
  - `suggestqueries.google.com`
  - `suggestion.baidu.com`
  - `api.bing.com`
  - `duckduckgo.com`
  - `www.xiaohongshu.com`
- `newtab.html` 设置面板 `#defaultEngineSelect` 增加 `xiaohongshu` 选项

### 4. 安全加固
- 新增 `escapeHtml()`，所有自定义弹窗、书签渲染、搜索建议做 HTML 转义
- 新增 `normalizeUrl()` / `isAllowedUrl()`：默认 `https://`，拦截 `javascript:`/`data:`/`file:`/`about:`/`vbscript:`
- `newtab.js` 与 `popup.js` 保存/打开书签前均校验 URL
- favicon 抓取增加 5 秒超时，避免网络卡死

### 5. 代码重构
- 新增 `navi-bookmarks-chrome/common.js`，抽离共享工具：
  - `escapeHtml`, `isAllowedUrl`, `normalizeUrl`, `getRootDomain`
  - `imageToDataUrl`, `loadFaviconAsImage`, `fetchFavicon`
  - `DEFAULT_CATEGORIES`, `createI18nHelper`
- `newtab.html` 与 `popup.html` 已引入 `common.js`
- 后续可继续删除 `newtab.js`/`popup.js` 中的重复函数定义，实现彻底去重

### 6. 文档与仓库卫生
- 重写 `README.md`：新增系统要求、截图占位、安装方式、隐私说明、支持语言、开发 workflow
- 新增 `CONTRIBUTING.md`
- 新增 `.github/workflows/ci.yml`：自动跑 i18n 校验与构建
- 新增 `.github/ISSUE_TEMPLATE/bug_report.md`、`feature_request.md`
- 新增 `.github/PULL_REQUEST_TEMPLATE.md`
- 根目录大图片 `Zoigê - 3k.JPG` 移到 `assets/`

## 验收命令

```bash
npm install
npm run lint:i18n
npm run build
```

当前输出：
- ✅ All locales are consistent with "en".
- ✅ Packaged: dist/navi-bookmarks-chrome-v1.3.1.zip

## 仍建议后续处理

1. **彻底去重**：删除 `newtab.js` / `popup.js` 中已迁移到 `common.js` 的重复函数
2. **README 截图**：把实际截图放入 `assets/screenshots/`，取消 README 中的注释
3. **LICENSE 文件**：README 写了 MIT，但仓库根目录仍缺 `LICENSE` 文件
4. **商店上架材料**：如计划发布到 Chrome Web Store，需准备
   - `PRIVACY_POLICY.md`
   - 1280x800 或 1440x900 商店截图
   - 440x280 小图 / 920x680 大图（可选）
   - 对 `tabs` 权限的用途说明（权限是合理的，但审核会要求解释）
5. **搜索建议的 CORS 现实**：即使补齐了 `host_permissions`，MV3 扩展页面直接 `fetch()` 搜索建议仍可能受 CORS 限制；如实际不稳定，可考虑移除或改为 service worker 代理
