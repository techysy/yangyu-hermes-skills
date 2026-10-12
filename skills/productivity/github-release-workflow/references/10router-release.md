# 10Router v1.0.0 Release Reference

## Repository
- `techysy/10router` — main repo (Docker + fpk + standalone all in one)

## Three Parallel Workflows (triggered by `v*` tag)

| Workflow | Output | Typical Duration |
|----------|--------|-----------------|
| `docker-publish.yml` | `ghcr.io/techysy/10router:X.Y.Z` + `:latest` | 15-20 min (multi-platform amd64+arm64) |
| `build-fpk.yml` | 4 fpk: `10router-X.Y.Z[-iframe]-{x86,arm}.fpk` | 2-3 min |
| `build-server.yml` | `10router-server.tar.gz` | 1-2 min |

## Release Assets (5 total)
- `10router-1.0.0-x86.fpk`
- `10router-1.0.0-arm.fpk`
- `10router-1.0.0-iframe-x86.fpk`
- `10router-1.0.0-iframe-arm.fpk`
- `10router-server.tar.gz`

## Key Learnings from v1.0.0

### Release Notes Overwrite Issue
`build-server.yml` auto-overwrites the release description when uploading its asset. Fix:
```bash
gh release edit v1.0.0 --notes-file /tmp/10router-release-notes.md
```

### Docker `:latest` Tag
Ensure `docker-publish.yml` has `type=raw,value=latest,enable=${{ startsWith(github.ref, 'refs/tags/v') }}` so tag pushes also update latest.

### Data Directory Migration
v1.0.0 changed data dir from `~/.9router` to `~/.10router`. Migration is automatic (one-time cpSync on first start when old dir exists and new dir is empty).

## Breaking Changes (document in CHANGELOG)
- Data directory: `~/.9router` → `~/.10router`
- SAML entityID: `urn:9router:sp` → `urn:10router:sp`
- MITM CA renamed

## Notification Groups
- fnOS 群: `oc_ee1b7f03464e3c4f80772afb958f47cc`
- 10Router 群: `oc_d1341c474b7641ccc48c4e85c9b690b4`
