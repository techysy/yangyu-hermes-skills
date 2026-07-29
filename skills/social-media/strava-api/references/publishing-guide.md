# Hermes Skill Publishing Guide

Lessons from open-sourcing `strava-api` skill.

## Prerequisites

- GitHub CLI (`gh`) or `GITHUB_TOKEN` with `repo` + `workflow` scopes
- `hermes skills publish` command

## Security Scanner Pitfalls

Pre-publish scan verdicts:
- **DANGEROUS** → blocked (even `--force` can't override)
- **SAFE** → allowed

### DANGEROUS triggers (real examples)

| Pattern → Verdict | Fix |
|------------------|-----|
| `SECRET = "replace_with_your_secret"` → credential_exposure | Use `SECRET = "CHANGE_ME"` instead |
| `client_id = "254304"` → credential_exposure | Replace with `"YOUR_CLIENT_ID"` |
| `subprocess.run(...)` → execution (MEDIUM) | Accepted — MEDIUM alone = SAFE verdict |

### .gitignore for public repos

```
# Sensitive files
*/strava_tokens.json
*/strava_credentials.py
*/strava_creds.py
__pycache__/
```

## gh CLI Auth

```bash
sudo pacman -S github-cli
gh auth login       # device code flow
gh auth status      # verify
```

## Publish

```bash
hermes skills publish <skill-dir> --to github --repo <user>/<repo>
```

Note: 404 = repo doesn't exist yet. Create it on GitHub first.

## Tap Discovery

GitHub repos need `skills/<name>/SKILL.md` structure for auto-discovery.
Flat repos work for direct `git clone` installation.
