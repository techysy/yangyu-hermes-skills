# Strava API Credential Storage

Stored in `scripts/strava_creds.py` — imported by any script that needs Strava access.
Contains `CLIENT_ID`, `CLIENT_SECRET`, `ACCESS_TOKEN`, `REFRESH_TOKEN`, `ATHLETE_ID`.

## Auto-refresh

`scripts/strava_refresh.py` handles token refresh automatically (tokens expire in 6 hours).
Run it before any fetch call, or let the skill's fetch script call it internally.

## Test

```bash
python3 scripts/strava_creds.py  # prints masked values to confirm loaded
```
