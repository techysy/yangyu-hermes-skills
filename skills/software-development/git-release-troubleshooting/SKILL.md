---
name: git-release-troubleshooting
description: "Git 发布/版本流程故障排查 — Conventional Commits、SemVer、Keep a Changelog、GitHub Release 落地时的常见坑（版本号升错、Unreleased 丢失、changelog 格式、标签不一致、提交被 squash）。Use when a version number, CHANGELOG.md, git tag, or GitHub Release is wrong, missing, or inconsistent during a release, or when release output doesn't match the commits."
version: 1.0.0
platforms: [linux, macos]
---

# Git 发布 / 版本流程故障排查（Troubleshooting）

> 独立排障模块，配套 [git-project-lifecycle](../git-project-lifecycle/SKILL.md)（正向开发/版本/日志/发版全流程规范）。
> 主模块讲**应该怎么做**，本模块讲**出了问题怎么查、怎么修**。
> 按「问题 → 原因 → 解决」排查，每条附可执行命令。

## 一、版本号（SemVer）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 版本号升错位 | 破坏性变更没标 `!` 或 `BREAKING CHANGE:`；把 `feat` 当 `fix` 记 | 复核提交类型，再按 MAJOR/MINOR/PATCH 规则回改版本号 |
| 该升 MAJOR 只升了 MINOR | 有 BREAKING CHANGE 但漏标 | `git log --oneline` 检查提交，找出破坏性变更，标 `!` 或补脚注后升 MAJOR |
| 4 位版本（fnOS）第 3/4 位混淆 | 测试包升了第 3 位，或正式版累加了第 4 位 | 测试包累加第 4 位 `0.4.4.x`；正式版才升第 3 位 `0.4.5` |
| 版本号与 `package.json`/manifest 不一致 | 只改了 changelog 忘了同步项目版本字段 | `grep '"version"' package.json` 核对，改到与 changelog 一致 |

## 二、CHANGELOG 问题

| 问题 | 原因 | 解决 |
|---|---|---|
| `[Unreleased]` 丢失 | 归档版本条目后忘了重建 | 归档后立即在顶部补 `## [Unreleased]` |
| 版本条目日期格式错 | 日期写成本地格式 | 用 ISO 8601：`## [1.2.3] - 2026-08-04` |
| changelog 顺序乱 | 新版本插到中间 | 最上方是 `[Unreleased]`，其余按时间倒序 |
| 六分类中/英文混用 | 标题不统一 | 用「`### 变更 / Changed`」双语标题，空分类省略 |
| 改动类别放错分区 | `feat` 记进 Fixed、`refactor` 记进 Added | 对照「提交类型 → Changelog 分类」表核对 |
| 忘了更新版本对比链接 | 文件底部链接仍指向旧版 | 归档后同步更新底部链接 |

## 三、git 标签（tag）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 标签与版本号不一致 | 打错标签格式（`1.2.3` 而非 `v1.2.3`） | 统一 `vX.Y.Z`；打错删除重打 |
| 标签打在错误提交上 | 打包前忘了 commit 最新改动 | `git tag -d vX.Y.Z`，`git tag vX.Y.Z <正确SHA>` |
| 标签已推送但想改 | 远程标签无法直接覆盖 | 本地+远程都删：`git push origin :refs/tags/vX.Y.Z`，本地重打再推 |
| 忘记推标签 | 只 push 了代码没 push tag | `git push --tags` 补推 |

## 四、GitHub Release 问题

| 问题 | 原因 | 解决 |
|---|---|---|
| Release 说明与 changelog 不一致 | 手动复制遗漏 | 直接从 changelog 版本条目提取发布说明 |
| Release 指向错误的 tag | 创建时选错目标 | 删除 Release 重建，或编辑指向正确 tag |
| Release 没触发 CI/工作流 | tag 命名不含 `v` 前缀，工作流只监听 `v*` | 统一 `vX.Y.Z` tag 命名 |
| 忘了打 tag 就建 Release | GitHub 要求 Release 绑定 tag | 先 `git tag vX.Y.Z && git push --tags`，再建 Release |

## 五、提交（Commit）问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 提交信息不符合 Conventional Commits | 漏 `type:` 前缀或用中文混写 | `git log` 复核，用 `git commit --amend` 改最近一条 |
| 提交被 squash，破坏性变更标记丢失 | 合并 MR 时 squash 成一条 | 在 squash 后的提交信息里保留 `BREAKING CHANGE:` 脚注 |
| 改动散在多条无意义提交里 | 忘了用 `feat`/`fix` 分类 | 按需 `git rebase -i` 合并重写提交信息 |

## 六、验证清单

- [ ] 版本号符合 SemVer，与 changelog、项目版本字段一致
- [ ] 破坏性变更已标 `!` / `BREAKING CHANGE:`，版本按 MAJOR 升
- [ ] CHANGELOG 有 `[Unreleased]`、版本条目日期 ISO、顺序倒序、六分类正确
- [ ] git 标签 `vX.Y.Z` 与版本号一致，已推送
- [ ] GitHub Release 说明与 changelog 一致，绑定正确 tag
