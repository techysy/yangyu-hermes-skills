#!/usr/bin/env python3
"""release_notify.py — GitHub release → Feishu interactive card → group.

Sends a Feishu card (release notes + optional README summary) to a chat via the
Hermes bot app. Validated working 2026-08 (dsh 0.1.0-rc.7 → oc_ee1b7f...).

Usage:
  python3 release_notify.py --repo techysy/deepseek-harness-fnos --tag 0.1.0-rc.7 \
      --chat oc_ee1b7f03464e3c4f80772afb958f47cc [--readme]

Credentials: FEISHU_APP_ID / FEISHU_APP_SECRET from ~/.hermes/.env (single-quoted → stripped).
Note: bot must be in the chat (230002) and the app needs external-group permission for
cross-tenant groups (232033) — else use a custom-robot webhook instead (see SKILL.md).
"""
import argparse
import json
import os
import re
import sys
import urllib.request

ENV_PATH = os.path.expanduser("~/.hermes/.env")
FEISHU_DOMAIN = "open.feishu.cn"
MAX_BODY = 4000


def env_val(key):
    if not os.path.isfile(ENV_PATH):
        return ""
    for line in open(ENV_PATH, encoding="utf-8"):
        line = line.strip()
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip("'").strip('"')
    return ""


def http_json(url, data=None, headers=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if data is not None else "GET"))
    req.add_header("Content-Type", "application/json; charset=utf-8")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def get_token():
    d = http_json(f"https://{FEISHU_DOMAIN}/open-apis/auth/v3/tenant_access_token/internal",
                  {"app_id": env_val("FEISHU_APP_ID"), "app_secret": env_val("FEISHU_APP_SECRET")})
    if d.get("code") != 0:
        print(f"token error: {d}", file=sys.stderr)
        sys.exit(1)
    return d["tenant_access_token"]


def fetch_release(repo, tag):
    return http_json(f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
                     headers={"Accept": "application/vnd.github+json", "User-Agent": "release-notify"})


def fetch_readme(repo):
    d = http_json(f"https://api.github.com/repos/{repo}/readme",
                  headers={"Accept": "application/vnd.github.raw+json", "User-Agent": "release-notify"})
    if isinstance(d, dict) and "content" in d:
        return d["content"]
    return d if isinstance(d, str) else ""


def md_to_plain(md, maxlen):
    lines = []
    for ln in md.splitlines():
        if ln.startswith("<!--") or ln.startswith("[!["):
            continue
        if ln.startswith("#"):
            continue
        if ln.strip().startswith("|") and ln.strip().endswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            lines.append(" | ".join(cells))
            continue
        lines.append(ln)
    return "\n".join(lines).strip()[:maxlen]


def build_card(repo, tag, rel, readme=""):
    name = rel.get("name") or f"{repo} {tag}"
    elements = []
    fields = []
    assets = rel.get("assets") or []
    if assets:
        fields.append({"is_short": True, "text": {"tag": "lark_md", "content": f"**📦 资产**\n{len(assets)} 个"}})
    if rel.get("published_at"):
        fields.append({"is_short": True, "text": {"tag": "lark_md", "content": f"**🕒 发布时间**\n{rel['published_at'][:10]}"}})
    if fields:
        elements.append({"tag": "div", "fields": fields})
        elements.append({"tag": "hr"})

    body_plain = md_to_plain(rel.get("body") or "", MAX_BODY)
    if body_plain:
        elements.append({"tag": "markdown", "content": body_plain})

    if readme:
        rd_plain = md_to_plain(readme, 2000)
        if rd_plain:
            elements.append({"tag": "hr"})
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "**📖 项目说明**"}})
            elements.append({"tag": "markdown", "content": rd_plain})

    links = [f"[Release 详情]({rel.get('html_url') or f'https://github.com/{repo}/releases/tag/{tag}'})",
             f"[GitHub 仓库](https://github.com/{repo})"]
    elements.append({"tag": "hr"})
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": " · ".join(links)}})

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"🚀 {name}"}, "template": "blue"},
        "elements": elements,
    }


def send_card(chat_id, card, token):
    return http_json(
        f"https://{FEISHU_DOMAIN}/open-apis/im/v1/messages?receive_id_type=chat_id",
        {"receive_id": chat_id, "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)},
        headers={"Authorization": f"Bearer {token}"},
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--chat", required=True)
    ap.add_argument("--readme", action="store_true")
    args = ap.parse_args()

    rel = fetch_release(args.repo, args.tag)
    if not rel or "html_url" not in rel:
        print(f"release not found: {args.repo} {args.tag}", file=sys.stderr)
        sys.exit(1)
    card = build_card(args.repo, args.tag, rel, fetch_readme(args.repo) if args.readme else "")
    resp = send_card(args.chat, card, get_token())
    if resp.get("code") == 0:
        print(f"✅ 卡片已发送: {args.repo} {args.tag} -> {args.chat}")
    else:
        print(f"❌ 发送失败: {resp}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
