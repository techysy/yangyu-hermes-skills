# Gateway API Server Setup (Arch VM)

Enable the Hermes Gateway's built-in HTTP API server so thin clients (WebUI, Hermes Studio) can route chat through it remotely.

## Required Environment Variables

The Gateway reads these from the **daemon's process environment** (not from config.yaml directly, though `hermes config set` bridges them):

| Variable | Value | Purpose |
|----------|-------|---------|
| `API_SERVER_ENABLED` | `true` | Enable the OpenAI-compatible HTTP endpoint |
| `API_SERVER_KEY` | `<random-string>` | Bearer token — **required**, even for loopback binds |
| `API_SERVER_PORT` | `8642` | Listen port (must match `HERMES_WEBUI_GATEWAY_BASE_URL`) |
| `API_SERVER_HOST` | `0.0.0.0` | Bind address |

## systemd Drop-In (recommended for persistence)

```bash
# /home/yangyu/.config/systemd/user/hermes-gateway.service.d/api-server.conf
[Service]
Environment="API_SERVER_ENABLED=true"
Environment="API_SERVER_KEY=webui-gateway-key-2026"
Environment="API_SERVER_PORT=8642"
Environment="API_SERVER_HOST=0.0.0.0"
```

After writing the file:
```bash
systemctl --user daemon-reload
systemctl --user restart hermes-gateway.service
```

## Verification

```bash
# Check API server is listening
ss -tlnp | grep 8642

# Test health endpoint
curl -sf http://127.0.0.1:8642/health
# → {"status": "ok", "platform": "hermes-agent", "version": "0.19.0"}

# Test skills endpoint (proxies from Gateway)
curl -sf -H "Authorization: Bearer webui-gateway-key-2026" \
  http://127.0.0.1:8642/v1/models
# → {"object": "list", "data": [{"id": "hermes-agent", ...}]}
```

## Known Issues

### Gateway API server adapter fails to load on native fnOS install (v0.19.0)

**Symptom**: After installing hermes-agent via pip on fnOS and starting `hermes gateway run --force`:
- Gateway runs (PID exists, systemd service active)
- `ss -tlnp | grep 18642` shows **nothing** — no port listening
- Log shows: `WARNING gateway.run: API Server: aiohttp not installed` + `No adapter available for api_server`
- `curl http://127.0.0.1:18642/api/status` returns nothing
- `aiohttp` IS installed and importable: `python -c "import aiohttp; print(aiohttp.__version__)"` → `3.14.3`

**Root cause**: The Gateway's api_server adapter loading mechanism fails silently on fnOS native installs. The aiohttp module is installed but the adapter check doesn't find it (possibly a sub-dependency or version check issue in hermes-cli internals).

**Impact**: Without the API server, hermes-webui cannot use local Gateway mode on fnOS — only remote Gateway (Arch VM) works.

**Workarounds**:
1. **Use remote Gateway mode** — point hermes-webui to Arch VM's Gateway API at port 8642 (reliable, tested)
2. **Wait for hermes-agent fix** — the adapter loading is a hermes-cli bug
3. **Try `hermes serve`** — provides a backend server on a port, but serves Dashboard SPA (HTML) at all endpoints, NOT OpenAI-compatible API. `/v1/chat/completions` returns 405 Method Not Allowed

**Test**: After starting Gateway, always verify API server:
```bash
curl -sf http://127.0.0.1:18642/api/status 2>&1 | head -3
# If returns JSON → API server works
# If returns HTML or empty → adapter failed to load
```

### Cannot restart from within gateway process tree

**Symptom**: All `systemctl --user restart/stop hermes-gateway.service` commands fail with:
```
Blocked: cannot restart or stop the gateway from inside the gateway process
```

**Workarounds** (pick one):
1. SSH from another LAN machine
2. Reboot the VM
3. `kill -9 <PID>` then immediately `systemctl --user stop` before systemd auto-restarts it (race window ~2-5s)

### Gateway API only exposes `hermes-agent` model

The Gateway abstracts the provider config. Chat requests to `hermes-agent` are forwarded to whichever model the Gateway's config.yaml specifies.

