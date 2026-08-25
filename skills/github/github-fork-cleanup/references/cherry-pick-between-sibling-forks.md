# Cherry-picking Feature Commits Between Sibling Forks

Context: user maintains several 9router derivatives (techysy/9router, techysy/10router, \*-fnos packs). Recurring task: move a set of feature commits from one checkout to another WITHOUT dragging decolua upstream history along.

## Workflow

1. Wire the source repo as a local remote on the target:
   ```bash
   git -C ~/projects/<target> remote add fryup ~/projects/<source>
   git -C ~/projects/<target> fetch fryup master
   ```
2. Branch off the target mainline: `git checkout -b <source>-fork master`
3. Map the commit chain (`git log --oneline <range>`), then cherry-pick IN ORDER, skipping chore/noise commits (CI-workflow adds, bare "Update xx.json", WIP) — pick only feat/fix commits.
4. Conflict resolution patterns observed:
   - Target component structurally diverged (own rewrite, e.g. custom UsageStats) → `git checkout --ours <file> && git add`. The rest of the feature (settingsRepo persistence, providers-page toggle, constants) still lands, so the switch exists even if one integration point waits.
   - Same hunk edited differently (e.g. locale handling in profile page) → hand-merge: keep target's improvement AND add incoming feature lines. Afterwards `grep -rn '<<<<<<<' src` to catch leftovers.
5. Rode-along junk: picked commits can carry dev artifacts (`.workbuddy/` memory dirs, stray zero-byte files). Finish with `Chore: remove dev artifacts ...` cleanup commit.
6. Verify by running ONLY the newly added test files, borrowing vitest deps from the sibling checkout (avoids a full install):
   ```bash
   cd tests && ln -sfn ~/projects/<source>/tests/node_modules node_modules \
     && npx vitest run unit/<new-tests>.test.js && rm node_modules
   ```
7. Fast-forward merge into mainline and push. If the branch itself must contain only your authors' commits, use the SKILL.md filter-repo flow instead.

## Gotchas

- Multi-commit `git cherry-pick A B C` halts at the first conflict: resolve → `git add` → `git -c core.editor=true cherry-pick --continue`.
- An uncommitted stash on the branch blocks picking ("local changes would be overwritten") → `git stash` first, pop after.
- An aborted/interrupted pick leaves untracked strays (half-created files) that block the retry: `git cherry-pick --quit` (or `--abort`), delete strays, re-run.
- Dry-run the final merge: `git merge-tree $(git merge-base main <branch>) main <branch> | grep -c '^<<<<<<<'` — 0 means clean.
- `git rm -r` on a directory flagged by safety scanners is expected; it stages deletions only, nothing leaves disk until commit+push.
