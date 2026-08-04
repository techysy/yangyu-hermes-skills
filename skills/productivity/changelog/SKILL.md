---
name: changelog
description: "维护 CHANGELOG.md 更新日志 — 遵循 Keep a Changelog 1.1.0 规范 + 语义化版本 (SemVer)，结合中文/Conventional Commit 实践。创建新版本条目、分类变更、按时间倒序、验证格式。Use when writing or updating a CHANGELOG.md, changelog, 更新日志, release notes, or version history."
version: 1.0.0
platforms: [linux, macos]
---

# Changelog（更新日志）

维护 `CHANGELOG.md`：人工编辑、按时间倒序记录每个版本的显著变动。基于 **Keep a Changelog 1.1.0** 规范 + **SemVer**，并结合中文/Conventional Commit 实践。

> 核心原则：更新日志**不是 git log 的堆砌**，而是面向用户/开发者的显著变更精选。

## 文件结构与引导语

`CHANGELOG.md` 开头必须包含：

```markdown
# Changelog

本项目的所有显著变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]
```

## 版本条目格式

```markdown
## [1.2.3] - 2026-08-04
```

- 版本号 `[X.Y.Z]` **用方括号**（链接锚点）
- 日期 `- YYYY-MM-DD`（ISO 8601，从大到小）
- **`[Unreleased]` 永远在最顶部**，记录待发布变更
- 按**时间倒序**排列（最新在上）

## 六类变动

按 Keep a Changelog 1.1.0，最多使用六类。每类标题用 `###`：

| 类别 | 英文 | 中文 | 说明 |
|---|---|---|---|
| Added | `### Added` | `### 新增` | 新功能 |
| Changed | `### Changed` | `### 变更` | 现有功能改动 |
| Deprecated | `### Deprecated` | `### 弃用` | 即将移除的功能 |
| Removed | `### Removed` | `### 移除` | 已移除的功能 |
| Fixed | `### Fixed` | `### 修复` | Bug 修复 |
| Security | `### Security` | `### 安全` | 安全漏洞修复 |

> 推荐**中英双语标题**（如 `### 变更 / Changed`），便于中文用户和国际化读者。空分类直接省略（不占位）。

## 条目写法

```markdown
### 新增 / Added

- **功能名称** — 一句话说明做了什么
- 附带细节可用子列表或换行说明

### 修复 / Fixed

- **Bug 描述** — 根因 + 解决方式
```

规则：
- 每条 `- ` 开头，**一句话**概括要点（可加 `**加粗要点**`）
- 面向用户表达，不用内部代号
- 引用文件/代码用反引号 `` ` ``（如 `config.yaml`）
- 重要变动必须记录，保持一致（不能漏记）

## 结合 Conventional Commits

Conventional Commits 1.0.0 为提交信息提供人机可读的规范，与 SemVer 相互对应。changelog 从提交**提炼**而非照抄。

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

范围（scope）用圆括号补充上下文：`feat(parser): adds ability to parse arrays.`。破坏性变更用 `!` 标记：`feat(api)!: drop support for Node 6` 或脚注 `BREAKING CHANGE: ...`。

### 提交类型 → Changelog 分类映射

| Conventional Commit 类型 | Changelog 分类 |
|---|---|
| `feat:` / `feat(scope):` | Added / 新增 |
| `fix:` / `fix(scope):` | Fixed / 修复 |
| `refactor:` / `perf:` / `style:` / `chore:` | Changed / 变更 |
| `!` / `BREAKING CHANGE:` | Removed / 移除（若删功能）或 Changed（若改接口） |
| `docs:` | 一般不记入 changelog（除非影响用户） |
| `build:` / `ci:` / `test:` | 一般省略 |

> 破坏性变更（`BREAKING CHANGE`）在 changelog 中必须显著标注，常置于 `Removed` 或单独强调。

### SemVer 版本号规则

根据提交类型决定新版本号：
- **MAJOR**（破坏性变更 `BREAKING CHANGE` / `!`）→ `X+1.0.0`
- **MINOR**（`feat:` 新功能）→ `X.Y+1.0`
- **PATCH**（`fix:` 修复）→ `X.Y.Z+1`
- 项目若用 4 位版本（如 fnOS 应用 `0.4.4.14`），测试包累加第 4 位，正式版升第 3 位

### 生成 changelog 条目

从提交记录提炼显著变更（非照抄），按提交类型归类到对应 changelog 分类：

```bash
# 查看某版本间的提交
git log v1.2.2..v1.2.3 --oneline
```


## 版本对比链接（可选，推荐）

文件底部维护版本对比链接，便于跳转：

```markdown
[Unreleased]: https://github.com/OWNER/REPO/compare/v1.2.2...HEAD
[1.2.3]: https://github.com/OWNER/REPO/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/OWNER/REPO/compare/v1.2.1...v1.2.2
```

## 完整模板

```markdown
# Changelog

本项目的所有显著变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [1.2.3] - 2026-08-04

### 新增 / Added

- **新功能** — 说明

### 变更 / Changed

- **改动** — 说明

### 修复 / Fixed

- **修复** — 说明

## [1.2.2] - 2026-08-01

### 修复 / Fixed

- **修复** — 说明
```

## 添加新版本的流程

1. 读当前 CHANGELOG 顶部（确认最新版本号与日期）
2. 确定新版本号（SemVer：`MAJOR.MINOR.PATCH`，破坏性→MAJOR、新功能→MINOR、修复→PATCH）
3. 把当前未发布内容从 `[Unreleased]` 归档为新版本条目（或新建版本条目）
4. 顶部新建 `[Unreleased]`（若还没有）
5. 按六类分类写入变更，按时间倒序
6. 核对：版本号、日期 ISO 8601、分类、无遗漏重要变更

## 验证清单

- [ ] 开头有引导语 + `[Unreleased]`
- [ ] 版本 `[X.Y.Z] - YYYY-MM-DD`（方括号 + ISO 日期）
- [ ] 按时间倒序
- [ ] 六类变动标题正确
- [ ] 无空分类（省略）
- [ ] 条目是面向用户的显著变更（非 git log 堆砌）
- [ ] 版本对比链接正确（若用）
