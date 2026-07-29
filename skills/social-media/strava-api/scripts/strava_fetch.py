#!/usr/bin/env python3
"""
Strava data fetcher — one-shot: exchange code → get tokens → fetch stats + activities.
Usage: 
  1. Get authorization code from user browser
  2. Edit CLIENT_ID, CLIENT_SECRET, CODE below
  3. python3 scripts/strava_fetch.py
"""
import json, urllib.request, urllib.parse, sys

# --- CONFIGURE THESE ---
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
CODE = "YOUR_AUTH_CODE"  # one-time code from OAuth redirect
# -----------------------

def api(path, token):
    req = urllib.request.Request(
        f"https://www.strava.com/api/v3{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return json.loads(urllib.request.urlopen(req).read())

# Step 1: Exchange code for tokens
data = urllib.parse.urlencode({
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "code": CODE, "grant_type": "authorization_code"
}).encode()
resp = json.loads(urllib.request.urlopen(
    urllib.request.Request("https://www.strava.com/oauth/token", data=data)
).read())

token = resp["access_token"]
aid = resp["athlete"]["id"]
print(f"Athlete: {resp['athlete']['firstname']} {resp['athlete']['lastname']} (ID: {aid})")
print(f"Scope: {resp.get('scope')}")
print(f"New refresh token: {resp['refresh_token'][:20]}...\n")

# Step 2: Stats
s = api(f"/athletes/{aid}/stats", token)
rt = s['all_ride_totals']
yt = s['ytd_ride_totals']
print(f"Total rides: {rt['count']} | {rt['distance']/1000:.0f}km | {rt['elapsed_time']/3600:.0f}h | {rt['elevation_gain']:.0f}m")
print(f"This year: {yt['count']} rides | {yt['distance']/1000:.0f}km\n")

# Step 3: Recent activities
acts = api("/athlete/activities?per_page=10", token)
print("Recent 10:")
for a in acts:
    d = a['distance']/1000; mt = a['moving_time']
    h, m, s = mt//3600, (mt%3600)//60, mt%60
    sp = a.get('average_speed', 0)*3.6
    hr = a.get('average_heartrate', '—')
    pw = a.get('average_watts', '—')
    print(f"  {a['start_date_local'][:10]} [{a['type'][:4]:4s}] {d:5.1f}km  {h}:{m:02d}:{s:02d}  {sp:.1f}km/h  🔋{pw}W  💓{hr}  {a['name']}")
