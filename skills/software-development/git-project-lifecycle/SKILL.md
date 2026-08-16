---
name: git-project-lifecycle
description: "Git 项目全生命周期管理（提交规范 / 版本 / 变更日志 / 发版 + 故障排查）— Conventional Commits 1.0.0、SemVer、Keep a Changelog 1.1.0、发版流程，含版本/CHANGELOG/tag/Release/提交 常见坑排查。Use when versioning a release, writing CHANGELOG.md, deciding commit conventions, bumping versions, preparing a GitHub release, or fixing a wrong/missing/inconsistent version, changelog, tag, or Release."
version: 2.0.0
platforms: [linux, macos]
---

# Git 项目全生命周期管理（提交规范 / 版本 / 变更日志 / 发版 / 排障）

管理 GitHub 项目从提交到发版的完整生命周期，统一三个参考规范，并含故障排查模块（原 git-release-troubleshooting）。

- **Conventional Commits 1.0.0** — 提交信息规范（决定版本号）
- **SemVer** — 语义化版本（决定版本号位数）
- **Keep a Changelog 1.1.0** — CHANGELOG.md 格式

> 本技能整合了正向流程（怎么做）与排障（出了问题怎么查/怎么修），平台无关、语言无关。

## 一、提交规范（Conventional Commits 1.0.0）

### 提交格式

```
<type>[可选 scope]: <描述>

[可选 正文]

[可选 脚注]
```

### 提交类型

| 类型 | 含义 | SemVer |
|---|---|---|
| `feat:` | 新功能 | MINOR |
| `fix:` | 修复 bug | PATCH |
| `BREAKING CHANGE:` 脚注 或 `<type>!:` | 破坏性变更 | MAJOR |
| `build:` | 构建系统/依赖 | — |
| `chore:` | 非业务性修改/工具配置 | — |
| `ci:` | 持续集成流程 | — |
| `docs:` | 文档 | — |
| `style:` | 代码样式（缩进/空格等） | — |
| `refactor:` | 重构（不改功能逻辑） | — |
| `perf:` | 性能优化 | — |
| `test:` | 测试用例 | — |

范围用圆括号补充上下文：`feat(parser): adds ability to parse arrays.`。破坏性变更用 `!` 标记：`feat(api)!: drop support for Node 6` 或脚注 `BREAKING CHANGE: ...`。

## 二、版本号规则（SemVer）

根据提交类型决定新版本号：

- **MAJOR**（`BREAKING CHANGE` / `!`）→ `X+1.0.0`
- **MINOR**（`feat:` 新功能）→ `X.Y+1.0`
- **PATCH**（`fix:` 修复）→ `X.Y.Z+1`
- **4 位版本**（如 fnOS 应用 `0.4.4.14`）：测试包累加第 4 位，正式版升第 3 位
- 发正式版需明确确认；测试包可随时打包

## 三、变更日志（Keep a Changelog 1.1.0）

### 文件结构

`CHANGELOG.md` 开头：

```markdown
# Changelog

本项目的所有显著变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]
```

### 版本条目

```markdown
## [1.2.3] - 2026-08-04
```

- 版本号 `[X.Y.Z]` 用方括号
- 日期 `- YYYY-MM-DD`（ISO 8601）
- `[Unreleased]` 永远在最顶部
- 按时间倒序

### 六类变动

| 类别 | 英文 | 中文 |
|---|---|---|
| Added | `### Added` | `### 新增` |
| Changed | `### Changed` | `### 变更` |
| Deprecated | `### Deprecated` | `### 弃用` |
| Removed | `### Removed` | `### 移除` |
| Fixed | `### Fixed` | `### 修复` |
| Security | `### Security` | `### 安全` |

推荐中英双语标题（`### 变更 / Changed`），空分类省略。

### 条目写法

```markdown
- **功能名称** — 一句话说明
```

每条 `- ` 开头、一句话概括要点、面向用户表达、引用文件用反引号、重要变动必须记录。

### 提交类型 → Changelog 分类

| Conventional Commit 类型 | Changelog 分类 |
|---|---|
| `feat:` | Added / 新增 |
| `fix:` | Fixed / 修复 |
| `refactor:` / `perf:` / `style:` / `chore:` | Changed / 变更 |
| `!` / `BREAKING CHANGE:` | Removed / 移除（或 Changed 若改接口） |
| `docs:` | 一般不记入（除非影响用户） |
| `build:` / `ci:` / `test:` | 一般省略 |

