#!/usr/bin/env python3
# Strava token auto-refresh. Updates strava_creds.py in-place.
# Outputs new access_token to stdout.
import json, urllib.request, urllib.parse, sys, os, re

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
from strava_creds import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN

CREDS = os.path.join(DIR, "strava_creds.py")
data = urllib.parse.urlencode({
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN,
}).encode()

resp = json.loads(urllib.request.urlopen(
    urllib.request.Request("https://www.strava.com/oauth/token", data=data)
).read())

new_access = resp["access_token"]
new_refresh = resp["refresh_token"]

with open(CREDS) as f:
    content = f.read()

for attr, val in [("ACCESS_TOKEN", new_access), ("REFRESH_TOKEN", new_refresh)]:
    content = re.sub(
        rf'^{attr}\s*=\s*\".*\"',
        f'{attr}="{val}"',
        content, flags=re.MULTILINE
    )

with open(CREDS, "w") as f:
    f.write(content)

print(new_access)