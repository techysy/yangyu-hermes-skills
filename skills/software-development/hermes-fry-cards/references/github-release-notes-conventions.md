# GitHub Release 发版规范（v0.1.1 实践总结）

> 2026-08-23 发布 v0.1.1 首个正式版过程中沉淀。适用于 hermes-fry-cards 及同构的 GitHub 开源项目发版。

## Full Changelog 对比链接（用户指定格式）

Release 正文末尾必须补一行 compare 链接，格式同 GitHub 自动生成：

```
**Full Changelog**: https://github.com/<owner>/<repo>/compare/<起点>...<tag>
```

**起点 = 本开发周期的第一个 tag**，不是紧邻的上一个 tag。
例：正文写「rc2–rc7 七轮迭代」→ 链接用 `compare/v0.1.0-rc2...v0.1.1`，用户会核对两者一致性。

## Release Notes 重写

- 每次发版重写 `release-notes.md`，禁止沿用旧稿（曾把 rc2 的 notes 原样带进正式版）
- 结构：版本定位一句话 → 本次变更分类详述 → 安装/卸载命令 → 页脚链接
- 正式版标题不带 rc 后缀；`gh release create` 不加 `--prerelease`

## README 一致性清扫（用户逐项验收，漏做必被指出）

发版提交后对 README 做一遍：

1. 版本徽章 `Release-vX.Y.Z`
2. 相对链接按仓库实际路径逐一核对（曾发生 OPTIMIZATION_PLAN.md 移入 docs/ 后根路径引用 404）
3. 「相关项目」表 star 数刷新：`gh api repos/<owner>/<repo> --jq .stargazers_count`
4. 扫描损坏 emoji：历史提交可能把 emoji 写坏成 U+FFFD 替换符（�）字面量，
   python 检查 `'\ufffd' in text`，按语义恢复原 emoji
5. 新特性是否需要正文体现：纯内部重构可只加稳定性小节 + 日志事件表

## Gotchas

- PR body / release notes 含「hermes gateway restart」类命令字符串 → Hermes 网关安全拦截
  （防 SIGTERM 自杀）。措辞改「在独立 shell 重启网关」。
- 本机 editable 安装：`pip show` 显示旧版本号但代码即时生效；新代码需外部 shell 重启网关加载。
- 旧 release 资产找回当底稿：`gh release download <tag> -D /tmp/x`（skill.md 曾只存在于旧资产中）。
- 资产覆盖重传用 `gh release upload <tag> <file> --clobber`。

## 标准资产清单

`INSTALL.md` + `hermes-fry-cards-skill.md`（后者同时入库仓库根目录并随代码维护）。
