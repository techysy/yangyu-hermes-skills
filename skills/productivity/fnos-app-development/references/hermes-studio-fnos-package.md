# Hermes Studio fnOS Package Reference

Status: **EXPERIMENTAL / BLOCKED** — Hermes Studio (npm: `hermes-web-ui`) requires a local Hermes Agent binary. It is NOT a thin client.

## Key Blockers

| Issue | Detail | Workaround |
|-------|--------|-----------|
| Startup crash | `spawn('hermes', ['gateway', 'run', '--replace'])` at startup — crashes with `ENOENT` if hermes not in PATH | None (hard crash, not a warning) |
| node-pty compilation | npm install triggers node-gyp for `node-pty`. Fails on fnOS without build-essential. | `--ignore-scripts` (disables web-terminal feature only) |
| Thin client not supported | All disable flags (`DISABLE_GATEWAY_AUTOSTART`, `MANAGED_GATEWAY=0`) are ignored at startup | HERMES Studio always checks for local Hermes |
| Agent bridge required | Chat runs through local agent bridge, not directly proxied to remote Gateway | Cannot work without local hermes binary |

## Architecture (How it SHOULD work vs HOW IT ACTUALLY WORKS)

**Designed architecture:**
```
Browser → Hermes Studio (Node, :8648) → agent bridge → Hermes Agent (local/gateway)
```

**Actual behavior at startup:**
```javascript
// src/server.js (simplified)
const cp = require('child_process');
cp.spawn('hermes', ['gateway', 'run', '--replace']);  // CRASHES if not found
```

Even with `HERMES_WEB_UI_DISABLE_GATEWAY_AUTOSTART=1` and `HERMES_WEB_UI_MANAGED_GATEWAY=0`, the startup code still calls `spawn('hermes', ...)` before checking the disable flags. This is a hard dependency.

## Comparison with hermes-webui (Python)

| Feature | hermes-webui ✅ | Hermes Studio ❌ |
|---------|----------------|-----------------|
| Remote Gateway chat | `HERMES_WEBUI_CHAT_BACKEND=gateway` | Requires local hermes binary |
| No local Agent needed | ✅ `HERMES_WEBUI_DISABLE_AGENT_CHECK=1` | ❌ Crashes on startup |
| Skills/Config from remote | ❌ (needs rsync or bundled) | N/A (crashes) |
| Node.js required | No (Python) | Yes |
| App size | 22MB (bundled source) | 47KB + npm install at setup |

## Repository

https://github.com/techysy/hermes-studio-fnos

## Build

```bash
cd HermesStudio/
fnpack build
# → HermesStudio.fpk
```

## Install on fnOS

1. **Node.js v24** must be installed from fnOS App Center first
2. App Center → Manual Install → select `HermesStudio.fpk`
3. Fill wizard: Gateway URL + API Key
4. App opens → crashes with `spawn hermes ENOENT`

## What Would Need to Change

To make Hermes Studio work as a thin client, the upstream project would need to:
1. Make `spawn('hermes', ...)` optional / gated behind the same disable flags
2. Add a pure-proxy mode where ALL agent communication goes through `GATEWAY_URL`
3. Remove the agent bridge dependency for remote-only deployments

Until those changes are made upstream, **hermes-webui (Python) is the correct choice for fnOS thin-client deployments**.
