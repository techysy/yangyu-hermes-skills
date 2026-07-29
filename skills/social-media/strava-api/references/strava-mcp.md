# Strava MCP Connector

Strava offers two MCP options:

## 1. Official Strava MCP (`mcp.strava.com`)

- Endpoint: `https://mcp.strava.com/mcp`
- Auth: OAuth 2.0 Bearer token from `www.strava.com/mcp-issuer`
- Scopes: `read`, `read_all`, `activity:read`, `activity:read_all`, `profile:read_all`
- Status: **Authorization server not publicly open** (mcp-issuer returns 404 as of July 2026)

## 2. Third-party: `eddmann/strava-mcp`

- PyPI: `mcp-strava` (`uvx mcp-strava auth`)
- GitHub: https://github.com/eddmann/strava-mcp
- Provides: 11 tools (activities, athlete, segments, routes, analysis)
- Auth: OAuth device flow, saves tokens to `~/.strava-mcp.env`
- Works with: Claude Desktop, ChatGPT, Hermes (via stdio MCP transport)

### Hermes MCP Config

```yaml
mcp_servers:
  strava:
    command: "uvx"
    args: ["mcp-strava"]
```

Run `uvx mcp-strava auth` first to authorize.

### Note for OpenClash users

Behind fake-ip DNS, you'll need the SSH + `--resolve` workaround for OAuth.
See `references/router-proxy-workaround.md`.
