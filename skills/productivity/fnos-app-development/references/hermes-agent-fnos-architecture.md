# Hermes Agent on fnOS Architecture

## Official Hermes Agent App (trim.hermes)

The official Hermes Agent app on fnOS uses a **two-process architecture**:

### Wrapper (Go binary)
- **Location**: `/var/apps/trim.hermes/wrapper/trim-hermes-wrapper`
- **Listens on**: Unix socket (`/var/apps/trim.hermes/run/trim-hermes.sock`)
- **Purpose**: Manages the Python runtime lifecycle
- **Process name**: `trim-hermes-wrapper`
- **PID file**: `/vol4/@appdata/trim.hermes/trim.hermes.pid`

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

## Debugging Commands

```bash
# Check if wrapper is running
ps aux | grep trim-hermes-wrapper

# Check if dashboard is listening
ss -tlnp | grep 19119

# Check wrapper logs
cat /vol4/@appdata/trim.hermes/trim.hermes.log

# Check dashboard health
curl -sf http://127.0.0.1:19119/api/health

# Check PID file
cat /vol4/@appdata/trim.hermes/trim.hermes.pid

# Check if PID is alive
PID=$(cat /vol4/@appdata/trim.hermes/trim.hermes.pid)
ps -p $PID
```
