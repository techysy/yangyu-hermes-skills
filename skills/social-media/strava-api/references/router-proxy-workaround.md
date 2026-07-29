# Router Proxy Workaround for OpenClash Environments

When the host machine is behind OpenClash (fake-ip mode), ALL HTTPS traffic gets DNS-hijacked to `198.18.x.x` (Clash virtual IPs). Python's `urllib`, Node.js fetch, and most HTTP clients will fail with `SSL: UNEXPECTED_EOF_WHILE_READING`.

## Root Cause

- DNS resolver returns `198.18.8.31` for all external domains (fake-ip)
- OpenClash's TUN mode is OFF so those IPs are unroutable
- `--noproxy` and env var unsetting (`unset http_proxy`) do NOT help — the DNS is configured at system level

## Solution: SSH + --resolve

Route API calls through the OpenClash router itself, which has working DNS and proxy routing.

### Step 1: Find the real IP

```bash
ssh root@ROUTER_IP "nslookup api.strava.com 8.8.8.8"
```

### Step 2: Call API with --resolve

```bash
ssh root@ROUTER_IP \
  "curl -s --max-time 15 --resolve 'api.strava.com:443:104.26.11.186' \
    -H 'Authorization: Bearer TOKEN' \
    'https://api.strava.com/api/v3/athlete/activities?per_page=5'"
```

### Step 3: Python/Programmatic Calls

1. Write a shell script to `scp` to router, then `ssh` execute
2. Or use `subprocess.run` with `capture_output=True` and parse JSON from stdout

```python
import subprocess, json
cmd = "ssh root@ROUTER_IP 'curl -s --max-time 15 --resolve \\"api.strava.com:443:104.26.11.186\\" -H \\"Authorization: Bearer TOKEN\\" \\"https://api.strava.com/api/v3/athlete/activities?per_page=5\\"'"
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
data = json.loads(result.stdout)
```

### Token Refresh (same pattern)

```python
cmd = f"""ssh root@ROUTER_IP 'curl -s --max-time 15 --resolve "www.strava.com:443:104.26.11.186" -X POST https://www.strava.com/oauth/token -d "client_id=ID" -d "client_secret=SECRET" -d "grant_type=refresh_token" -d "refresh_token={refresh_token}"' > /tmp/strava_resp.json"""
subprocess.run(cmd, shell=True, timeout=30)
```

### Known Real IPs

| Domain | Real IP | 
|--------|---------|
| `www.strava.com` | `104.26.11.186` |
| `api.strava.com` | `104.26.11.186` |
| `intervals.icu` | `104.26.14.117` or `172.67.73.247` |

### Pitfalls

1. **SSH warning noise**: every SSH call prints a PQ warning — filter it out
2. **Token file on host vs router**: refresh the token on the router, save back to host
3. **shell quoting**: complex JSON in `-d` on router may fail. Use `cat > /tmp/script.sh << 'ENDSCRIPT'` pattern for reliability
4. **Token truncation**: if the refresh response contains `...` in the token, store it as a raw response file and parse with Python
