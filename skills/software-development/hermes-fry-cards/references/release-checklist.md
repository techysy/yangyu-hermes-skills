# Release Checklist for hermes-fry-cards

## Pre-release
1. Run tests: `HERMES_PYTHON=~/.hermes/hermes-agent/venv/bin/python3 $HERMES_PYTHON -m pytest tests/ -q`
2. Verify no new failures (baseline: 4 failures)
3. Update version in `pyproject.toml` and `__init__.py`
4. Update `CHANGELOG.md` with new entries
5. Update `README.md` badge version

## Release
1. Commit changes
2. Push to main
3. Create tag: `git tag vX.Y.Z-rcN`
4. Push tag: `git push origin vX.Y.Z-rcN`
5. Create GitHub release: `gh release create vX.Y.Z-rcN --prerelease --title "vX.Y.Z-rcN" --notes "..."`
6. Upload assets: `gh release upload vX.Y.Z-rcN INSTALL.md skill.md`

## Post-release
1. Verify release page shows correct assets
2. Update skill file if needed
3. Notify relevant groups if applicable

## Common Issues
- **Draft state**: If release shows as draft, delete and recreate with `gh release delete` + `gh release create`
- **Missing assets**: Re-upload with `gh release upload --clobber`
- **Tag mismatch**: Delete remote tag, recreate, force push
