---
name: git-project-lifecycle
description: "Git 项目全生命周期管理（提交规范 / 版本 / 变更日志 / 发版）— Conventional Commits 1.0.0 提交规范、SemVer 语义化版本号、Keep a Changelog 1.1.0 变更日志、发版流程。从提交到发版一站式。Use when versioning a release, writing CHANGELOG.md, deciding commit message conventions, bumping version numbers, preparing a GitHub release, or managing a project's release lifecycle."
version: 1.0.0
platforms: [linux, macos]
---

# Git 项目全生命周期管理（提交规范 / 版本 / 变更日志 / 发版）

管理 GitHub 项目从提交到发版的完整生命周期，统一三个参考规范：

- **Conventional Commits 1.0.0** — 提交信息规范（决定版本号）
- **SemVer** — 语义化版本（决定版本号位数）
- **Keep a Changelog 1.1.0** — CHANGELOG.md 格式

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

## 五、验证清单

- [ ] 提交信息符合 Conventional Commits 格式
- [ ] 版本号符合 SemVer（MAJOR/MINOR/PATCH 正确）
- [ ] CHANGELOG 有引导语 + `[Unreleased]`
- [ ] 版本 `[X.Y.Z] - YYYY-MM-DD`（方括号 + ISO 日期）
- [ ] 按时间倒序、六分类正确、无空分类
- [ ] git 标签 + GitHub Release 已创建
