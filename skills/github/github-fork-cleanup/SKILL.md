---
name: github-fork-cleanup
description: "Fork → standalone repo: clean history, attribution, rename."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Fork, History, Attribution, LICENSE, Clean]
    related_skills: [github-repo-management, github-pr-workflow]
---

# GitHub Fork → Standalone Cleanup

When you've cloned/forked an open-source project, made extensive local modifications, and need to publish as a **standalone repo** (not a GitHub fork) with clean history and legal attribution.

## Trigger

- "复刻" / "重新建仓库" / "清空历史"
- "把原项目历史清掉"
- "包名、仓库名、GitHub URL 统一"
- Cloned upstream, made major changes, want clean independent repo

## Workflow

### 1. Install git-filter-repo

```bash
pip install git-filter-repo
```

### 2. Backup .git

```bash
cp -r .git /tmp/myrepo-git-backup
```

### 3. Filter History to Allowed Authors (NEVER git init!)

**CRITICAL**: The goal is to **drop upstream/third-party commits** while keeping your own and collaborators'. Always use `git filter-repo` with an **allowlist** of authors to keep — never `git init` + single commit (that destroys ALL commits including yours).

```bash
# Step 0: Identify authors to keep vs drop
git log --format="%an|%ae" | sort | uniq -c

# Step 1: Backup and verify
cp -r .git /tmp/myrepo-git-backup
cd /tmp/myrepo-git-backup && git log --oneline -3 && cd -

# Step 2: Filter — keep ONLY named authors, skip everything else
git filter-repo --commit-callback '
    allowed = [b"your-username", b"Friend-Name"];
    commit.skip() if commit.author_name not in allowed else None
' --force --partial
```

**Verify before proceeding**:
- Backup is restorable (`cd /tmp/backup && git log` works)
- Filter direction is **keep-list**, not drop-list (safer to audit)
- User explicitly named BOTH authors-to-keep AND authors-to-drop

### 4. Recover Binary Assets from Upstream

Binary files (images, etc.) often don't survive filter-repo. Re-fetch from original:

```bash
mkdir -p assets
curl -sL "https://raw.githubusercontent.com/owner/repo/main/assets/image.jpg" -o assets/image.jpg
```

### 5. Add LICENSE (Preserve Copyright)

Fetch original LICENSE — MIT requires preserving copyright notice:

```bash
curl -sL "https://raw.githubusercontent.com/owner/repo/main/LICENSE" -o LICENSE
```

### 6. Add .gitignore

Prevent build artifacts from polluting new history:

```gitignore
__pycache__/
*.pyc
*.pyo
.eggs/
*.egg-info/
build/
dist/
.pytest_cache/
tests/samples/
```

### 7. Clean Build Artifacts

```bash
rm -rf .git
rm -rf .github/workflows/*.yml    # workflows need workflow scope token
rm -rf */__pycache__ */*/__pycache__
rm -rf *.egg-info
rm -rf tests/__pycache__ tests/samples
rm -rf .pytest_cache
```

### 8. Rename Package/Repo Consistently

User preference: **repo name = PyPI package name = GitHub URL name**.

When renaming Python packages (e.g., `hermes_potato_stream` → `hermes_fry_cards`):

```bash
# 1. Rename directory
mv old_package new_package

# 2. Replace all references
find . -path './.git' -prune -o -type f \( -name "*.py" -o -name "*.toml" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \) -exec sed -i 's/old-name/new-name/g' {} +
```

Verify no stragglers:

```bash
grep -rn "old-name" . --include="*.py" --include="*.toml" --include="*.md" | grep -v __pycache__
```

### 9. Reinit and Single Commit (ONLY for truly blank-slate rewrites)

**DANGER**: This step destroys ALL existing history including your own commits and collaborators'. ONLY use when you genuinely want a fresh repo with a single commit (e.g., package rename with clean-slate intent). NEVER use this to "clean upstream history" — use Step 3's filter-repo keep-list instead.

```bash
git init
git add -A
git commit -m "feat: init <project-name> — <description>"
git branch -m master main    # rename default branch if needed
```

### 10. Create and Push

```bash
gh repo create owner/repo-name --public --description "Description"
git remote add origin https://github.com/owner/repo-name.git
git push origin main
```

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| Workflow scope error | Pushing `.github/workflows/*.yml` requires token with `workflow` scope. Standard OAuth lacks this. Either get PAT with workflow scope or omit workflows and add later via GitHub UI. |
| `hermes-hermes-fry-cards` double replacement | Running sed twice (replace A→B, then C→B) can produce double-replacements. Always grep for `"hermes-hermes"` after batch sed. |
| Force push overwrites | `git push --force` rewrites remote history. Warn collaborators. |
| LICENSE forgotten | MIT requires preserving copyright notice. Always fetch original LICENSE. |
| Binary assets lost | Images don't survive filter-repo. Re-fetch from upstream raw URL. |
| CHANGELOG stale | Original CHANGELOG entries persist after history cleanup. Rewrite to only include your project's releases. |
| Old references remain | After renaming package, grep ALL file types (.py, .toml, .md, .yml, .yaml) for old name. |
| GitHub delete token | `gh repo delete` requires `delete_repo` scope. Standard OAuth lacks this. Use GitHub Settings → Delete repository manually. |

## User Preferences (Embedded)

- **Clean start over patching**: When repo history gets messy, user prefers `git init` + single commit over incremental fixes. ⚠️ BUT only if the user explicitly says "blank slate / fresh start" — NOT when they say "remove upstream commits" (which means keep their own + collaborators' history).
- **Name consistency**: GitHub repo name = PyPI package name = import path (e.g., `hermes-fry-cards` / `hermes_fry_cards`).
- **README full rewrite**: When content is stale, user wants full rewrite not partial patch.
- **No contribution carryover**: When cleaning history, remove original project's contributor avatars/sections.
- **Preserve own + friends' commits**: If the user says "don't want upstream commits" or "remove decolua", they mean **keep their own and collaborators' commits**, not "destroy everything and start fresh". Always filter-repo with allowlist, never `git init`.
