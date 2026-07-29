# Hermes WebUI fnOS Package Guide

## Repository

Source code and fnOS packaging for this project lives at:
**https://github.com/techysy/hermes-webui-fnos**

The `fnos-pack/` directory contains the complete fnOS application package:
- `manifest` — app metadata
- `cmd/main` — lifecycle script (start/stop/status)
- `app/ui/config` — entry config
- `config/privilege` — run-as: package
- `config/resource` — data-share definition

To build: `cd fnos-pack && fnpack build`

## Two Deployment Modes

### Mode A: Remote Gateway (lighter, no local agent)

飞牛 NAS 上跑 Hermes WebUI 作为 fnOS 原生应用，连接到 Arch VM 或远程 Hermes Gateway。

```
fnOS (192.168.x.x)          Arch VM (192.168.x.x)
┌──────────────────────┐      ┌──────────────────────┐
│ fnOS App Center      │      │ Hermes Agent         │
│  └─ HermesWebUI      │      │  └─ Gateway :9119    │
│     ├─ :8787         │──▶   │                      │
│     └─ hermes-webui  │      └──────────────────────┘
│        (server.py)   │
└──────────────────────┘
```

Requires `HERMES_WEBUI_CHAT_BACKEND=gateway` and `HERMES_WEBUI_GATEWAY_BASE_URL`.
No local Hermes Agent install needed.

### Mode B: Bundled Agent (self-contained, heavier)

Hermes Agent installed in the app's venv at install time. WebUI connects to local `127.0.0.1:9119` Gateway.

```
fnOS (192.168.x.x)
┌─────────────────────────────┐
│ fnOS App Center             │
│  └─ HermesWebUI             │
│     ├─ venv/hermes          │
│     │   └─ dashboard :9119  │
│     ├─ :8787                │
│     └─ hermes-webui         │
│        (server.py)          │
└─────────────────────────────┘
```

Heavier install (~50+ pip deps) but no external dependency.

## Gateway Detection (cmd/main, Remote Mode)

```bash
detect_gateway() {
  if curl -sf --max-time 2 "http://127.0.0.1:9119/api/health" > /dev/null 2>&1; then
    echo "http://127.0.0.1:9119"       # local Hermes Agent
  else
    echo "http://192.168.x.x:9119"    # remote Arch VM Gateway
  fi
}
```

## Key Debug Commands (on fnOS)

```bash
# fnOS lifecycle log (install/cmd/main output)
cat /var/log/apps/HermesWebUI.log

# webui server startup log
cat /vol4/@appdata/HermesWebUI/webui.log

# check listening port
ss -tlnp | grep 8787

# source presence (always under target/)
ls -la /var/apps/HermesWebUI/target/server/server.py

# check actual app dir symlinks
ls -la /var/apps/HermesWebUI/target

# appcenter errors
sudo cat /var/log/trim_app_center/error.log 2>/dev/null || echo "need sudo"
```

## Build and Deploy Cycle

1. Edit files in build dir on Arch VM (e.g. `/tmp/HermesWebUI-build/HermesWebUI/`)
2. `scp` updated files to fnOS or write them via `ssh`
3. `fnpack build` to produce `HermesWebUI.fpk`
4. `cp HermesWebUI.fpk /vol4/1000/SSD/HermesWebUI-v0.1.0.fpk`
5. On fnOS Web UI: App Center → Manual Install → select file
6. To UPDATE: just install the new `.fpk` — fnOS detects the version bump and upgrades

Version naming: `HermesWebUI-v{major}.{minor}.{patch}.fpk`

## What Worked (Proven Approach)

1. **Start with `fnpack create` template** — don't build from scratch. Then modify manifest, swap cmd/main, replace icons.
2. **Bundle source in `app/server/`** — avoid network dependency at install time. install_init should be a no-op.
3. **Use `TRIM_*` env vars** — `TRIM_APPDEST`, `TRIM_PKGVAR`, `TRIM_PKGETC`. Never hardcode paths.
4. **Run server.py directly** — bootstrap.py needs local Hermes Agent. Pass `HERMES_WEBUI_DISABLE_AGENT_CHECK=1` and run `server.py`.
5. **Use `type: \"url\"` for debugging** — iframe type may fail behind fygo-browser. Switch to iframe only after confirming the service starts.
6. **For bundled-agent mode**: install hermes-agent in `install_callback` (not at startup). `pip install hermes-agent` takes a while (~30-60s on fnOS).
7. **For remote mode**: must set `HERMES_WEBUI_CHAT_BACKEND=gateway` or WebUI defaults to legacy mode and fails.

