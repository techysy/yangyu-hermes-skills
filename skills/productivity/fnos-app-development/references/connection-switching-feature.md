# Connection Switching Feature

Added to Hermes WebUI at `/connection/` endpoint.

## Architecture
- **API**: `/api/connection/config` (GET/POST), `/api/connection/test` (POST)
- **UI**: `/connection/` - Connection settings page
- **Config file**: `/vol4/@appdata/HermesWebUI/gateway.env`

## Gateway Modes
| Mode | Description | URL |
|------|-------------|-----|
| local | Auto-managed by WebUI | N/A |
| local_running | Connect to running local Hermes | http://127.0.0.1:18642 |
| remote | Connect to remote Gateway | http://192.168.31.31:8642 |

## Implementation
- API reads/writes `gateway.env` file
- Tests connection via `/health` endpoint
- Saves config and restarts WebUI

## Known Issues
- hermes-webui server.py doesn't read .env files directly
- Config changes require WebUI restart
- Gateway must be running for connection test to work
