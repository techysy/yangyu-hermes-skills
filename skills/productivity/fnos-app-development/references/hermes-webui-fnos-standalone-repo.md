# HermesWebUI fnOS Standalone Repo Reference

## Why Standalone (Not Fork)

When wrapping an upstream project as an fnOS app, create a **separate repo** — do NOT fork the upstream.

**Problems with forking:**
- Forks get cluttered with upstream commits
- The fnOS package only needs packaging files (manifest, cmd/, config/, wizard/, icons)
- The actual source is installed at runtime via npm/pip
- Maintaining a fork adds merge burden for upstream updates

**Reference repo**: https://github.com/techysy/hermes-webui-fnos

## Repo Structure

```
hermes-webui-fnos/
├── manifest              # App metadata (depends on nodejs_v24)
├── ICON.PNG              # 64x64 package icon
├── ICON_256.PNG          # 256x256 package icon
├── app/ui/
│   ├── config            # Entry config (type: "url", port 8787)
│   └── images/           # Entry icons (icon_64/128/256.png)
├── cmd/
│   ├── main              # start/stop/status with Gateway connection
│   ├── install_init      # npm install hermes-web-ui
│   ├── config_callback   # Save Gateway config from wizard
│   ├── uninstall_init    # Stop process, clean node_modules
│   └── uninstall_callback # Remove data/config/logs
├── config/
│   ├── privilege         # {"defaults": {"run-as": "package"}}
│   └── resource          # {"data-share": {"shares": []}}
├── wizard/
│   ├── install           # Gateway URL/key configuration
│   └── config            # Settings page (same fields)
├── README.md
└── CHANGELOG.md
```

## Key Design Decisions

1. **URL entry type** (`"type": "url"`) — opens in new browser tab, not iframe. More reliable for debugging.
2. **npm install in install_init** — fetches hermes-web-ui at install time, not bundled.
3. **wizard/config + config_callback** — allows users to change Gateway settings via App Center UI without SSH.
4. **Gateway mode default** — `HERMES_WEBUI_CHAT_BACKEND=gateway` with remote Gateway URL.

## Build & Deploy

```bash
# On fnOS
cd hermes-webui-fnos
fnpack build          # Produces HermesWebUI.fpk

# Install via Web UI
# App Center → 手动安装 → select HermesWebUI.fpk
```

## Upstream Reference

- hermes-webui: https://github.com/nesquena/hermes-webui
- hermes-webui-fnos-bak (old fork): https://github.com/techysy/hermes-webui-fnos-bak
- fnOS developer docs: https://developer.fnnas.com/docs/guide

## Version Numbering

Sync manifest version with upstream hermes-webui releases:
```ini
version = 0.52.106  # Match upstream tag
```

This makes it clear which upstream version the package wraps.

## Cleanup: Removing Old fnOS App Remnants

When switching from old fnOS apps to new ones, clean up remnants:

```bash
# App data
rm -rf /vol4/@appdata/HermesAgentCN /vol4/@appdata/HermesWebUI /vol4/@appdata/HermesWebUICN

# App config
rm -rf /vol4/@appconf/HermesAgentCN /vol4/@appconf/HermesStudio /vol4/@appconf/HermesWebUI /vol4/@appconf/HermesWebUICN /vol4/@appconf/trim.hermes

# Logs (requires sudo)
sudo rm -f /var/log/apps/Hermes*.log* /var/log/apps/trim.hermes.log*

# Temp files
rm -f /tmp/hermes-pty-active-*.json
```

Note: `appcenter-cli install-fpk` was removed in fnOS 1.1.31xx series. Only App Center manual install works.

## Build & Release Workflow

```bash
# On NAS — build and copy to SSD
cd /tmp/hermes-webui-fnos && git pull && fnpack build
cp HermesWebUI.fpk /vol4/1000/SSD/

# On Arch VM — create GitHub release
gh release create vX.Y.Z --title "vX.Y.Z" --notes "..." /path/to/HermesWebUI.fpk
```