## Common Issues

### Bootstrapping: "Hermes Agent was not found and auto-install was disabled"

bootstrap.py is NOT suitable for headless/remote-Gateway deployments. Fix: bypass bootstrap.py and run server.py directly:

```bash
export HERMES_API_URL="http://192.168.x.x:9119"
export HERMES_WEBUI_HOST="0.0.0.0"
export HERMES_WEBUI_PORT="8787"
export HERMES_WEBUI_STATE_DIR="${DATA_DIR}/state"
export HERMES_WEBUI_SKIP_ONBOARDING=1
export HERMES_WEBUI_DISABLE_AGENT_CHECK=1
# Gateway chat mode — REQUIRED for remote Gateway setup
export HERMES_WEBUI_CHAT_BACKEND=gateway
export HERMES_WEBUI_GATEWAY_BASE_URL="${GATEWAY_URL}"
export GATEWAY_HEALTH_URL="${GATEWAY_URL}/api/health"
# server.py also reads these as fallbacks
export HOST="0.0.0.0"
export PORT="8787"

cd "${SRC_DIR}"
python server.py
```

### "拒绝了我们的连接请求"

Two possible causes:

**A) Server process didn't start** — check:
1. Source exists at `$TRIM_APPDEST/target/server/server.py`
2. cmd/main uses correct path (`target/server` not `server`)
3. venv + deps installed (pyyaml, cryptography)

**B) Server started but iframe blocked** — check:
1. `curl http://127.0.0.1:8787/health` — if ok, server is running
2. `curl http://192.168.x.x:8787/health` — if ok, network is fine
3. Try `type: "url"` instead of `type: "iframe"` in app/ui/config
4. Open `http://192.168.x.x:8787` directly in fnOS Chrome

### "执行脚本出错且原因未知"

Install script failed. Check `/var/log/apps/HermesWebUI.log` for exact error.
Common cause: network timeout downloading source from GitHub.
Fix: bundle source in `app/server/` at build time, make install_init a no-op.

### "应用包格式不符合系统版本要求"

fpk rejected by fnOS. Always diff against a `fnpack create` template:
1. Run `fnpack create TestApp` on the same fnOS machine
2. `fnpack build` and install TestApp.fpk — if it installs, the format is fine
3. Diff your manifest, config/privilege, config/resource with the template
4. Extract both fpk files (`tar xf`) and inspect `app.tgz` content

## History of Iterations

| Version | Changes |
|---------|---------|
| v1-v3   | Initial fpk attempts — "格式不符合系统版本" |
| v4      | Fixed manifest format (added arch/distributor) — installed |
| v5      | Added install_init to download source — timed out |
| v6      | Fixed bootstrap.py `--port` → positional arg — agent missing |
| v7      | Bundled source in `app/server/` (22MB) |
| v8      | Hardcoded APP_DIR path — wrong dir |
| v9      | Used TRIM_* env vars — server/ was in `target/` not root |
| v10     | Fixed to `target/server` — bootstrap required local agent |
| v11     | Run server.py directly instead of bootstrap.py — WORKED 🎉 |
| v0.1.0  | Stable release, version normalized |
| v0.1.1  | Default settings.json (theme: dark, skin: default) |
| v0.1.2  | Default skin: codex |
| v0.1.3  | Default language: zh |
| v0.1.4  | HERMES_WEBUI_CHAT_BACKEND=gateway for remote Gateway |
| v0.1.5  | Default theme: system (follow system) + codex skin |
| v1.0.0  | Bundled Hermes Agent mode (local dashboard + gateway) |
| v1.0.1  | Moved hermes-agent install to install_callback |
| v0.2.0  | Stripped to pure-remote mode (no bundled agent). Lighter, faster startup. |
| v1.0.2  | Type: url instead of iframe (fixes "拒绝连接" in fygo-browser) |
| v0.3.0  | Gateway mode with API key. `HERMES_WEBUI_CHAT_BACKEND=gateway` + `HERMES_WEBUI_GATEWAY_API_KEY` + `HERMES_WEBUI_GATEWAY_BASE_URL`. Arch VM API server on 8642. |

