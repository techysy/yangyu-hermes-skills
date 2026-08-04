---
name: git-release-troubleshooting
description: "Git 发布/版本流程故障排查 — Conventional Commits、SemVer、Keep a Changelog、GitHub Release 落地时的常见坑（版本号升错、Unreleased 丢失、changelog 格式、标签不一致、提交被 squash、CI 不触发、产物缺失）。Use when a version number, CHANGELOG.md, git tag, or GitHub Release is wrong, missing, or inconsistent during a release, or when release output doesn't match the commits."
version: 1.1.0
platforms: [linux, macos]
---

# Git 发布 / 版本流程故障排查（Troubleshooting）

> 独立排障模块，配套 [git-project-lifecycle](../git-project-lifecycle/SKILL.md)（正向开发/版本/日志/发版全流程规范）。
> 主模块讲**应该怎么做**，本模块讲**出了问题怎么查、怎么修**。
> 按「问题 → 原因 → 解决」排查，每条附可执行命令。
> **平台无关、语言无关**——适用于任何 GitHub 开源项目（Web 应用、Python/Node 工具、Chrome 扩展、静态站点、CLI 等），不限定特定平台（如 fnOS）的开发流程。

## 一、版本号（SemVer）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 版本号升错位 | 破坏性变更没标 `!` 或 `BREAKING CHANGE:`；把 `feat` 当 `fix` 记 | 复核提交类型，再按 MAJOR/MINOR/PATCH 规则回改版本号 |
| 该升 MAJOR 只升了 MINOR | 有 BREAKING CHANGE 但漏标 | `git log --oneline` 检查提交，找出破坏性变更，标 `!` 或补脚注后升 MAJOR |
| 预发布版 vs 正式版混淆 | 忘了区分 `-beta`/`-rc` 与正式版 | 预发布用 `v1.2.3-rc.1`；正式版去掉后缀升稳定位 |
| 版本号与项目版本字段不一致 | 只改了 changelog 忘了同步代码里的版本 | 逐个核对 `package.json` / `pyproject.toml` / `Cargo.toml` / `manifest.json` 里的版本字段 |

**真实场景（Web 应用）**：`spot-studio` 这类活动发布平台改版后忘了同步 `package.json` 的 `version` 与 CHANGELOG，npm 打包出的产物版本号停留在旧版。→ 发版前统一跑 `grep '"version"' package.json` + `git tag` 三方核对。

## 二、CHANGELOG 问题

| 问题 | 原因 | 解决 |
|---|---|---|
| `[Unreleased]` 丢失 | 归档版本条目后忘了重建 | 归档后立即在顶部补 `## [Unreleased]` |
| 版本条目日期格式错 | 日期写成本地格式 | 用 ISO 8601：`## [1.2.3] - 2026-08-04` |
| changelog 顺序乱 | 新版本插到中间 | 最上方是 `[Unreleased]`，其余按时间倒序 |
| 六分类中/英文混用 | 标题不统一 | 用「`### 变更 / Changed`」双语标题，空分类省略 |
| 改动类别放错分区 | `feat` 记进 Fixed、`refactor` 记进 Added | 对照「提交类型 → Changelog 分类」表核对 |
| 忘了更新版本对比链接 | 文件底部链接仍指向旧版 | 归档后同步更新底部链接 |
| 双语项目中文/英文条目写进同一条 | 双语夹杂、读起来乱 | 每条保留双语（`中文 / English`），或分语言段落，不混写 |

**真实场景（静态站点/纯前端）**：`tianfu-greenway-ranking`、`navi-bookmarks-chrome` 这类纯 HTML/CSS/JS 项目改版频繁，changelog 常出现新版本插到中间的错——归档 `[Unreleased]` 时必须按时间倒序整体重排。