## Proxy Settings for fnOS App

When HermesWebUI runs on fnOS and needs to access external APIs, configure proxy via the app settings page.

### wizard/config (fnOS app settings)

```json
[
  {
    "stepTitle": "Gateway 连接配置",
    "items": [
      {"type": "text", "field": "gateway_url", "label": "Gateway 地址", "initValue": "http://192.168.31.31:8642"},
      {"type": "text", "field": "gateway_key", "label": "API Key", "initValue": "webui-gateway-key-2026"},
      {"type": "text", "field": "dashboard_url", "label": "Dashboard 地址", "initValue": "http://192.168.31.31:9119"},
      {"type": "text", "field": "use_remote_gateway", "label": "远程Gateway (true/false)", "initValue": "true"}
    ]
  },
  {
    "stepTitle": "代理设置",
    "items": [
      {"type": "text", "field": "use_proxy", "label": "代理开关 (true/false)", "initValue": "true"},
      {"type": "text", "field": "proxy_url", "label": "代理地址", "initValue": "http://192.168.31.31:7890"}
    ]
  }
]
```

### config_callback (save settings to env file)

```bash
#!/bin/bash
APP_NAME="${TRIM_APPNAME:-HermesWebUI}"
DATA_DIR="${TRIM_PKGVAR:-/vol4/@appdata/${APP_NAME}}"
mkdir -p "${DATA_DIR}"
cat > "${DATA_DIR}/gateway.env" <<-EOF
USE_REMOTE_GATEWAY="${use_remote_gateway:-true}"
DASHBOARD_URL="${dashboard_url:-http://192.168.31.31:9119}"
GATEWAY_URL="${gateway_url:-http://192.168.31.31:8642}"
GATEWAY_KEY="${gateway_key:-webui-gateway-key-2026}"
USE_PROXY="${use_proxy:-true}"
PROXY_URL="${proxy_url:-http://192.168.31.31:7890}"
EOF
exit 0
```

### cmd/main (read config + apply proxy)

```bash
CONFIG_FILE="${DATA_DIR}/gateway.env"
[ -f "${CONFIG_FILE}" ] && source "${CONFIG_FILE}"

USE_PROXY_FLAG="${USE_PROXY:-true}"
PROXY_URL="${PROXY_URL:-http://192.168.31.31:7890}"

if [ "${USE_PROXY_FLAG}" = "true" ] && [ -n "${PROXY_URL}" ]; then
  export http_proxy="${PROXY_URL}"
  export https_proxy="${PROXY_URL}"
  export HTTP_PROXY="${PROXY_URL}"
  export HTTPS_PROXY="${PROXY_URL}"
  export no_proxy="localhost,127.0.0.1,192.168.31.*"
  log "Proxy enabled: ${PROXY_URL}"
fi
```

## Hybrid Mode (Local + Remote Fallback)

The most robust fnOS app pattern:

```bash
start_webui() {
  # Prefer local kernel if available
  if [ -f "${WEBUI_VENV}/bin/hermes" ]; then
    start_local_kernel && return 0
  fi
  # Fall back to remote Gateway
  export HERMES_API_URL="${REMOTE_DASHBOARD_URL}"
  start_remote_fallback
}
```

Local kernel:
```bash
nohup "${WEBUI_VENV}/bin/hermes" dashboard --host 127.0.0.1 --port 9119 --no-open &
echo $! > "${DATA_DIR}/dashboard.pid"
```

Remote fallback:
```bash
export HERMES_WEBUI_CHAT_BACKEND=gateway
export HERMES_WEBUI_GATEWAY_BASE_URL="${REMOTE_GATEWAY_URL}"
export HERMES_API_URL="${REMOTE_DASHBOARD_URL}"
```

## Skills Sync from Remote

When rsync unavailable, use tar+ssh:
```bash
tar czf - -C /home/yangyu/.hermes skills/ | \
  ssh yangyu@192.168.31.101 \
  "tar xzf - -C /vol4/@appdata/HermesWebUI/hermes_home"
```

Set up cron: `cronjob action=create no_agent=true script="..." schedule="every 5m"`
