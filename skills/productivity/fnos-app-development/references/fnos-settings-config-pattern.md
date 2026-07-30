# fnOS App Settings Page (wizard/config + config_callback) Pattern

## Overview

Make an fnOS app's configuration editable via App Center → 应用设置. Users fill in fields, save, and the values persist to a config file that cmd/main reads on startup.

## Files Needed

```
myapp/
├── wizard/
│   └── config              # Settings form definition (JSON)
├── cmd/
│   ├── config_callback     # Saves settings when user clicks "保存"
│   └── main                # Reads config file on startup
└── config/
    └── resource            # Must have data-share for write access
```

## wizard/config

Same JSON format as `wizard/install`. Fields appear in the fnOS settings page.

```json
[
  {
    "stepTitle": "连接配置",
    "items": [
      {
        "type": "text",
        "field": "gateway_url",
        "label": "Gateway 地址",
        "placeholder": "http://192.168.31.31:8642",
        "initValue": "http://192.168.31.31:8642",
        "desc": "远程 Gateway API 地址",
        "rules": [{"required": true, "message": "必填"}]
      },
      {
        "type": "text",
        "field": "gateway_key",
        "label": "API Key",
        "initValue": "webui-gateway-key-2026",
        "rules": [{"required": true, "message": "必填"}]
      }
    ]
  }
]
```

## config_callback

Runs when the user saves settings. Wizard field values are available as **bare env vars** (no `wizard_` prefix, unlike install wizard).

```bash
#!/bin/bash
APP_NAME="${TRIM_APPNAME:-MyApp}"
DATA_DIR="${TRIM_PKGVAR:-/vol4/@appdata/${APP_NAME}}"
mkdir -p "${DATA_DIR}"

cat > "${DATA_DIR}/gateway.env" <<-EOF
GATEWAY_URL="${gateway_url:-http://192.168.31.31:8642}"
GATEWAY_KEY="${gateway_key:-webui-gateway-key-2026}"
DASHBOARD_URL="${dashboard_url:-http://192.168.31.31:9119}"
EOF

echo "Config saved to ${DATA_DIR}/gateway.env"
exit 0
```

## cmd/main reads config

```bash
DATA_DIR="${TRIM_PKGVAR:-/vol4/@appdata/${APP_NAME}}"
CONFIG_FILE="${DATA_DIR}/gateway.env"
[ -f "${CONFIG_FILE}" ] && source "${CONFIG_FILE}"

# Use configured values with defaults
GATEWAY_URL="${DASHBOARD_URL:-http://192.168.31.31:9119}"
GATEWAY_API="${GATEWAY_URL:-http://192.168.31.31:8642}"
GATEWAY_KEY="${GATEWAY_KEY:-webui-gateway-key-2026}"
```

## Limitations

- **Config change does NOT restart the app**: fnOS only runs `config_callback`. The running service keeps the old config until manually restarted. Best practice: add a note in the wizard title/description.
- **No validation feedback**: The wizard can validate required fields, but complex validation (URL format, network reachability) is not supported.
- **CRITICAL: env vars differ between install and config wizards**: `wizard/install` → `wizard_<field>` prefix. `wizard/config` → bare `<field>` name. This is a fnOS quirk — always test both paths.

## Related

- Reference: `fnos-app-development` skill SKILL.md → "App Settings Page" section
- Official docs: https://developer.fnnas.com/docs/core-concepts/wizard
