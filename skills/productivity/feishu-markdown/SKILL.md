---
name: feishu-markdown
description: "Fix Feishu/Lark markdown rendering issues in Hermes Agent — tables, bold, code blocks, etc."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [feishu, lark, markdown, tables, rendering, adapter]
    related_skills: [feishu-table-render]
---

# Feishu Markdown Rendering Fix

Fixes common markdown rendering issues in Hermes Agent's Feishu/Lark adapter.

## Problem 1: Tables render as plain text

The Feishu adapter forces `msg_type=text` for content containing markdown tables.

**Fix:** Remove the table check in the adapter:

```python
# plugins/platforms/feishu/adapter.py — _build_outbound_payload()
# Remove this block:
if _MARKDOWN_TABLE_RE.search(content):
    text_payload = {"text": content}
    return "text", json.dumps(text_payload, ensure_ascii=False)
```

## Problem 2: All markdown stripped

Feishu adapter strips markdown, showing raw text.

**Fix:**

```bash
hermes config set display.final_response_markdown keep
```

> ⚠️ `final_response_markdown` goes under `display:`, NOT top level. `hermes config set` creates top-level keys — use `config edit` for nested values.

## Problem 3: Tables still broken after fix

After removing the table check, ensure `display.final_response_markdown` is `keep` (not `strip`).

## Verification

Send a message with **bold**, *italic*, `code`, and a markdown table — all should render in Feishu.
