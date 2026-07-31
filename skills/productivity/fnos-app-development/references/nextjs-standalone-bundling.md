# Next.js Standalone App Bundling (fnOS package)

For wrapping a Next.js web app whose **npm package ships a prebuilt standalone server** — e.g. 9Router (`decolua/9router`, port 20128, MIT). Verified 2026-07-31 with 9router@0.5.45 on fnOS 1.1.31xx.

## When to use this pattern

The skill's standard Node.js cookbook (npm install at install_init) requires the NAS to reach npm at install time. When the project publishes a standalone build inside its npm package, **bundle it into `app/server/` at build time** — zero network dependency at install, smaller blast radius.

## How to know the npm package is standalone-capable

```bash
npm pack <pkg>@latest          # download tarball
tar tzf <pkg>-*.tgz | head     # inspect
```

A standalone-capable package contains `package/app/` with:
- `custom-server.js` (optional wrapper, e.g. real-IP injection)
- `server.js` (Next standalone entry; reads `PORT`, `HOSTNAME`, sets `distDir`)
- `.next-cli-build/` ← **the production build** (BUILD_ID, server/, static/)
- `node_modules/` (traced subset — may be incomplete!)
- `public/`, `src/`

## ⚠️ Pitfall: `cp -r pkg/app/*` silently skips dot-directories

`bash` glob `*` does NOT match hidden entries. `.next-cli-build` starts with a dot, so:

```bash
cp -r /tmp/9r_pkg/package/app/* app/server/   # ❌ .next-cli-build NOT copied!
```

Result: server starts, prints "✓ Ready", then dies with
`Error: Could not find a production build in the './.next-cli-build' directory.`

**Fix — copy the dot-dir explicitly:**
```bash
cp -r /tmp/9r_pkg/package/app/.next-cli-build app/server/
```

## Pitfall: standalone node_modules may miss runtime deps

Next standalone tracing only keeps what server.js imports at build time. **Diff against the project's Dockerfile** — it lists what must be copied back:

9router Dockerfile does:
```dockerfile
COPY --from=builder /app/src/mitm ./src/mitm                      # MITM child process
COPY --from=builder /app/node_modules/node-forge ./node_modules/node-forge
COPY --from=builder /app/open-sse ./open-sse                      # quota ping service
```

For 9router@0.5.45 specifically: `node-forge` was MISSING from the npm standalone (needed by MITM cert generation). `open-sse` was NOT in the npm package at all — but also not referenced by the bundled build, so skip it (verify with `grep -rl "open-sse" .next-cli-build/server/`). Check requires in the wrapper: `grep -oE 'require\("[^"]+"\)' server.js` — 9router's only needs `next`.

## Lifecycle scripts (cmd/main)

⚠️ **SRC_DIR must be detected, not assumed** — on fnOS 1.1.31xx `TRIM_APPDEST=/vol4/@appcenter/<App>` (server directly under it); older versions `/var/apps/<App>` (server under `target/`). Hardcoding `target/server` produces 无法启用 / 本地应用启动失败 (log: `cd: .../target/server: No such file or directory`):

```bash
APP_DIR="${TRIM_APPDEST:-/var/apps/${APP_NAME}}"
if [ -d "${APP_DIR}/server" ]; then
    SRC_DIR="${APP_DIR}/server"
elif [ -d "${APP_DIR}/target/server" ]; then
    SRC_DIR="${APP_DIR}/target/server"
else
    echo "ERROR: server dir not found" >&2; exit 1
fi

NODE_BIN="/vol4/@appcenter/nodejs_v24/bin/node"
[ -x "${NODE_BIN}" ] || NODE_BIN="$(command -v node || echo /usr/bin/node)"
PORT="${TRIM_SERVICE_PORT:-20128}"   # manifest service_port
HOSTNAME="0.0.0.0"
cd "${SRC_DIR}"
DATA_DIR="${DATA_DIR}" PORT="${PORT}" HOSTNAME="${HOSTNAME}" \
    nohup "${NODE_BIN}" --max-old-space-size=4096 custom-server.js >> "${LOG}" 2>&1 &
```

- `DATA_DIR` env overrides the default data location (`~/.9router` for 9router) — point it at `$TRIM_PKGVAR` so data lands in `/vol4/@appdata/<AppName>/`.
- Health wait loop: `curl -sf "http://127.0.0.1:${PORT}/api/health"` (9router has `/api/health`; root `/` 307-redirects to `/login`).

## Verification BEFORE shipping the fpk (do both)

1. **Local run (dev machine):** `PORT=20128 HOSTNAME=127.0.0.1 DATA_DIR=/tmp/test node custom-server.js` → curl `/api/health` (expect `{"ok":true}`) and `/login` (200). This catches the missing-build-dir bug in seconds.
2. **NAS simulation:** extract `app.tgz` from the built fpk (`tar xzf <(tar xOf app.fpk app.tgz)`), run with the NAS node (`/vol4/@appcenter/nodejs_v24/bin/node --version` → v24 works) and the same env vars, curl health. Catches fpk packaging mistakes before the user installs.

## fnOS package facts (9router case)

- manifest: `service_port = 20128`, `ctl_stop = true`, `desktop_applaunchname = 9router.Application`
- Entry config: `type: "iframe"` works (unlike some Python web UIs) — 9router has no CORS issues.
- fpk size ~14MB compressed (node_modules/next is ~26MB unpacked) — acceptable.
- **MITM advanced features need root** (DNS rewrite, root CA install on 443). fnOS apps run as `package` user → MITM/anti-detect features may be limited; core routing, RTK token saving, quota tracking work fine. Mention this in the install notes.