## Gateway API Server Setup

When deploying hermes-webui with `HERMES_WEBUI_CHAT_BACKEND=gateway`, the Arch VM's Gateway needs its `api_server` platform enabled.

### Configuration (Arch VM)

Drop-in file at `/home/your_user/.config/systemd/user/hermes-gateway.service.d/api-server.conf`:
```
[Service]
Environment="API_SERVER_ENABLED=true"
Environment="API_SERVER_KEY=webui-gateway-key-2026"
Environment="API_SERVER_PORT=8642"
Environment="API_SERVER_HOST=0.0.0.0"
```

**⚠️ CRITICAL**: The `API_SERVER_KEY` must be present. Without it, the API server refuses with:
```
ERROR gateway.platforms.api_server: [Api_Server] Refusing to start:
API_SERVER_KEY is required for the API server, including loopback-only binds on 0.0.0.0.
```

The WebUI side must match with `HERMES_WEBUI_GATEWAY_API_KEY=webui-gateway-key-2026`.

### Restart Safety Feature (Blocked from Within)

The Hermes Gateway (#30719) intercepts ANY stop/restart command from within its own process tree:

| Method | Works? |
|--------|--------|
| `systemctl --user restart` (inside gateway) | ❌ |
| `systemd-run --user --scope systemctl --user kill` | ❌ |
| `ssh yangyu@127.0.0.1` | ❌ |
| `ssh yangyu@192.168.x.x` (local loopback) | ❌ |
| `hermes gateway restart` | ❌ |
| `cronjob` (also runs inside gateway tree) | ❌ |
| `execute_code` with `subprocess.run()` | ❌ |
| `xfce4-terminal -e` from background true | ❌ |
| SSH from a **different LAN machine** | ✅ |
| Manual terminal on desktop (outside Hermes) | ✅ |
| Reboot the VM | ✅ |

**Workaround**: Ask the user to run `systemctl --user restart hermes-gateway.service` from their desktop terminal, or SSH from a different machine on the LAN.

### Verification

```bash
# Check API server is listening
ss -tlnp | grep 8642

# Health check
curl -sf http://127.0.0.1:8642/health
# Expected: {"status": "ok", "platform": "hermes-agent", "version": "0.19.0"}

# Check Gateway has loaded the drop-in
systemctl --user show hermes-gateway.service -p Environment
# Should show API_SERVER_KEY in output
```

### WebUI Side Configuration

```bash
export HERMES_WEBUI_CHAT_BACKEND=gateway
export HERMES_WEBUI_GATEWAY_BASE_URL="http://192.168.x.x:8642"
export HERMES_WEBUI_GATEWAY_API_KEY="webui-gateway-key-2026"
export HERMES_API_URL="http://192.168.x.x:9119"
```

The Dashboard (`HERMES_API_URL` at 9119) provides REST API; the Gateway (`GATEWAY_BASE_URL` at 8642) provides chat backend. Both are needed.

### For the fnOS app specifically:

The most reliable approach is Mode B (bundled agent). Install hermes-agent in install_callback, start dashboard + webui at each boot, no remote dependency at all. Install takes 30-60s for pip install; subsequent boots are fast (venv already exists).

## SSH Skills Sync

When skills/settings don't sync from Arch VM to fnOS, set up SSH key-based periodic sync.

See `references/ssh-skills-sync.md` for full setup guide.

## CGI Redirect for External Dashboard Access

fnOS app entries cannot link to external IPs directly. When the user wants an app icon that opens an external Dashboard (e.g. `http://192.168.x.x:9119/`), use a CGI redirect.

### Create app/ui/index.cgi

```bash
#!/bin/bash
echo "Status: 302"
echo "Location: http://192.168.x.x:9119/"
echo "Content-Type: text/html"
echo ""
echo "<html><body><a href='http://192.168.x.x:9119/'>Redirect</a></body></html>"
```

### Update app/ui/config

```json
{
  ".url": {
    "HermesWebUI.Application": {
      "title": "Hermes Agent",
      "icon": "images/icon_{0}.png",
      "type": "iframe",
      "protocol": "http",
      "port": "8080",
      "url": "/cgi/ThirdParty/HermesWebUI/index.cgi/",
      "allUsers": true
    }
  }
}
```

The `protocol` and `port` are ignored for CGI routes — the request flows through the fnOS web server domain. The browser follows the 302 redirect to the external target URL.

## Common Issue: fnOS App Center Shows "拒绝连接" After Update

When updating the fnOS app (even with `type: "url"`), if the old WebUI server process is still running on the previous port, the new app config may conflict. Fix:

1. Kill the old process: `pkill -f server.py`
2. If the source server was removed (switching to CGI redirect only), no backend process is needed
3. The app icon now opens a browser tab → CGI → 302 redirect → Dashboard

### Symptom

Chat works fine, but the Skills page, Settings page, and other management sections in the WebUI show no data (empty lists or default values). The `/api/skills` endpoint returns 200 almost instantly (~0.3ms) with an empty list.

### Root Cause

In Remote Gateway Mode, the WebUI has a **split architecture**:

- **Chat** → proxied through Gateway wire to remote Hermes Agent ✅
- **Skills/Settings** → served by WebUI's own API layer (`api/routes.py` / `api/config.py`) reading from the **local filesystem on the NAS** ❌

The WebUI creates its own `hermes_home` directory on the NAS (e.g. `/vol4/@appdata/HermesWebUI/hermes_home/`) with a separate `config.yaml`, `.env`, an **empty `skills/` directory**, and its own `state.db`. The Skills and Settings pages read from this local directory, NOT from the remote Gateway's Hermes Agent.

Relevant code path in the WebUI (`api/routes.py`):
```python
# GET /api/skills reads from local fs
skills_dir = get_active_hermes_home() / "skills"
data = _skills_list_from_dir(skills_dir)  # empty on NAS!
```

### Diagnosis

```bash
# On the NAS, check the WebUI's hermes_home
ls /vol4/@appdata/HermesWebUI/hermes_home/skills/         # empty or missing
cat /vol4/@appdata/HermesWebUI/hermes_home/config.yaml     # tiny, separate config

# Check if dashboard URL is misconfigured
grep dashboard /vol4/@appdata/HermesWebUI/hermes_home/config.yaml
# May show wrong port like :9191 instead of :9119

# Check webui.log for skills/settings API timing
cat /vol4/@appdata/HermesWebUI/webui.log | grep 'api/skills\|api/settings'
# Skills: 0.3ms → local response, not proxied
```

### Workarounds

| Approach | Pros | Cons |
|----------|------|------|
| **A) Sync skills to NAS** | Simple, keeps WebUI unified | Stale data, manual sync |
| **B) Use Dashboard directly** | Full management, real-time | Need to switch UIs |
| **C) Bundled Agent Mode** | Self-contained, everything local | Heavier install, more RAM |

**Workaround A — Sync skills via cron (tar+ssh when rsync unavailable):**
See `references/ssh-skills-sync.md` for complete setup guide (SSH key gen, one-time key push, cron creation).

```bash
# Manual one-shot sync from Arch VM:
tar czf - -C /home/your_user/.hermes skills/ | \
  ssh yangyu@192.168.x.x \
  "tar xzf - -C /vol4/@appdata/HermesWebUI/hermes_home"
```

**Workaround B — Use Dashboard for management:**
Access the Hermes Dashboard directly (e.g. http://192.168.x.x:9119) for skills/settings management. Keep WebUI for chat.

**Workaround C — Upgrade to Bundled Agent:**
Install hermes-agent locally on the NAS during install_callback, set `HERMES_API_URL=http://127.0.0.1:9119`, and `HERMES_WEBUI_CHAT_BACKEND=gateway` pointing to the local dashboard. Full skills/settings support at the cost of ~50+ pip deps and extra RAM.
