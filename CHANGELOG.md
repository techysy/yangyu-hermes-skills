# CHANGELOG / 更新日志

---

## 2026-08-04

### 新增 / Added
- **git-release-troubleshooting** — 精简为通用排障：去除平台限定（非 fnOS 专属），补充真实开源项目场景案例（spot-studio、web-jpg-tool、tianfu-greenway-ranking、navi-bookmarks-chrome、inspection-visualizer、film-price-tracker、daily-inspection-checklist）/ Streamlined to generic troubleshooting: removed platform-specific (non-fnOS) constraints, added real open-source project case studies

### 变更 / Changed
- **git-project-lifecycle** — version 升至 1.1.0；排障内容移入独立模块 git-release-troubleshooting，主流程保持纯净 / Bumped to 1.1.0; troubleshooting moved to standalone module, main flow kept clean
- **git-release-troubleshooting** — 移除 fnOS 专属的 4 位版本号内容，改为平台无关通用排障（多语言项目版本字段、预发布/正式版、Docker 镜像 tag、CI 自动构建产物）；version 升至 1.1.0 / Removed fnOS-specific 4-part versioning, generalized to platform-agnostic troubleshooting (multi-lang version fields, pre-release/stable, Docker image tag, CI auto-build); bumped to 1.1.0
- **README** — 技能数 9→10，新增 git-release-troubleshooting 安装示例与列表 / Skills count 9→10, added install example & list entry

---

## 2026-08-01 (README)

### 变更 / Changed
- **README** — 新增「Hermes 相关 fnOS 应用」章节，链接三个可部署到飞牛 NAS 的 Hermes 生态应用：hermes-webui-fnos（WebUI）、9router-fnos（AI 路由器/API 代理）、metacubexd-fnos（Mihomo 网络代理面板） / Added "Related fnOS Apps" section linking three Hermes-ecosystem apps deployable to fnOS NAS

---

## 2026-08-01

### 新增 / Added
- **lark-streaming** — 飞书流式卡片插件安装指南（hermes-lark-streaming v1.6.0）/ Feishu streaming cards plugin install guide
- **feishu-markdown** — 修复飞书 Markdown 渲染问题（表格、粗体、代码块）/ Fix Feishu markdown rendering (tables, bold, code blocks)

### 迁移 / Moved
- **fnos-app-development** — 移至独立私有仓库 [techysy/fnos-app-dev-skill](https://github.com/techysy/fnos-app-dev-skill) / Moved to private repo

### 清理 / Cleanup
- **strava-api** — 移除内部引用（credentials、router-bypass、secret-redaction、dns-fix、tokens）/ Removed internal references (credentials, router-bypass, secret-redaction, dns-fix, tokens)

## 2026-07-31

### 新增 / Added
- **fnos-app-development** — 新增 references/nextjs-standalone-bundling.md：Next.js standalone 应用打包模式（9Router 实战）/ Added Next.js standalone bundling pattern reference (9Router case)

### 变更 / Changed
- **fnos-app-development** — 修正 TRIM_APPDEST 路径认知：fnOS 1.1.31xx 直接传 /vol4/@appcenter/<App>（server 在根下），旧版传 /var/apps/<App>（server 在 target/ 下）；cmd/main 必须双路径检测，硬编码 target/server 会导致"无法启用/本地应用启动失败" / Fixed TRIM_APPDEST layout: fnOS 1.1.31xx passes /vol4/@appcenter/<App> directly (server at root), older versions /var/apps/<App> (server under target/); cmd/main must detect both layouts
- **fnos-app-development** — 新增踩坑：fpk 复制到可见目录可能变 mode 000（需 chmod 644）；后台 SSH 杀进程只杀客户端、远端 node 残留占端口（需按 PID 杀） / New pitfalls: fpk copied to visible NAS dir can land mode 000 (chmod 644 needed); killing background SSH session only kills the client, remote node survives holding the port (kill by PID)

## 2026-07-30

### 变更 / Changed
- **fnos-app-development** — 大幅更新：v0.19.0 dashboard 架构、Gateway 进程树保护陷阱、API server 绑定变更、Node.js cookbook、connection switching 等（SKILL.md 388→966行，references 2→8个） / Major update: v0.19.0 dashboard architecture, Gateway process tree protection, API server binding changes, Node.js cookbook, connection switching, etc. (SKILL.md 388→966 lines, references 2→8 files)
- **fnos-app-development** — 新增 build 要求：app/ 目录必须存在、wizard 可能导致验证失败、install_dep_apps 导致拒绝等 / Added build requirements: app/ directory must exist, wizard may cause validation failure, install_dep_apps causes rejection, etc.

## 2026-07-29

### 新增 / Added
- **feishu-table-render** — 修复飞书 Markdown 表格渲染 / Fix Feishu table rendering
- **strava-api** — Strava 骑行统计查询（脱敏后发布） / Strava ride stats (sanitized)
- **fnos-app-development** — 飞牛 NAS 应用开发指南 / fnOS app development guide
- **outdoor-trip-planner** — 户外出行规划（骑行/徒步） / Outdoor trip planner (cycling/hiking)
- skillhub.json — SkillHub 兼容清单 / SkillHub manifest
- README.md — 项目说明 / Project documentation

### 变更 / Changed
- 仓库更名为 yangyu-skills-hub / Repo renamed to yangyu-skills-hub
- README 双语化 / README bilingual (CN/EN)
- outdoor-trip-planner 标注 12306 为第三方依赖 / Marked 12306 as third-party dependency
