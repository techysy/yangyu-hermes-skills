---
name: github-release-workflow
description: Create GitHub releases and verify CI-built assets.
category: productivity
---

# GitHub Release Workflow (Multi-Workflow Projects)

Use when creating a GitHub release that triggers multiple CI workflows (e.g., Docker image build, fnOS fpk packaging, standalone server tarball).

## Full Release Flow

### 1. Pre-flight
```bash
# Check for stale tags/releases from previous attempts
git tag -l
gh release list --limit 5
# Clean up old tags if needed
gh release delete vX.Y.Z --yes 2>/dev/null
git tag -d vX.Y.Z 2>/dev/null
git push origin :refs/tags/vX.Y.Z 2>/dev/null
```

### 2. Create Tag + Release
```bash
# Push annotated tag (triggers all workflows)
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z

# Create release with notes (workflows will attach assets to this release)
gh release create vX.Y.Z --title "Project vX.Y.Z" --notes-file /tmp/release-notes.md
```

### 3. Monitor Workflows
```bash
gh run list --limit 5
# Check specific run progress
gh run view <run_id> --json jobs --jq '.jobs[] | {name, status, conclusion}'
# Cancel stuck runs: gh run cancel <run_id>
```

**Note**: Multi-platform Docker builds (amd64+arm64) typically take 15-20+ minutes. Check job steps progress before assuming stuck.

### 4. Verify Assets
```bash
gh release view vX.Y.Z --json assets --jq '.assets[].name'
# Expected for 10router: 4 fpk + server.tar.gz
```

### 5. Fix Overwritten Release Notes (Common Pitfall)

**Problem**: Some workflows auto-create the release when a step attaches a file, using a generic default body and a bare-tag title. Two distinct failure shapes:

- The workflow passes its own default `--notes`, replacing your text.
- The workflow passes *neither* `--notes` nor `--title` (deliberately, so manual notes survive re-runs) — then **whichever workflow finishes first creates the release with an empty body and the bare tag as title**. Later attach steps only add files and never fill in notes.

**Fix** (after the tag is pushed):
```bash
gh release edit vX.Y.Z --notes-file /tmp/release-notes.md
gh release edit vX.Y.Z --title "Project vX.Y.Z"      # title is a SEPARATE field
```

**Prevention**: add an ensure-release step **before** every attach step: if the release already exists, do nothing; if not, create it with the correct title and a placeholder body (`--notes "Release notes pending — see CHANGELOG"`). A placeholder `--notes ""` alone is not enough — an empty body still reads as "notes missing" in the release list.

**Third shape — the workflow passes a `--title` that contradicts the project's naming convention** (typically an emoji prefix while the convention is bare `project vX.Y.Z`). Whatever you fix by hand, the next CI-created release comes back wrong: a manual `gh release edit` is a one-off, the workflow line is the source. Confirm the intended direction with the user first (drop the emoji, or keep it everywhere — never pick unilaterally), then edit that line; locate it with `grep -rn 'gh release create' .github/workflows/` and confirm with a full `gh release list` after fixing history.

**Expect the source to fire again before you finish.** Fixing the workflow line does not retract releases CI already created in the meantime — while you were auditing, a new tag may have been built and published already wrong. After editing the line: (a) `gh release list --limit 5` again and fix any entry that appeared since, and (b) keep the workflow fix and the history fix as **separate commits/actions**, each with its own verification — a one-line workflow change is easy to hide inside a large release commit. If the push of that one-line change is rejected for `workflow` scope, see the pitfalls table.

### 5b. Audit the whole release list after publishing

A new release is rarely the only one out of shape. After publishing, scan the list and fix in one pass:

```bash
gh release list --limit 30
```

Check three things across **all** entries, not just the new one:

| Check | Fix |
|-------|-----|
| Title format consistent (project name + tag, vs bare tag) | `gh release edit <tag> --title "<project> <tag>"` |
| Body non-empty and ends with a compare link | `gh release edit <tag> --notes-file …` (add `**Full Changelog**: …/compare/<prev>...<tag>`) |
| Pre-release rc series cluttering the list as N separate entries | Fold into ONE summary release, then delete the redundant release records |