## 三、git 标签（tag）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 标签与版本号不一致 | 打错标签格式（`1.2.3` 而非 `v1.2.3`） | 统一 `vX.Y.Z`；打错删除重打 |
| 标签打在错误提交上 | 打包前忘了 commit 最新改动 | `git tag -d vX.Y.Z`，`git tag vX.Y.Z <正确SHA>` |
| 标签已推送但想改 | 远程标签无法直接覆盖 | 本地+远程都删：`git push origin :refs/tags/vX.Y.Z`，本地重打再推 |
| 忘记推标签 | 只 push 了代码没 push tag | `git push --tags` 补推 |
| 打了标签但没同步升版本号 | 标签和 changelog 版本脱节 | 打 tag 前先确认 changelog 归档 + 版本字段一致 |

**真实场景（Chrome 扩展）**：`web-jpg-tool`、`navi-bookmarks-chrome` 这类含 MV3 扩展的项目，Chrome Web Store 上架用的版本号来自 `manifest.json`。曾出现 git tag 是 `v0.2.0` 但 `manifest.json` 还是 `0.1.0`，导致商店版本和源码脱节。→ 三个版本源（git tag / manifest / changelog）必须一致。

## 四、GitHub Release 问题

| 问题 | 原因 | 解决 |
|---|---|---|
| Release 说明与 changelog 不一致 | 手动复制遗漏 | 直接从 changelog 版本条目提取发布说明 |
| Release 指向错误的 tag | 创建时选错目标 | 删除 Release 重建，或编辑指向正确 tag |
| Release 没触发 CI/工作流 | tag 命名不含 `v` 前缀，工作流只监听 `v*` | 统一 `vX.Y.Z` tag 命名，检查工作流 `on.push.tags` 匹配 |
| 忘了打 tag 就建 Release | GitHub 要求 Release 绑定 tag | 先 `git tag vX.Y.Z && git push --tags`，再建 Release |
| Release 缺附件/产物 | 忘了手动上传构建产物 | 用 GitHub Actions 在 tag 触发时自动构建并上传，避免手动遗漏 |
| Docker/容器镜像 tag 与 Release 版本不同步 | 镜像 tag 手写错 | 镜像 tag 与 git tag 用同一版本号，工作流里 `${{ github.ref_name }}` 引用 |

**真实场景（Python 工具）**：`web-jpg-tool`、`inspection-visualizer`、`film-price-tracker` 这类 Python/OCR 工具，Release 附件常需要打包好的可执行文件。曾出现 tag 命名不带 `v`，GitHub Actions 的 `on.push.tags: ['v*']` 不触发，导致 Release 一直没有构建产物。→ tag 统一 `v` 前缀 + 用 `github.ref_name` 自动命名附件。

## 五、提交（Commit）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 提交信息不符合 Conventional Commits | 漏 `type:` 前缀或用中文混写 | `git log` 复核，用 `git commit --amend` 改最近一条 |
| 提交被 squash，破坏性变更标记丢失 | 合并 MR 时 squash 成一条 | 在 squash 后的提交信息里保留 `BREAKING CHANGE:` 脚注 |
| 改动散在多条无意义提交里 | 忘了用 `feat`/`fix` 分类 | 按需 `git rebase -i` 合并重写提交信息 |
| 发版提交和代码改动混在一起 | 分不清哪个是发版 commit | 发版独立成一条 commit（changelog 归档 + 版本字段），便于回滚和追溯 |

**真实场景（TypeScript/CLI）**：`daily-inspection-checklist` 这类 TypeScript 工具，曾把发版（版本字段 + changelog）和功能改动塞进同一条 commit，回滚时牵连功能。→ 发版独立 commit，`git revert` 可单独回退版本号而不影响功能代码。

## 六、验证清单

- [ ] 版本号符合 SemVer，与 changelog、项目版本字段（`package.json`/`pyproject.toml`/`manifest.json`）一致
- [ ] 破坏性变更已标 `!` / `BREAKING CHANGE:`，版本按 MAJOR 升
- [ ] CHANGELOG 有 `[Unreleased]`、版本条目日期 ISO、顺序倒序、六分类正确
- [ ] git 标签 `vX.Y.Z` 与版本号一致，已推送
- [ ] GitHub Release 说明与 changelog 一致，绑定正确 tag，产物/Docker 镜像齐全
