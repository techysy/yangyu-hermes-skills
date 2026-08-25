# Incident: author-filter rewrite silently deleted 52 runtime files

Repo: `techysy/10router` (fork-style local repo of decolua/9router), 2026-08-24.

## What happened

Goal: strip all upstream (decolua + third-party contributors') commits, keep only
techysy / ShiYanG Yu / monkey2jack (friend). Ran:

```bash
git filter-repo --commit-callback '
allowed = [b"techysy", b"ShiYanG Yu", b"monkey2jack"];
commit.skip() if commit.author_name not in allowed else None
' --force --partial
```

**Important**: friend's GitHub login is `monkey2jack` (display name: 糖小猴), **not** `monlor` — `monlor` is a different contributor. Always verify the exact GitHub username (e.g. via the GitHub profile URL) before putting it in the allowlist.

1122 commits → 11. Looked clean. Then `npm run build` failed with
`Module not found: Can't resolve '@/shared/constants/cliTools'` — and clearing `.next`
did not help, because **the imported file chain itself was gone**.

## Root cause

`commit.skip()` removes the commit *and its tree changes*. 51 files whose last-modifying
commit belonged to a filtered author disappeared from the tip entirely:

- `jsconfig.json`, `eslint.config.mjs`, `package-lock.json` (build config)
- `src/lib/oauth/services/*.js`, `src/lib/usageDb.js`, `src/lib/db/index.js` companions
- `src/app/api/auth/login|logout/route.js`, dashboard pages (`UsageStats.js`, …)
- `public/*.svg`, favicon

The surviving commits (cherry-picked optimizations) *referenced* these files, so the
module graph was broken everywhere at once.

## Detection

```bash
# inventory diff between raw .git backup and rewritten checkout
git ls-files | sort > /tmp/new-files.txt
git --git-dir=/tmp/10router-git-backup-0823 ls-tree -r master --name-only | sort > /tmp/old-files.txt
comm -23 /tmp/old-files.txt /tmp/new-files.txt          # lost = in old, absent in new
```

Build errors are the secondary detector, but only catch files that are actually imported;
inventory-diff catches everything (e.g. unused-but-wanted assets).

## Recovery

The pre-rewrite `cp -r .git /tmp/10router-git-backup-0823` was the savior — filter-repo
rewrites history in place, so without that copy the old objects are unreachable.

```bash
# restore all lost files (minus intentionally deleted: gitbook/, old workflows)
cd /tmp/10router-git-backup-0823
git archive master $(cat lost-files.txt | tr '\n' ' ') | tar -x -C ~/projects/10router
git add -A && git commit -m "Chore: restore files lost in history rewrite"
```

(`git archive` handles missing parent dirs better than shell redirection.)

## Post-restore fixes that were needed

1. **Legacy `src/middleware.js`** came back and collided with `src/proxy.js`
   (Next.js 16: "Both middleware file and proxy file detected"). The proxy variant
   (backed by `dashboardGuard`) covered the same JWT guard + `/`→`/dashboard` redirect,
   so the legacy file was deleted again.
2. **Shim re-export gaps**: `open-sse/handlers/chatCore.js` imports
   `saveRequestDetail/getRequestDetails/getActiveRequests/getChartData/statsEmitter`
   from `@/lib/usageDb`, but those functions now live in the SQLite layer
   (`src/lib/db/*`). Added explicit re-exports in `usageDb.js`. Webpack surfaces these
   as "Attempted import error" warnings — iterate until build is warning-clean.

## Verification checklist after any history surgery

```bash
npm run build                      # zero errors AND zero attempted-import warnings
PORT=<p> npm run start &           # boot the standalone/custom server
curl localhost:<p>/api/health      # {"ok":true}
curl -o /dev/null -w "%{http_code}" localhost:<p>/dashboard   # 307 → login expected
```

## Process lessons

- Take the `.git` backup BEFORE touching history, every time; it converted a disaster
  into a 5-minute fix.
- An earlier "clean rebuild" attempt (fresh `git init`, single squash commit) had also
  been wrong for this user — see the author-scope preference in SKILL.md. The correct
  target was "remove decolua's commits", i.e. an author-scoped rewrite, not a squash.
