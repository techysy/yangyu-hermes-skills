# Cleaning Git History for Independent Projects

When building on top of an open-source project, you may want to drop the original project's commit history and start fresh with your own.

## Two Approaches

### Approach 1: `git-filter-repo` (keep only your commits)

Best: you cloned the original, made changes, and want to strip everything except your own commits.

```bash
# Install
pip install git-filter-repo

# Backup .git first
cp -r .git /tmp/my-repo-git-backup

# Strip commits NOT from you (by author name)
git filter-repo --commit-callback '
    if commit.author_name != b"your-username":
        commit.file_changes = []
        commit.skip()
' --force --partial
```

Then recreate assets that got wiped (LICENSE, images) from upstream and commit them.

### Approach 2: Re-init (single clean commit)

Best: you want one clean commit with current code state.

```bash
rm -rf .git
rm -rf .github/workflows/*.yml  # remove upstream CI if needed
rm -rf __pycache__ **/__pycache__ *.egg-info
git init
git add -A
git commit -m "feat: initial commit"
git branch -m master main  # rename if needed
gh repo create owner/repo --public --description "..."  # create fresh
git remote add origin https://github.com/owner/repo.git
git push origin main
```

## Common Pitfalls

- **Force push required**: both approaches rewrite history. Use `git push --force origin main`.
- **Workflow files need `workflow` scope**: force-pushing `.github/workflows/*.yml` requires a GitHub token with `workflow` scope. If your token lacks it, delete workflow files before pushing.
- **git-filter-repo wipes binary assets**: images, vendored files that came from upstream will be removed. Re-download them from the raw upstream URL after filtering.
- **License compliance**: if upstream is MIT, keep their LICENSE file and add your own copyright notice. Don't strip attribution.
- **Double replacement**: when running sed twice (replace A→B, then C→B), you can produce double-replacements. Always grep for `hermes-hermes` patterns after batch sed.
- **secret_scope empty**: `agent.secret_scope.get_secret` may not read `.env` in newer Hermes versions. Test with `$HERMES_PYTHON -c "from agent.secret_scope import get_secret; print(repr(get_secret('KEY', '')))"`. If empty, credentials won't load — fix config or env loading.
- **Version mismatch**: after renaming, check `version` field in pyproject.toml — old version may persist. Update to match your release tag.

## When to Use Which

| Situation | Approach |
|-----------|----------|
| You have 5-30 commits to keep | `git-filter-repo` |
| History doesn't matter, clean slate | Re-init |
| Need to preserve PR review history | Fork instead of clone |