## 四、发版流程

### 分阶段发布策略（通用）

多数项目采用 **测试 → 正式** 的分阶段发布，通用规则（适用于任何项目/平台）：

- **测试/预发布包可随时构建**：迭代节奏快，验证改动
- **正式版需明确确认才发**：正式发布有后果，不主动发，需用户/负责人显式确认
- **版本递增规则**：测试阶段在候选版本上累加（如第 4 位 `0.4.4.x`），正式版才升正式位（第 3 位 `0.4.5`）
- **changelog 合并**：测试阶段每版记录当前改动；正式版发布说明**合并**测试阶段所有改动为一条
- **测试/正式产物命名区分**：测试包带 `-test`/`-beta`/`-rc` 后缀，正式包不带

> 具体实现（打包工具、产物目录、版本位约定）由项目/平台决定，见对应平台 skill（如 fnOS 见 fnos-app-development）。

### 发版步骤

1. 确认提交都符合 Conventional Commits（`git log` 检查）
2. 根据提交类型决定新版本号（SemVer）
3. 把 `[Unreleased]` 归档为新版本条目（`## [X.Y.Z] - 日期`），分类写入变更
4. 顶部重建 `[Unreleased]`
5. 打 git 标签：`git tag vX.Y.Z`
6. 创建 GitHub Release（从 changelog 提取发布说明）
7. 更新版本对比链接（文件底部）

### 生成 changelog 条目

```bash
# 查看两版本间提交，提炼显著变更
git log v1.2.2..v1.2.3 --oneline
```

## 五、故障排查（原 git-release-troubleshooting）

### 5.1 版本号（SemVer）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 版本号升错位 | 破坏性变更没标 `!` 或 `BREAKING CHANGE:`；把 `feat` 当 `fix` 记 | 复核提交类型，再按 MAJOR/MINOR/PATCH 规则回改版本号 |
| 该升 MAJOR 只升了 MINOR | 有 BREAKING CHANGE 但漏标 | `git log --oneline` 检查提交，找出破坏性变更，标 `!` 或补脚注后升 MAJOR |
| 预发布版 vs 正式版混淆 | 忘了区分 `-beta`/`-rc` 与正式版 | 预发布用 `v1.2.3-rc.1`；正式版去掉后缀升稳定位 |
| 版本号与项目版本字段不一致 | 只改了 changelog 忘了同步代码里的版本 | 逐个核对 `package.json` / `pyproject.toml` / `Cargo.toml` / `manifest.json` 里的版本字段 |

> 真实场景（Web 应用）：`spot-studio` 改版后忘了同步 `package.json` 的 `version` 与 CHANGELOG，npm 打包产物版本号停留在旧版。→ 发版前统一跑 `grep '"version"' package.json` + `git tag` 三方核对。

### 5.2 CHANGELOG 问题

| 问题 | 原因 | 解决 |
|---|---|---|
| `[Unreleased]` 丢失 | 归档版本条目后忘了重建 | 归档后立即在顶部补 `## [Unreleased]` |
| 版本条目日期格式错 | 日期写成本地格式 | 用 ISO 8601：`## [1.2.3] - 2026-08-04` |
| changelog 顺序乱 | 新版本插到中间 | 最上方是 `[Unreleased]`，其余按时间倒序 |
| 六分类中/英文混用 | 标题不统一 | 用「`### 变更 / Changed`」双语标题，空分类省略 |
| 改动类别放错分区 | `feat` 记进 Fixed、`refactor` 记进 Added | 对照「提交类型 → Changelog 分类」表核对 |
| 忘了更新版本对比链接 | 文件底部链接仍指向旧版 | 归档后同步更新底部链接 |
| 双语项目中文/英文条目写进同一条 | 双语夹杂、读起来乱 | 每条保留双语（`中文 / English`），或分语言段落，不混写 |

> 真实场景（静态站点/纯前端）：`tianfu-greenway-ranking`、`navi-bookmarks-chrome` 改版频繁，changelog 常出现新版本插到中间的错——归档 `[Unreleased]` 时必须按时间倒序整体重排。

