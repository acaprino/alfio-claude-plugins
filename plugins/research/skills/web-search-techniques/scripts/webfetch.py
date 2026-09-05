#!/usr/bin/env python3
"""Fast web fetcher with Chrome TLS impersonation for research agents.

Uses curl_cffi to impersonate a real Chrome browser (TLS fingerprint, HTTP/2,
header order) so sites that block bots via TLS/JA3 fingerprinting serve
normal content. Falls back to httpx if curl_cffi is unavailable.

Usage:
    python webfetch.py URL [--timeout SECONDS] [--max-chars CHARS] [--raw]

Returns clean text content extracted from HTML pages.
Exits with code 1 on timeout or error -- agents should proceed without the result.

Dependencies (install before use):
    pip install curl_cffi beautifulsoup4
    # Optional fallback: pip install httpx
"""

from __future__ import annotations

import argparse
import io
import sys
from urllib.parse import urlparse

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 not installed. Run: pip install beautifulsoup4", file=sys.stderr)
    sys.exit(1)

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

if not HAS_CURL_CFFI and not HAS_HTTPX:
    print("Error: neither curl_cffi nor httpx installed. Run: pip install curl_cffi", file=sys.stderr)
    sys.exit(1)

DEFAULT_TIMEOUT = 15
DEFAULT_MAX_CHARS = 30000
MAX_REDIRECTS = 5
CONNECT_TIMEOUT = 10

ALLOWED_SCHEMES = ("http", "https")

# Tags that don't contain useful content
STRIP_TAGS = (
    "script", "style", "nav", "footer", "header", "aside",
    "iframe", "noscript", "svg", "form", "button",
)


def validate_url(url: str) -> None:
    """Reject non-HTTP(S) URLs to prevent SSRF."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Blocked URL scheme: {parsed.scheme or '(empty)'}. Only http/https allowed.")
    if not parsed.hostname:
        raise ValueError("No hostname in URL.")


def fetch_url(url: str, timeout: int) -> tuple[str, str]:
    """Fetch URL and return (text, content_type). Tries curl_cffi first, then httpx."""
    if HAS_CURL_CFFI:
        resp = cffi_requests.get(
            url,
            impersonate="chrome",
            timeout=timeout,
            allow_redirects=True,
            max_redirects=MAX_REDIRECTS,
        )
        resp.raise_for_status()
        return resp.text, resp.headers.get("content-type", "")

    # Fallback to httpx
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(
        timeout=httpx.Timeout(timeout, connect=CONNECT_TIMEOUT),
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
    ) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
    return resp.text, resp.headers.get("content-type", "")


def extract_text(html: str, max_chars: int) -> str:
    """Extract clean text from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in STRIP_TAGS:
        for el in soup.find_all(tag):
            el.decompose()

    # Try to find main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find(id="content")
        or soup.find(class_="content")
        or soup.body
        or soup
    )

    text = main.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    lines = []
    prev_blank = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if not prev_blank:
                lines.append("")
                prev_blank = True
        else:
            lines.append(stripped)
            prev_blank = False

    return "\n".join(lines)[:max_chars]


def is_html_content(content_type: str) -> bool:
    """Check if content-type indicates HTML."""
    mime = content_type.split(";")[0].strip().lower()
    return mime in ("text/html", "application/xhtml+xml")


def main():
    parser = argparse.ArgumentParser(description="Fetch web page with Chrome impersonation and strict timeout")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help=f"Max output chars (default: {DEFAULT_MAX_CHARS})")
    parser.add_argument("--raw", action="store_true", help="Return raw response without HTML extraction")
    args = parser.parse_args()

    try:
        validate_url(args.url)
        text, content_type = fetch_url(args.url, args.timeout)

        if args.raw or not is_html_content(content_type):
            print(text[:args.max_chars])
        else:
            print(extract_text(text, args.max_chars))

    except Exception as e:
        err = str(e).lower()
        if "timeout" in err or "timed out" in err:
            print(f"TIMEOUT: request did not complete within {args.timeout}s", file=sys.stderr)
        elif "blocked" in err or "scheme" in err:
            print(f"VALIDATION: {e}", file=sys.stderr)
        else:
            print("ERROR: failed to fetch URL", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
