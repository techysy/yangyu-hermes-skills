---
name: feishu-table-render
description: "Use when fixing Feishu/Lark Markdown table rendering in Hermes Agent. Removes the table-to-plaintext fallback so post+md renders tables natively."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [feishu, lark, markdown, tables, adapter]
    related_skills: []
---

# Feishu Markdown Table Rendering Fix

## Overview

Hermes Agent's Feishu adapter historically downgraded Markdown tables to plain text because Feishu's `post` + `md` message type was believed not to support tables. Current Feishu versions **do** support tables in `post` + `md`, so the guard can be removed.

The fix involves two changes:
1. **Adapter code**: Remove the early return that catches Markdown tables and forces plain text.
2. **Config**: Set `final_response_markdown: keep` under the `display:` section.

---

## When to Use

- Hermes responds with raw Markdown table source on Feishu instead of a rendered table
- After upgrading Hermes Agent and Feishu tables appear as plain text
- Setting up a new Feishu bot and tables don't render

---

## Fix Steps

### 1. Check config

Ensure `config.yaml` has:

```yaml
display:
  final_response_markdown: keep
```

This must be under `display:`, NOT at the config root level.

### 2. Locate the adapter file

```bash
ls ~/.hermes/hermes-agent/plugins/platforms/feishu/adapter.py
```

### 3. Remove table-to-plaintext fallback

Find the `_build_outbound_payload` method. Look for a regex check that matches markdown tables (`_MARKDOWN_TABLE_RE`) and delete the early-return block:

**Before:**
```python
# Feishu post-type 'md' elements do not render markdown tables; sending
# table content as post causes the message to appear blank on the client.
# Force plain text for anything that looks like a markdown table.
if _MARKDOWN_TABLE_RE.search(content):
    text_payload = {"text": content}
    return "text", json.dumps(text_payload, ensure_ascii=False)
```

**After:** Delete those lines entirely. The `_MARKDOWN_HINT_RE` check below will catch all Markdown content and send it as `post` + `md`.

### 4. Verify the change (optional)

If you want a safety net, you can replace the removed block with a comment:

```python
# Feishu post-type 'md' elements now support tables (confirmed in current
# Feishu versions). Post-type fallback will downgrade to plain text
# automatically if the API rejects it — no need to force text here.
```

### 5. Restart gateway

```bash
systemctl --user restart hermes-gateway
```

---

## Verification

Send a message with a Markdown table to the Feishu bot:

```
| 列1 | 列2 |
|-----|-----|
| A | B |
| C | D |
```

**Before fix:** Shows as raw plain text

**After fix:** Renders as a proper Feishu three-line table ✅

---

## Common Pitfalls

1. **`final_response_markdown` at wrong config level** — must be under `display:`, not at the top level of `config.yaml`.
2. **Gateway not restarted** — the adapter file is loaded at gateway start; changes won't take effect until `systemctl --user restart hermes-gateway`.
3. **Upstream updates overwrite the patch** — after `pip install --upgrade hermes-agent`, the adapter file is replaced. You'll need to re-apply this fix until upstream merges it.
4. **Upgrade from v0.17.0 to v0.19.0** — this fix was confirmed working on v0.18.x/v0.19.x. Earlier versions may have different adapter structure.

---

## Verification Checklist

- [ ] `config.yaml` has `display.final_response_markdown: keep`
- [ ] `adapter.py` no longer has the `_MARKDOWN_TABLE_RE.search(content)` early return
- [ ] Gateway restarted
- [ ] Feishu bot renders `| col | col |` as a proper table