### 5.3 git 标签（tag）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 标签与版本号不一致 | 打错标签格式（`1.2.3` 而非 `v1.2.3`） | 统一 `vX.Y.Z`；打错删除重打 |
| 标签打在错误提交上 | 打包前忘了 commit 最新改动 | `git tag -d vX.Y.Z`，`git tag vX.Y.Z <正确SHA>` |
| 标签已推送但想改 | 远程标签无法直接覆盖 | 本地+远程都删：`git push origin :refs/tags/vX.Y.Z`，本地重打再推 |
| 忘记推标签 | 只 push 了代码没 push tag | `git push --tags` 补推 |
| 打了标签但没同步升版本号 | 标签和 changelog 版本脱节 | 打 tag 前先确认 changelog 归档 + 版本字段一致 |

> 真实场景（Chrome 扩展）：`web-jpg-tool`、`navi-bookmarks-chrome` 含 MV3 扩展，Chrome Web Store 版本号来自 `manifest.json`。曾出现 git tag 是 `v0.2.0` 但 `manifest.json` 还是 `0.1.0`，商店版本和源码脱节。→ 三个版本源（git tag / manifest / changelog）必须一致。

### 5.4 GitHub Release 问题

| 问题 | 原因 | 解决 |
|---|---|---|
| Release 说明与 changelog 不一致 | 手动复制遗漏 | 直接从 changelog 版本条目提取发布说明 |
| Release 指向错误的 tag | 创建时选错目标 | 删除 Release 重建，或编辑指向正确 tag |
| Release 没触发 CI/工作流 | tag 命名不含 `v` 前缀，工作流只监听 `v*` | 统一 `vX.Y.Z` tag 命名，检查工作流 `on.push.tags` 匹配 |
| 忘了打 tag 就建 Release | GitHub 要求 Release 绑定 tag | 先 `git tag vX.Y.Z && git push --tags`，再建 Release |
| Release 缺附件/产物 | 忘了手动上传构建产物 | 用 GitHub Actions 在 tag 触发时自动构建并上传 |
| Docker/容器镜像 tag 与 Release 版本不同步 | 镜像 tag 手写错 | 镜像 tag 与 git tag 用同一版本号，工作流里 `${{ github.ref_name }}` 引用 |

> 真实场景（Python 工具）：`web-jpg-tool`、`inspection-visualizer` 等 Python/OCR 工具，Release 附件常需打包可执行文件。曾出现 tag 命名不带 `v`，GitHub Actions `on.push.tags: ['v*']` 不触发，Release 一直没构建产物。→ tag 统一 `v` 前缀 + 用 `github.ref_name` 自动命名附件。

### 5.5 提交（Commit）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 提交信息不符合 Conventional Commits | 漏 `type:` 前缀或用中文混写 | `git log` 复核，用 `git commit --amend` 改最近一条 |
| 提交被 squash，破坏性变更标记丢失 | 合并 MR 时 squash 成一条 | 在 squash 后的提交信息里保留 `BREAKING CHANGE:` 脚注 |
| 改动散在多条无意义提交里 | 忘了用 `feat`/`fix` 分类 | 按需 `git rebase -i` 合并重写提交信息 |
| 发版提交和代码改动混在一起 | 分不清哪个是发版 commit | 发版独立成一条 commit（changelog 归档 + 版本字段），便于回滚和追溯 |

> 真实场景（TypeScript/CLI）：`daily-inspection-checklist` 曾把发版和功能改动塞进同一条 commit，回滚时牵连功能。→ 发版独立 commit，`git revert` 可单独回退版本号而不影响功能代码。

## 六、验证清单

- [ ] 提交信息符合 Conventional Commits 格式
- [ ] 版本号符合 SemVer（MAJOR/MINOR/PATCH 正确），与 changelog、项目版本字段（`package.json`/`pyproject.toml`/`manifest.json`）一致
- [ ] 破坏性变更已标 `!` / `BREAKING CHANGE:`，版本按 MAJOR 升
- [ ] CHANGELOG 有引导语 + `[Unreleased]`，版本条目日期 ISO、顺序倒序、六分类正确
- [ ] git 标签 `vX.Y.Z` 与版本号一致，已推送
- [ ] GitHub Release 说明与 changelog 一致，绑定正确 tag，产物/Docker 镜像齐全
