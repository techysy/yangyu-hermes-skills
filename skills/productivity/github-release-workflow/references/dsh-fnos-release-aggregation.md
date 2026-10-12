# dsh-fnos 构建段 Release 聚合（techysy/deepseek-harness-fnos）

适用：`0.2.0-rc.2` → `0.2.0-rc.2.1` → `.2` → `.3` → `.4` 这类**上游版本不变、本地构建段递增**的发布系列。

## 判据：什么时候该聚合

先 `gh release list --limit 5 --json tagName,name` 看列表，再逐条 `gh release view <tag> --json assets` 看 `assets[] | .name, .size, .downloadCount`：

- 每条 4 个 fpk、单包 ~126M。**四个构建段合计约 2.5 GB**；中间几条资产的 `downloadCount` 常低到个位数（arm 种可能是 0）。
- 若中间构建段的下载量都是 0～十几次，且上层还有一个**基线 tag**（`v0.2.0-rc.2`）与**最新构建段**（`v0.2.0-rc.2.4`），把中间几条折进最新那条几乎零成本。
- 汇报时把下载数写出来（如「x86 fpk 分别 7/9/11/0 次，arm 全 0」），让用户基于事实拍，而不是凭「版本太多了」这句感觉。

## 聚合方向：两种形态，先问用户

| 形态 | 存活物 | 代价 |
|------|--------|------|
| 只删 Release 记录（tag 留） | 每条 tag 仍可 checkout；拉过 tag 的人不受影响 | `gh release list` 干净了，但 `git tag` 仍列出一长串 |
| Release + tag 都删 | 列表与 tag 列表都干净 | 删除已发布 ref 需用户明确同意；引用过该 tag 的文档/链接会断 |

用 clarify 把**两种形态与「基线 tag 留不留」一起问**，不要自己拍。用户可能选全删 tag，也可能只要记录折叠。

## 执行步骤

### 1. 备份每个待删 Release 的 body（保证可逆）

```bash
for t in v0.2.0-rc.2.1 v0.2.0-rc.2.2 v0.2.0-rc.2.3; do
  HTTPS_PROXY=http://<PROXY_HOST>:<PROXY_PORT> gh release view $t --json body --jq .body \
    > ~/.hermes/cache/scratch/dsh-${t}-body.md
done
```

### 2. 把 carrier Release 的 body 换成聚合正文

用最新构建段（`.4`）作 carrier，`gh release edit <tag> --notes-file <file>`，body 结构：

1. 标题行 + 一句 fpk 版本说明（上游未变）
2. `## 📦 聚合说明`：哪些构建段被折入、从基线 tag 可直接升到最新
3. **构建段 → 主题对照表**（例：`rc.2.1 面板重构与修复` / `rc.2.2 统一网关` / `rc.2.3 下载体验` / `rc.2.4 附件权限`）
4. `---` 分隔后，**逐个构建段全文原样保留**（`## 🚀 0.2.0-rc.2.N：<主题>` + 各自原有的修复/变更/真机验证 小节）——不压成摘要，旧页上能读到的细节新页也要能读到
5. 末尾 `## 📦 安装` 表：只列 carrier 的真实 4 个 fpk

正文里的历史构建段标题**保留当时的 emoji**；去掉 emoji 的是 Release **title**（见下）。

### 3. 删中间 Release 记录，再视授权删 tag

```bash
for t in v0.2.0-rc.2.1 v0.2.0-rc.2.2 v0.2.0-rc.2.3; do gh release delete $t --yes; done
# 仅当用户明确同意删 tag：
for t in v0.2.0-rc.2.1 v0.2.0-rc.2.2 v0.2.0-rc.2.3; do
  git push origin :refs/tags/$t && git tag -d $t
done
```

### 4. 复核（三项都做）

```bash
gh release list --limit 10 --json tagName,name,isLatest --jq '.[] | "\(.tagName) | \(.name) | latest=\(.isLatest)"'
gh release view v0.2.0-rc.2.4 --json assets --jq '.assets[].name'   # 4 个 fpk 齐全
HTTPS_PROXY=... git ls-remote --tags origin | grep -E 'rc\.2'       # 中间 tag 真的没了
```

## 本仓库特有陷阱

### `gh release list --json` 没有 `assets` 字段

`gh release list --json tagName,name,assets` 报 `Unknown JSON field: "assets"`。可用字段仅 `createdAt/isDraft/isImmutable/isLatest/isPrerelease/name/publishedAt/tagName`。要资产数就**逐条 `gh release view <tag> --json assets`**，不要往 list 里猜字段。

### 推 workflow 文件被拒 → SSH 推送（并告知用户）

CI 里 `--title "🚀 DeepSeek Harness fnOS $VERSION"` 是 Release 标题反复飘 emoji 的**源头**。修这一行 push 时会被拒：

```
! [remote rejected] main -> main (refusing to allow an OAuth App to create or update
  workflow `.github/workflows/build-fpk.yml` without `workflow` scope)
```

`gh auth status` 的 scopes 只有 `gist, read:org, repo`。非交互解法：确认 `ssh -T git@github.com` 通，再 `git remote set-url origin git@github.com:techysy/deepseek-harness-fnos.git` 推完。**推完要明确告诉用户 remote 已改成 SSH**，不要静默改掉。永久修法是 `gh auth refresh -h github.com -s workflow`（交互）。

### 改完源头后列表还可能再飘一次

修 workflow 行的同时，用户往往已经又打了个新构建段。改完源头后**必须重拉一次 `gh release list` 并一并修掉新出现的条目**，且把「改 workflow 行」与「改历史标题」当两件独立的事分别验证、分开提交。

### 与发版卡片的联动

聚合完成后，已拟好的卡片（覆盖到旧构建段）会过期：告诉用户「卡片得改成覆盖到 carrier tag」，并同步**重算卡里的提交数**——区间起点是上一个**语义版本**的已发布 tag，不是系列里第一个构建段（构建段往往只有一两个提交，拿它算会把本版说小）。
