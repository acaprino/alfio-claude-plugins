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

Prints a compact result list (rank, title, URL, snippet, date when present,
then answer box, knowledge graph, related questions) or the raw JSON with
`--json`. Snippets qualify a page for reading; they are never a source on
their own. Read pages with WebFetch or webfetch.py.

Exit codes:
    0  success
    1  HTTP error, timeout, or malformed response (one line on stderr)
    2  SERPER_API_KEY not set (setup line on stderr)
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

SETUP_LINE = (
    "SERPER_API_KEY is not set. Get a key at https://serper.dev (2,500 free queries, "
    "no card) and export SERPER_API_KEY=<key>; or run with the native WebSearch backend."
)


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
    p.add_argument("query")
    p.add_argument("--vertical", choices=VERTICALS, default="search")
    p.add_argument("--num", type=int, default=DEFAULT_NUM)
    p.add_argument("--since", choices=sorted(SINCE), default=None)
    p.add_argument("--gl", default=None, help="country code, e.g. us, it")
    p.add_argument("--hl", default=None, help="language code, e.g. en")
    p.add_argument("--page", type=int, default=None)
    p.add_argument("--json", action="store_true", help="print the raw JSON response")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    return p.parse_args(argv)


def main(argv=None, fetcher=fetch) -> int:
    args = parse_args(argv)
    key = os.environ.get("SERPER_API_KEY", "").strip()
    if not key:
        print(SETUP_LINE, file=sys.stderr)
        return EXIT_NO_KEY
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
