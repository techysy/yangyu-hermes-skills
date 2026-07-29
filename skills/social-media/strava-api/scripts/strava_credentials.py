"""Strava API credentials - auto-refresh token store"""
import json, urllib.request, urllib.parse, os

CONFIG = {
    "client_id": "254304",
    "client_secret": "ee886ed9f7f60b5a0afa0a2ee191b20c3869cb2d",
    "athlete_id": "121173304",
}

_last_token = None

def _tokens_path():
    return os.path.join(os.path.dirname(__file__), "..", "references", "strava_tokens.json")

def get_token():
    global _last_token
    tokens = _load_tokens()
    if not tokens:
        return None
    
    data = urllib.parse.urlencode({
        "client_id": CONFIG["client_id"],
        "client_secret": CONFIG["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"]
    }).encode()
    
    try:
        resp = json.loads(urllib.request.urlopen(
            urllib.request.Request("https://www.strava.com/oauth/token", data=data),
            timeout=15
        ).read())
        _last_token = resp["access_token"]
        _save_tokens(resp["access_token"], resp["refresh_token"], resp.get("scope", ""))
        return resp["access_token"]
    except Exception as e:
        print(f"Token refresh failed: {e}")
        return None

def _load_tokens():
    path = _tokens_path()
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def _save_tokens(access, refresh, scope):
    path = _tokens_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"access_token": access, "refresh_token": refresh, "scope": scope}, f, indent=2)

def save_initial_tokens(access_token, refresh_token, scope):
    _save_tokens(access_token, refresh_token, scope)

def get_athlete_stats(token=None):
    if not token:
        token = get_token()
    if not token:
        return None
    req = urllib.request.Request(
        f"https://www.strava.com/api/v3/athletes/{CONFIG['athlete_id']}/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

def get_recent_activities(per_page=10, token=None):
    if not token:
        token = get_token()
    if not token:
        return None
    req = urllib.request.Request(
        f"https://www.strava.com/api/v3/athlete/activities?per_page={per_page}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())
