# navi-bookmarks-chrome 审计记录 v3（完整修复后）

> 审计时间：本次会话完整修复阶段
> 项目地址：https://github.com/techysy/navi-bookmarks-chrome
> 项目类型：Chrome MV3 新标签页扩展（vanilla JS + i18n）

## 本次会话新增的修复

在 v2 基础上，本会话继续完成了以下内容：

### 1. 上架文档

- 新增 `PRIVACY_POLICY.md`：双语隐私政策，详细说明数据本地存储、权限用途、第三方服务
- 新增 `STORE_LISTING.md`：Chrome Web Store 上架文案，包含英文/中文名称、短描述、详细描述、权限说明
- 新增 `assets/screenshots/README.md`：商店截图尺寸说明

### 2. Manifest 优化

- `action` 增加 `default_title: "__MSG_appName__"` — 鼠标悬停工具栏图标时显示本地化名称

### 3. 发布流程

- 新增 `.github/workflows/release.yml`：推送 `v*` 标签时自动构建并发布 GitHub Release
- 新增的 CHANGELOG 标准格式与 release 工作流配合，自动提取版本说明

### 4. 变更日志标准化

- `CHANGELOG.md` 重写为 Keep a Changelog 格式
- 新增 `[Unreleased]` 占位区
- 添加图例说明
- 保留历史版本 v0.9.9 ~ v1.3.1

### 5. 仓库结构整理

- 删除 `old/` 目录（旧版 Web 项目 server.js、start.ps1、index.html 等）
- 更新 README 项目结构，移除 `old/` 引用

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

1. **README 截图**：将实际截图放入 `assets/screenshots/`，取消 README 中的注释
2. **LICENSE 文件**：根目录仍缺少 `LICENSE` 文件
3. **商店上架**：如计划发布到 Chrome Web Store，需准备
   - 1280x800 或 1440x900 截图
   - 隐私政策公开 URL
   - 开发者联系邮箱
4. **彻底去重**：删除 `newtab.js` / `popup.js` 中已迁移到 `common.js` 的重复函数定义
5. **联系邮箱**：修改 `STORE_LISTING.md` 中的 `your-email@example.com`