**Folding an rc series**: keep the newest rc as the carrier — rename it to the merged title (e.g. `Project vX.Y.0（预览版 · rc1-rcN 汇总）`) and replace its body with a consolidated summary organized by theme. Worked end-to-end example for a build-segment series (upstream version unchanged, local `X.Y.Z.N` increments): `references/dsh-fnos-release-aggregation.md`.

**Ask the user which to do — they differ in risk and the user has a strong preference:**

| Shape | What survives | Cost |
|-------|---------------|------|
| **Records-only fold** (default when unsure) | Tags keep every rc reachable; anyone who pulled them still builds | `Release` rows gone but `git tag` still lists them |
| **Records + tags removed** | Released list is genuinely clean; no orphan tags | Anyone who pulled an intermediate tag, or any doc/link naming it, breaks. Requires deleting published refs — get explicit consent first |

Whichever the user picks, **back up each doomed release's body before deleting it** (`gh release view <tag> --json body --jq .body > scratch/<tag>-body.md`) so the fold is reversible, and report the backup path. Also ask whether to keep the series' **baseline tag** (the non-.N one, e.g. `v0.2.0-rc.2`) — keeping it preserves one working download link and costs one row; folding it in leaves a single latest release.

**Decide to fold on evidence, not on aesthetics.** Check the asset download counts first (`gh release view <tag> --json assets` → `downloadCount`) and the per-release asset weight (an rc series of 4 fpk × N builds reaches GBs). A handful of downloads on the intermediate tags means folding is nearly free; non-zero meaningful downloads on one of them means keep that one. Say which numbers drove the call when reporting.

**The aggregated release must carry the content, not just a promise.** Build its body as: (1) a short "聚合说明" stating which builds were folded and that rc.2 can jump straight to latest; (2) a table mapping each folded build → its theme; (3) each folded release's **full original sections, verbatim** (demote each to `## <version>：<主题>`), never summarize away the detail the old pages held; (4) a re-stated install/download table pointing at the carrier's real assets. Use `--notes-file` with the assembled markdown — a one-paragraph summary loses information users could previously read.

**Full Changelog 的起点**：用上一个**语义**版本，不是列表里紧邻的那个 rc/补丁 tag。

### 6. Verify Docker Image
```bash
TOKEN=$(gh auth token)
REG_TOKEN=$(curl -s -u "owner:$TOKEN" "https://ghcr.io/token?scope=repository:owner/repo:pull" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -s -H "Authorization: Bearer $REG_TOKEN" -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" "https://ghcr.io/v2/owner/repo/manifests/X.Y.Z" | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['platform']['os']+'/'+m['platform']['architecture'] for m in d.get('manifests',[])])"
```

### 7. Notify (optional)
Send Feishu card via `feishu-bot-cards` skill / `scripts/release_notify.py`.

### 8. 回答「vX 之后更新了什么」/「A 到 B 之间改了什么」

用户会反复问这个（决定是否升级、写发版卡片）。固定动作：

```bash
git fetch --tags origin                        # 本地 tag 常落后，先 fetch
git tag --sort=-v:refname | head -6            # 最新 tag
tag=$(git tag --sort=-v:refname | head -1)
gh release list --repo <repo> --limit 6        # 哪些真发布了、Latest 是谁
git rev-list --count <上一个已发布tag>..<本tag>  # 提交数：起点必须是上一个已发布 tag
git log --format='%h|%ad|%s' --date=short <range>
```

- **`origin/main` 领先最新 tag 是常态**（发版后仍在提交）。答「最新版有什么」用 tag；答「仓库最新有什么」用 `git log <最新tag>..origin/main`；两个数字分开报，并点明有无未发版内容。
- **部分 tag 的 Release body 只是占位符**（`Release notes pending — see CHANGELOG.md`，build workflow 先建空壳所致）。这时内容去**该 tag 自己的 CHANGELOG** 取：`git show <tag>:CHANGELOG.md`，按 `## vX.Y.Z` 段落读——比 `gh release view` 可靠。先看 body 长度，一行以内的直接转 CHANGELOG。
- 类型分布小计：`git log --format=%s <range>` 后按 `^(\w+)(\(.*?\))?!?:` 归类计数，报 `fix N · feat N · docs N`。
- 跨多版本问（「vA 之后」）时**逐 tag 分别报**，每个给主题行 + 要点，末尾再汇总共同趋势。

## Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Workflow default description overwrites manual release notes | Use `gh release edit` after workflows complete; add `--notes ""` to workflow release steps |
| First-finishing attach step creates the release with empty body + bare-tag title | Insert an ensure-release step **before** every attach step (create with title + placeholder notes only if absent) |
| Title left as bare tag while notes were fixed | `--title` is a separate field — check `gh release list` after editing notes |
| Titles drift back after you fix them (emoji / format mismatch recurring every release) | A packaging workflow hardcodes its own `--title`; align history once with `gh release edit`, then change that workflow line — otherwise each CI build reintroduces the mismatch |
| rc series occupies N rows in the release list | Fold into one summary release (newest rc as carrier, body = every folded release's sections verbatim + a build→theme table). **Ask the user first** whether to delete only the release records or also the intermediate git tags — both are legitimate, and tag deletion needs explicit consent. Back up each doomed body to a scratch file before deleting |
| Release list titles drift out of shape across versions (emoji added by CI, extra words, bare tag) | Fix **all** offenders in one pass (`gh release list --limit 30 --json tagName,name`, compare horizontally), not just the newest. **Ask the user which direction to align** (add the prefix everywhere vs strip it everywhere) before editing. Then find the source: `git ls-tree --name-only origin/main .github/workflows/` + `git show origin/main:<file> \| grep -n 'gh release'` — a hardcoded `--title` in a packaging workflow reintroduces the mismatch on every CI build, so report it and offer the one-line workflow fix. Editing release records never touches git tags |
| `gh release view` 显示「Release notes pending」就当没内容可答 | Release body 是 workflow 占位符时，真实内容在 **tag 自带的 CHANGELOG.md**：`git show <tag>:CHANGELOG.md`（见 §8） |
| Old tag/release from failed attempts blocks new release | Always clean up old tags before re-tagging |
| Multi-platform Docker build takes 15-20+ min, looks stuck | Check job steps progress before canceling |
| `gh release create` fails due to tag/release state mismatch | Ensure tag is pushed first, then create release |
| Tag already pushed but `gh release view` reports *not found* (Release never created, so nothing consumed the tag) | **Do not bump to a new patch version just to preserve the tag.** Fold the new work into the same version (archive `[Unreleased]`, set the CHANGELOG date to the real publish day), then `git tag -f -a vX.Y.Z` onto the new commit + `git push --force origin vX.Y.Z`, then create the Release. Whether to keep or bump the version number is the user's call, never yours |
| Push rejected because remote advanced while you prepared the release | `git fetch` then rebase; resolve conflicts by **keeping the remote's newer structure and re-applying only your own delta** (if remote rewrote the whole doc, take its version block by block and re-insert your wording — do not paste your stale copy back over it). Run the full test suite before pushing; never `--force` over remote commits |
| Fixing a workflow's `--title` line and the push is rejected: `refusing to allow an OAuth App to create or update workflow .github/workflows/x.yml without workflow scope` | The commit is fine — the token lacks the `workflow` scope and the commit touches `.github/workflows/`. Check with `gh auth status \| grep -i 'Token scopes'`; a plain gh login usually has only `gist, read:org, repo`, which stays invisible until the first CI-file edit. Permanent fix: `gh auth refresh -h github.com -s workflow` (interactive). Non-interactive escape: `ssh -T git@github.com` to confirm the key, then `git remote set-url origin git@github.com:<owner>/<repo>.git` and push — and **tell the user the remote URL is now SSH**, do not leave it silently changed. Never revert the workflow edit or force-push to get around it |

## User Preferences

- Release tag & title: NO emoji (pure version like `v1.0.0`)
- Release body/notes: emoji OK
- README: badges + emoji OK
- Wrapper apps: version aligned to upstream, no cosmetic suffix
