# HermesWebUI fnOS Package Reference

## Package History

- **v0.1.0-v0.3.0**: Remote Gateway mode only (nesquena/hermes-webui)
- **v0.4.0-v1.1.0**: Hybrid mode (local + remote kernel)
- **v1.2.0-v1.3.0**: Fixed proxy and Gateway settings

## Key Learnings

### Proxy Environment Variables Break Local Communication

**Problem**: Setting `no_proxy="localhost,127.0.0.1,192.168.31.*"` doesn't work with Python's `requests` library. The wildcard `*` is not supported. Requests to `192.168.31.31:8642` get sent through the proxy, causing 501 errors or wrong HTTP method concatenation.

**Root cause**: Python's `requests` library uses `urllib3` which doesn't support shell-style wildcards in `no_proxy`.

**Fix**: Either:
1. `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy` before starting the WebUI (for local-network-only use)
2. Use explicit IPs: `export no_proxy="localhost,127.0.0.1,192.168.31.101,192.168.31.31"`

### cmd/main Must Be Finalized Before Building fpk

After `fnpack build` and installation, `/var/apps/{appname}/cmd/` directory and files are owned by **root**. You cannot modify cmd/main from the yangyu user without sudo.

**Implication**: All cmd/main logic must be finalized BEFORE building the fpk. If you need to change cmd/main after install, ask the user to manually run:
```bash
cat /tmp/main_new.sh | sudo tee /var/apps/{appname}/cmd/main > /dev/null
sudo chmod 755 /var/apps/{appname}/cmd/main
```

### WebUI Doesn't Read .env Files

hermes-webui's `server.py` reads from **process environment variables only** — it does NOT use `python-dotenv` or read `.env` files. Creating a `.env` file in the project directory or HERMES_HOME won't work. All settings must be passed via `export` in `cmd/main` before starting the server.

### Gateway API Server vs Dashboard

These are separate services:
- **Gateway API server** (port 8642): Exposes OpenAI-compatible endpoints for chat
- **Dashboard** (port 9119): Serves the management UI

WebUI needs BOTH for full functionality. Enable Gateway API via env vars in systemd drop-in:
```
API_SERVER_ENABLED=true
API_SERVER_KEY=<key>
API_SERVER_PORT=8642
API_SERVER_HOST=0.0.0.0
```

### Skills Sync from Remote

When rsync isn't available, use `tar` over SSH:
```bash
tar czf - -C /home/yangyu/.hermes skills/ | ssh yangyu@192.168.31.101 "tar xzf - -C /vol4/@appdata/HermesWebUI/hermes_home"
```

Set up a cron job to run this every 5 minutes for automatic sync.

## cmd/main Template (v1.3.0)

```bash
#!/bin/bash
set -euo pipefail
APP_NAME="${TRIM_APPNAME:-HermesWebUI}"
APP_DIR="${TRIM_APPDEST:-/var/apps/${APP_NAME}}"
DATA_DIR="${TRIM_PKGVAR:-${APP_DIR}/var}"
WEBUI_PORT=8787
WEBUI_SRC="${APP_DIR}/target/server"
WEBUI_LOG="${DATA_DIR}/webui.log"
WEBUI_PID="${DATA_DIR}/webui.pid"
WEBUI_VENV="${DATA_DIR}/venv"
WEBUI_STATE="${DATA_DIR}/state"
HERMES_HOME="${DATA_DIR}/hermes_home"

# Read config from gateway.env
CONFIG_FILE="${DATA_DIR}/gateway.env"
[ -f "${CONFIG_FILE}" ] && source "${CONFIG_FILE}"
REMOTE_GATEWAY="${GATEWAY_URL:-http://192.168.31.31:8642}"
REMOTE_DASHBOARD="${DASHBOARD_URL:-http://192.168.31.31:9119}"
REMOTE_KEY="${GATEWAY_KEY:-webui-gateway-key-2026}"
USE_PROXY_FLAG="${USE_PROXY:-true}"
PROXY_URL="${PROXY_URL:-http://192.168.31.31:7890}"

mkdir -p "${DATA_DIR}" "${WEBUI_STATE}" "${HERMES_HOME}"
[ ! -f "${WEBUI_STATE}/settings.json" ] && echo '{"theme":"light","skin":"codex","language":"zh"}' > "${WEBUI_STATE}/settings.json"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "${WEBUI_LOG}"; }

ensure_venv() {
  [ -f "${WEBUI_VENV}/bin/python" ] && return 0
  /usr/bin/python3 -m venv "${WEBUI_VENV}"
  "${WEBUI_VENV}/bin/pip" install pyyaml cryptography >> "${WEBUI_LOG}" 2>&1
}

start_webui() {
  [ -f "${WEBUI_PID}" ] && kill -0 "$(cat "${WEBUI_PID}")" 2>/dev/null && return 0
  ensure_venv
  [ ! -f "${WEBUI_SRC}/server.py" ] && log "ERROR: source missing" && return 1

  # Unset proxy for local network communication
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy

  export HERMES_HOME="${HERMES_HOME}"
  export HERMES_API_URL="${REMOTE_DASHBOARD}"
  export HERMES_WEBUI_CHAT_BACKEND=gateway
  export HERMES_WEBUI_GATEWAY_BASE_URL="${REMOTE_GATEWAY}"
  export HERMES_WEBUI_GATEWAY_API_KEY="${REMOTE_KEY}"
  export HERMES_WEBUI_HOST="0.0.0.0"
  export HERMES_WEBUI_PORT="${WEBUI_PORT}"
  export HERMES_WEBUI_STATE_DIR="${WEBUI_STATE}"
  export HERMES_WEBUI_SKIP_ONBOARDING=1
  export HERMES_WEBUI_DISABLE_AGENT_CHECK=1
  export HOST="0.0.0.0"
  export PORT="${WEBUI_PORT}"

  cd "${WEBUI_SRC}"
  nohup "${WEBUI_VENV}/bin/python" server.py >> "${WEBUI_LOG}" 2>&1 &
  echo $! > "${WEBUI_PID}"

  for i in $(seq 1 30); do
    curl -sf "http://127.0.0.1:${WEBUI_PORT}/health" >/dev/null 2>&1 && log "WebUI started (PID $(cat ${WEBUI_PID}))" && return 0
    sleep 1
  done
  log "WebUI start timeout"
}

stop() {
  [ -f "${WEBUI_PID}" ] || return 0
  PID=$(cat "${WEBUI_PID}")
  kill "${PID}" 2>/dev/null || true
  for i in 1 2 3; do kill -0 "${PID}" 2>/dev/null || { rm -f "${WEBUI_PID}"; log "Stopped"; return 0; }; sleep 1; done
  kill -9 "${PID}" 2>/dev/null || true
  rm -f "${WEBUI_PID}"
  log "Force stopped"
}

status() {
  [ -f "${WEBUI_PID}" ] && kill -0 "$(cat "${WEBUI_PID}")" 2>/dev/null && echo "running" || echo "stopped"
}

case "${1:-start}" in
  start) start_webui ;;
  stop) stop ;;
  status) status ;;
  restart) stop; sleep 2; start_webui ;;
  *) echo "Usage: $0 {start|stop|status|restart}"; exit 1 ;;
esac
```

