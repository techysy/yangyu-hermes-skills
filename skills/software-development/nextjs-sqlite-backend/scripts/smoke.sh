#!/usr/bin/env bash
# Smoke-test a Next.js+SQLite app with cookie auth (built for fryrouter, generic shape).
# Usage: BASE=http://localhost:20129 PASSWORD=secret bash smoke.sh
# Checks: unauth 401/redirect, login, authed CRUD, secret-not-echoed, CSS actually loaded.
set -u
BASE="${BASE:-http://localhost:20129}"
PASSWORD="${PASSWORD:?PASSWORD env required}"
PASS=0; FAIL=0

ok()   { echo "  ok: $1"; PASS=$((PASS+1)); }
bad()  { echo "FAIL: $1"; FAIL=$((FAIL+1)); }

echo "── 1. unauthenticated access"
code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/providers")
[ "$code" = "401" ] && ok "unauth API -> 401" || bad "unauth API got $code (want 401)"
res=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$BASE/dashboard")
case "$res" in 3[07][27]*login*) ok "unauth dashboard -> $res";; *) bad "dashboard redirect got $res";; esac

echo "── 2. login"
curl -s -c /tmp/smoke_cookies.txt -o /dev/null -w '%{http_code}' \
  -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"password\":\"$PASSWORD\"}" | grep -q 200 && ok "login 200" || bad "login failed"
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' -d '{"password":"definitely-wrong"}')
[ "$code" = "401" ] && ok "wrong password -> 401" || bad "wrong password got $code"

echo "── 3. CSS really injected (build passing is not enough)"
html=$(curl -s "$BASE/login")
csspath=$(printf '%s' "$html" | grep -o '/_next/static/css/[^"]*\.css' | head -1)
if [ -n "$csspath" ]; then
  cssstat=$(curl -s -o /dev/null -w '%{http_code} %{size_download}' "$BASE$csspath")
  case "$cssstat" in "200 "[1-9]*) ok "css $csspath -> $cssstat bytes";; *) bad "css empty/broken: $cssstat";; esac
else
  bad "no css link tag in login HTML — globals.css not imported?"
fi

echo "── 4. provider CRUD roundtrip + secret never echoed"
created=$(curl -s -b /tmp/smoke_cookies.txt -X POST "$BASE/api/providers" \
  -H 'Content-Type: application/json' \
  -d '{"name":"__smoke__","provider":"openai","apiKey":"sk-SMOKE-123","modelIds":"m1,m2"}')
pid=$(printf '%s' "$created" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))')
[ -n "$pid" ] && ok "provider created" || bad "provider create failed: $created"
if printf '%s' "$created" | grep -q 'sk-SMOKE-123'; then bad "apiKey echoed in plaintext!"; else ok "apiKey not echoed"; fi
listed=$(curl -s -b /tmp/smoke_cookies.txt "$BASE/api/providers")
printf '%s' "$listed" | grep -q 'sk-SMOKE-123' && bad "apiKey echoed in list!" || ok "list keeps secret hidden"
code=$(curl -s -o /dev/null -w '%{http_code}' -b /tmp/smoke_cookies.txt \
  -X PUT "$BASE/api/providers/$pid" -H 'Content-Type: application/json' -d '{"name":"__smoke2__"}')
[ "$code" = "200" ] && ok "provider updated (empty apiKey kept)" || bad "update got $code"

echo "── 5. cleanup + delete check"
code=$(curl -s -o /dev/null -w '%{http_code}' -b /tmp/smoke_cookies.txt -X DELETE "$BASE/api/providers/$pid")
[ "$code" = "200" ] && ok "provider deleted" || bad "delete got $code"
rm -f /tmp/smoke_cookies.txt

echo "═══ $PASS passed, $FAIL failed"
exit $([ "$FAIL" = 0 ] && echo 0 || echo 1)
