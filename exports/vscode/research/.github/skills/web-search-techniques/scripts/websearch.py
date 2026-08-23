#!/usr/bin/env python3
"""Optional serper.dev search backend for the research agents.

Google results through serper.dev, for when `SERPER_API_KEY` is set. The
native WebSearch tool is the default backend; this script is never required.
What it adds: Google's index as a second source of candidates, the `news` and
`scholar` verticals, date filtering, and up to 100 results per call.

Usage:
    python websearch.py "QUERY" [--vertical search|news|scholar] [--num N]
                        [--since h|d|w|m|y] [--gl CC] [--hl LANG] [--page P]
                        [--json] [--timeout SECONDS]
    python websearch.py --check-key      # is a key available? no network call
    printf '%s' KEY | python websearch.py --set-key   # save it for future runs

The key is read from $SERPER_API_KEY, then from ~/.serper_key. The second is
what --set-key writes, so a key pasted once in chat is available to every later
run without travelling through any agent prompt.

Prints a compact result list (rank, title, URL, snippet, date when present,
then answer box, knowledge graph, related questions) or the raw JSON with
`--json`. Snippets qualify a page for reading; they are never a source on
their own. Read pages with WebFetch or webfetch.py.

Exit codes:
    0  success
    1  HTTP error, timeout, or malformed response (one line on stderr)
    2  no key available, or --set-key got nothing on stdin (setup line on stderr)
Agents pivot on non-zero; they do not retry in a loop.

No dependencies beyond the standard library.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_KEY = 2

BASE = "https://google.serper.dev"
VERTICALS = ("search", "news", "scholar")
SINCE = {"h": "qdr:h", "d": "qdr:d", "w": "qdr:w", "m": "qdr:m", "y": "qdr:y"}
MAX_NUM = 100
DEFAULT_NUM = 10
DEFAULT_TIMEOUT = 20

KEY_FILE = Path.home() / ".serper_key"

SETUP_LINE = (
    "No serper.dev key found. Looked at $SERPER_API_KEY and at "
    f"{KEY_FILE}. Get a key at https://serper.dev (2,500 free queries, no card), "
    "then either export SERPER_API_KEY=<key> or save it with "
    "`python websearch.py --set-key` (reads the key from stdin). "
    "Without a key the native WebSearch backend is used instead."
)


def resolve_key(env=None, key_file=None):
    """(key, source). The environment wins; the key file is the fallback the
    /research:team-research lead writes when the user pastes a key in chat, so
    the key lives in one place instead of travelling through spawn prompts."""
    env = os.environ if env is None else env
    key = (env.get("SERPER_API_KEY") or "").strip()
    if key:
        return key, "env"
    path = KEY_FILE if key_file is None else Path(key_file)
    try:
        key = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None, None
    return (key, str(path)) if key else (None, None)


def save_key(key, key_file=None):
    """Write the key readable only by this user. Returns the path.

    chmod is a no-op on Windows, where the file inherits the profile's ACL;
    that is why the caller is told the path rather than promised a mode."""
    path = KEY_FILE if key_file is None else Path(key_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key.strip() + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def mask(key):
    """Never print a key back in full: an echoed secret outlives the moment."""
    key = key.strip()
    return f"{'*' * max(0, len(key) - 4)}{key[-4:]}" if len(key) > 4 else "****"


class FetchError(Exception):
    """HTTP, timeout, or malformed-response failure, rendered as one stderr line."""


def endpoint(vertical: str) -> str:
    if vertical not in VERTICALS:
        raise ValueError(f"unknown vertical: {vertical}")
    return f"{BASE}/{vertical}"


def build_payload(query: str, num: int = DEFAULT_NUM, since: str | None = None,
                  gl: str | None = None, hl: str | None = None, page: int | None = None,
                  autocorrect: bool = True) -> dict:
    payload = {"q": query, "num": max(1, min(int(num), MAX_NUM)), "autocorrect": autocorrect}
    if since:
        payload["tbs"] = SINCE[since]
    if gl:
        payload["gl"] = gl
    if hl:
        payload["hl"] = hl
    if page:
        payload["page"] = int(page)
    return payload


def fetch(url: str, payload: dict, key: str, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"X-API-KEY": key, "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"connection failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise FetchError(f"timeout after {timeout}s") from exc
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise FetchError("malformed JSON response") from exc
    if not isinstance(parsed, dict):
        raise FetchError("unexpected response shape")
    return parsed


def _meta(item: dict) -> str:
    bits = []
    for k in ("date", "year", "source", "publicationInfo", "citedBy"):
        v = item.get(k)
        if v:
            bits.append(f"{k}: {v}" if k != "date" else str(v))
    return f" ({'; '.join(bits)})" if bits else ""


def render(data: dict, vertical: str) -> str:
    items = data.get("news") if vertical == "news" else data.get("organic")
    items = items or []
    lines = []
    if not items:
        lines.append("No results.")
    for i, item in enumerate(items, 1):
        title = item.get("title") or "(untitled)"
        link = item.get("link") or ""
        lines.append(f"{i}. {title}{_meta(item)}")
        lines.append(f"   {link}")
        snippet = (item.get("snippet") or "").strip()
        if snippet:
            lines.append(f"   {snippet}")
    box = data.get("answerBox")
    if isinstance(box, dict):
        answer = box.get("answer") or box.get("snippet")
        if answer:
            lines.append(f"Answer box: {answer} [{box.get('link', '')}]")
    kg = data.get("knowledgeGraph")
    if isinstance(kg, dict) and kg.get("title"):
        desc = kg.get("description") or kg.get("type") or ""
        lines.append(f"Knowledge graph: {kg['title']}. {desc}".rstrip())
    paa = data.get("peopleAlsoAsk") or []
    if paa:
        lines.append("People also ask:")
        for q in paa:
            if isinstance(q, dict) and q.get("question"):
                lines.append(f"  - {q['question']} [{q.get('link', '')}]")
    related = [r.get("query") for r in data.get("relatedSearches") or [] if isinstance(r, dict)]
    related = [r for r in related if r]
    if related:
        lines.append("Related searches: " + ", ".join(related))
    return "\n".join(lines) + "\n"


def parse_args(argv):
    p = argparse.ArgumentParser(description="Search Google through serper.dev (optional backend).")
    p.add_argument("query", nargs="?", default=None)
    p.add_argument("--check-key", action="store_true",
                   help="report whether a key is available and stop. Makes no network call, "
                        "so it costs no credit")
    p.add_argument("--set-key", action="store_true",
                   help=f"read a key from stdin and save it to {KEY_FILE}")
    p.add_argument("--vertical", choices=VERTICALS, default="search")
    p.add_argument("--num", type=int, default=DEFAULT_NUM)
    p.add_argument("--since", choices=sorted(SINCE), default=None)
    p.add_argument("--gl", default=None, help="country code, e.g. us, it")
    p.add_argument("--hl", default=None, help="language code, e.g. en")
    p.add_argument("--page", type=int, default=None)
    p.add_argument("--json", action="store_true", help="print the raw JSON response")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    return p.parse_args(argv)


def main(argv=None, fetcher=fetch, stdin=None) -> int:
    args = parse_args(argv)

    if args.set_key:
        raw = (stdin if stdin is not None else sys.stdin).read().strip()
        if not raw:
            print("No key on stdin. Pipe it in: printf '%s' <key> | "
                  "python websearch.py --set-key", file=sys.stderr)
            return EXIT_NO_KEY
        path = save_key(raw)
        print(f"saved {mask(raw)} to {path}")
        return EXIT_OK

    key, source = resolve_key()

    if args.check_key:
        if key:
            print(f"key available ({'environment' if source == 'env' else source})")
            return EXIT_OK
        print(SETUP_LINE, file=sys.stderr)
        return EXIT_NO_KEY

    if not key:
        print(SETUP_LINE, file=sys.stderr)
        return EXIT_NO_KEY
    if args.query is None:
        print("No query given. Usage: websearch.py \"<query>\" [--vertical ...]",
              file=sys.stderr)
        return EXIT_ERROR
    if args.num > 10:
        print("note: more than 10 results costs 2 credits per query on serper.dev",
              file=sys.stderr)
    payload = build_payload(args.query, num=args.num, since=args.since, gl=args.gl,
                            hl=args.hl, page=args.page)
    try:
        data = fetcher(endpoint(args.vertical), payload, key, args.timeout)
    except FetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render(data, args.vertical))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