## Hermes Agent on fnOS (trim.hermes)

The official Hermes Agent app on fnOS uses a two-process architecture:

### Wrapper (Go binary)
- **Location**: `/var/apps/trim.hermes/wrapper/trim-hermes-wrapper`
- **Listens on**: Unix socket (`/var/apps/trim.hermes/run/trim-hermes.sock`)
- **Purpose**: Manages the Python runtime lifecycle
- **Process name**: `trim-hermes-wrapper`

### Python Dashboard
- **Location**: `/vol4/@appcenter/trim.hermes/runtime/python/bin/hermes`
- **Listens on**: TCP port `19119` (configurable via `TRIM_HERMES_DASHBOARD_PORT`)
- **Start command**: `hermes dashboard --host 127.0.0.1 --port 19119 --no-open`
- **Process name**: `python3.11.real -m hermes_cli.main`

### Key Differences from Standard Hermes
1. The wrapper does NOT automatically start the Python dashboard
2. The wrapper listens on a Unix socket, not TCP
3. The dashboard must be started separately after the wrapper is running
4. The wrapper may appear to be running (PID exists) but the dashboard isn't listening

### How to Start the Dashboard Manually

```bash
# From the Hermes Agent data directory
cd /vol4/@appdata/trim.hermes
export HOME=/vol4/@appdata/trim.hermes/home
export HERMES_HOME=/vol4/@appdata/trim.hermes/hermes
/vol4/@appcenter/trim.hermes/runtime/python/bin/hermes dashboard --host 127.0.0.1 --port 19119 --no-open
```

### Configuration Files

- **PID file**: `/vol4/@appdata/trim.hermes/trim.hermes.pid`
- **Log file**: `/vol4/@appdata/trim.hermes/trim.hermes.log`
- **Config**: `/vol4/@appdata/trim.hermes/hermes/config.yaml` (created on first dashboard start)
- **State**: `/vol4/@appdata/trim.hermes/hermes/state.db`

### Connecting WebUI to Local Hermes Agent

When using HermesWebUI with the local Hermes Agent:

```bash
# gateway.env
USE_REMOTE_GATEWAY="false"
DASHBOARD_URL="http://127.0.0.1:19119"
GATEWAY_URL="http://127.0.0.1:19119"
GATEWAY_KEY=""
USE_PROXY="false"
PROXY_URL=""
```

### Common Issues

1. **Wrapper running but no port listening**: The wrapper starts but doesn't automatically spawn the Python dashboard. Need to start dashboard manually or configure the wrapper to do so.

2. **PID file exists but process is dead**: The wrapper may crash without cleaning up the PID file. Check with `ps -p <PID>` and remove stale PID files.

3. **Dashboard returns 401 Unauthorized**: The dashboard needs authentication. For local use, this is usually handled by the wrapper's Unix socket communication.

4. **Port conflict**: If another service is using port 19119, the dashboard won't start. Check with `ss -tlnp | grep 19119`.
