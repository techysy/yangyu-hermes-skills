# Cherry-pick Upstream Features, Then Filter by Author

Session pattern from 2026-08-23 (10router cleanup).

## Scenario

User has a fork with extensive upstream history (decolua/9router, 1122 commits). They want to:
1. Cherry-pick specific upstream features into their fork
2. Then remove ALL upstream history, keeping only their own + collaborators' commits

## Workflow

### Phase 1: Cherry-pick features onto a branch

```bash
# Work on master (or a feature branch)
git checkout master

# Cherry-pick specific commits by the user (already in their fork)
# These are commits that were made in the user's own fork, not upstream
git cherry-pick <commit-hash>

# Resolve conflicts manually, preferring user's existing code when
# upstream structure has diverged significantly
git checkout --ours <file>   # or --theirs, then manually merge
git add <file>
git cherry-pick --continue
```

### Phase 2: Merge to master, then filter

```bash
# Merge feature branch to master
git checkout master
git merge 9router-fork --no-edit

# NOW filter by author (keep-list)
git filter-repo --commit-callback '
    allowed = [b"techysy", b"ShiYanG Yu", b"monkey2jack"];
    commit.skip() if commit.author_name not in allowed else None
' --force --partial
```

### Phase 3: Clean up branches and push

```bash
# Delete all old branches (local + remote)
git branch -D 9router-fork catalinstanciu92/master master-backup-*
git push origin --delete 9router-fork catalinstanciu92/master master

# Force push the filtered main
git push origin HEAD:main --force
```

## Key Lessons

1. **Always backup .git before filter-repo** — `cp -r .git /tmp/backup`
2. **Verify backup works** — `cd /tmp/backup && git log --oneline -3`
3. **Use keep-list, not drop-list** — easier to audit what survives
4. **NEVER use `git init` to "clean history"** — destroys everything
5. **Cherry-pick conflicts are common** when upstream structure diverges — resolve manually
6. **Some commits may be lost** if they touch files that were deleted (e.g., monkey2jack's docker-publish.yml commit was lost because workflows were deleted)

## Recovery from Mistake

If you accidentally used `git init` and lost history:
```bash
# Restore from backup
mv .git /tmp/broken-single-commit
cp -r /tmp/myrepo-git-backup .git
git checkout master  # history restored
```
