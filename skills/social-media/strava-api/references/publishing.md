# Publishing the Strava API Skill

## What Was Sanitized (2026-07-03)

Before open-sourcing, these categories of sensitive info were removed:

| Category | What was replaced |
|----------|------------------|
| Credentials | `client_id`, `client_secret`, `access_token`, `refresh_token` → placeholders |
| Router IP | `192.168.31.102` → `ROUTER_IP` |
| Home path | `/home/YOUR_USER/...` → `YOUR_SKILL_PATH` |
| Athlete/User IDs | `121173304`, `i221776` → removed |
| Personal data | FTP/weight/knee injury/中江 terrain → deleted |
| PII | Name/Strava nick → removed |

## Files Changed

| File | Change |
|------|--------|
| `SKILL.md` | Removed personal background section, replaced IP/path/credentials, generalized terrain references |
| `references/router-bypass-fakeip.md` | `192.168.31.102` → `ROUTER_IP` |
| `references/hermes-secret-redaction-bypass.md` | IP and example token → placeholders |
| `references/chengdu-cycling-segments.md` | Removed athlete ID, intervals ID, personal website links, personal preferences |
| `scripts/strava_credentials.py` | `client_id`/`secret`/`athlete_id` → placeholders (restored locally) |
| `scripts/strava_creds.py` | `CLIENT_ID`/`ATHLETE_ID` → placeholders (restored locally) |
| `references/strava_tokens.json` | Template only (restored locally) |

## 🔴 必须：检查 Git 历史

**只检查当前工作目录是不够的！** 如果敏感文件在旧提交中被推送过，即使后来用 `.gitignore` 排除并删除了，历史中仍然保存着原文。

```bash
# 1. 检查所有提交中是否含敏感文件
git log --all --diff-filter=A --name-only --format="%h %s" | grep -E "credential|secret|token|publish"

# 2. 检查历史中是否有真实凭证
git log --all -p -- "scripts/strava_credentials.py" | head -30

# 3. 如果发现泄露，用 filter-branch 彻底清除
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch scripts/strava_credentials.py references/strava_tokens.json" \
  --prune-empty -- --all

# 4. 清理残留
git reflog expire --expire=now --all
git gc --aggressive --prune=now

# 5. Force push（⚠️ 改写历史，通知协作者）
git push --force origin main
```

> ⚠️ 如果 Client Secret 已经泄漏，**立即去 Strava API 设置页面重置密钥**，否则别人可以用你的 API 身份。

## Verification Checklist

Before publishing again:

- [ ] `search_files(pattern="192\\.168\\.31\\.102", target="content", path=SKILL_DIR, output_mode="count")` — 0 matches
- [ ] `search_files(pattern="/home/", target="content", path=SKILL_DIR, output_mode="count")` — 0 hits
- [ ] `search_files(pattern="YOUR_", target="content", path=SKILL_DIR, output_mode="files_only")` — only in expected template files
- [ ] No real tokens/credentials in any committed file
- [ ] Run: `hermes skills publish <path> --to github --repo NousResearch/hermes-skills`

## Publish Command

```bash
hermes skills publish ~/.hermes/skills/social-media/strava-api \
  --to github --repo NousResearch/hermes-skills
```

Requires `GITHUB_TOKEN` in `.env` or `gh auth login`.
