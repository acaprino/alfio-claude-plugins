# research 6.0.0 Deep-Research Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `/research:team-research` and its two agents into a parametric lead-plus-parallel-researchers pipeline (clarify, plan, iterate, cite, write a report file) with an optional serper.dev search backend, shipped as `research` 6.0.0 / marketplace 25.0.0 with docs, export twins and an eval harness.

**Architecture:** The command is the lead: it clarifies only ambiguous questions, shows a plan of sub-questions for approval, spawns one `research:deep-researcher` per sub-question in parallel, runs gap analysis with `research:quick-searcher` verifiers and a targeted second wave at `deep`, synthesizes a long-form cited report, runs a citation check and writes the report plus a companion file of raw researcher reports. `deep-researcher` becomes an iterative single-sub-question investigator (search, read, ledger, narrow, stop at saturation). Search goes through native `WebSearch` or, when `SERPER_API_KEY` is set, a stdlib script `websearch.py`. `research` drops its `agent-teams` dependency and depends on nothing.

**Tech Stack:** Markdown agents/commands/skills (no build step), stdlib-only Python (`urllib`, `argparse`, `json`, `unittest`), the repo's Python linters.

**Spec:** `docs/superpowers/specs/2026-08-23-research-deep-research-parity-design.md`

## Global Constraints

- `research` version `5.0.0` -> `6.0.0`; `metadata.version` `24.1.0` -> `25.0.0`, both in `.claude-plugin/marketplace.json`.
- `research` `dependencies` becomes `[]`. No `optionalDependencies` anywhere. No runtime reference to any `agent-teams:*` skill or agent may remain in `plugins/research/` (lint pass 2 fails otherwise).
- The plugin reads no local codebase and spawns no agent from another local plugin (standing rule, CLAUDE.md).
- Agent frontmatter: `model: inherit` (quick-searcher keeps `sonnet`), `color: pink`, kebab-case names matching filenames, long descriptions in YAML `>` form.
- No dash-aside construct anywhere (no `—`, no ` -- `, no ` - ` wrapping an aside) in any file written by this plan. Hyphenated compounds are fine. List bullets `- ` at line start are fine.
- Self-references use `${CLAUDE_PLUGIN_ROOT}/...`; no `plugins/<name>/...` paths in bodies (bundled-path linter).
- Export twins are adapted by hand in the same commit as the source change, per the `downstream-exports` skill; byte-copies and the manifest are CI's job but `python scripts/mirror_export.py` (fix mode) may be run locally so the local checks pass.
- Every task ends at a commit. Nothing in this plan pushes.
- Stage explicit paths only, never `git add -A` (other sessions share this working tree).

---

### Task 1: `websearch.py`, the optional serper.dev backend (TDD)

**Files:**
- Create: `plugins/research/scripts/websearch.py`
- Test: `tests/test_websearch.py`

**Interfaces:**
- Produces: CLI `python ${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py "<query>" [--vertical search|news|scholar] [--num N] [--since h|d|w|m|y] [--gl CC] [--hl LANG] [--page P] [--json] [--timeout S]`; exit 0 ok, 1 HTTP/timeout/malformed, 2 key missing. Python functions `build_payload(query, num=10, since=None, gl=None, hl=None, page=None, autocorrect=True) -> dict`, `endpoint(vertical) -> str`, `render(data, vertical) -> str`, `fetch(url, payload, key, timeout) -> dict`, `main(argv=None, fetcher=fetch) -> int`, constants `SETUP_LINE`, `EXIT_OK`, `EXIT_ERROR`, `EXIT_NO_KEY`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_websearch.py`:

```python
"""Tests for the research plugin's optional serper.dev backend script.

Stdlib only. The network is never touched: `main()` takes an injectable
fetcher, and the payload/render functions are pure.
"""
import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins" / "research" / "scripts" / "websearch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("websearch", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ws = load_module()

SAMPLE_SEARCH = {
    "searchParameters": {"q": "apple inc", "type": "search"},
    "answerBox": {"answer": "Cupertino", "title": "Apple HQ", "link": "https://example.com/hq"},
    "knowledgeGraph": {"title": "Apple", "type": "Company", "description": "Tech company"},
    "organic": [
        {"title": "Apple", "link": "https://www.apple.com/", "snippet": "Official site", "position": 1},
        {"title": "Apple Inc. news", "link": "https://news.example.com/a", "snippet": "Latest",
         "position": 2, "date": "Aug 20, 2026"},
    ],
    "peopleAlsoAsk": [{"question": "Who founded Apple?", "snippet": "Jobs, Wozniak, Wayne",
                       "link": "https://example.com/founders"}],
    "relatedSearches": [{"query": "apple stock"}],
}

SAMPLE_NEWS = {
    "news": [
        {"title": "Apple event", "link": "https://news.example.com/event", "snippet": "New devices",
         "date": "2 hours ago", "source": "Example News"},
    ]
}


def run_main(argv, env=None, fetcher=None):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, env if env is not None else {}, clear=True):
        with redirect_stdout(out), redirect_stderr(err):
            code = ws.main(argv, fetcher=fetcher or ws.fetch)
    return code, out.getvalue(), err.getvalue()


class PayloadTests(unittest.TestCase):
    def test_since_maps_to_tbs(self):
        payload = ws.build_payload("q", since="w")
        self.assertEqual(payload["tbs"], "qdr:w")

    def test_no_since_omits_tbs(self):
        self.assertNotIn("tbs", ws.build_payload("q"))

    def test_num_is_capped_at_100(self):
        self.assertEqual(ws.build_payload("q", num=500)["num"], 100)

    def test_optional_fields_only_when_given(self):
        payload = ws.build_payload("q", gl="it", hl="en", page=2)
        self.assertEqual((payload["gl"], payload["hl"], payload["page"]), ("it", "en", 2))
        self.assertNotIn("gl", ws.build_payload("q"))

    def test_endpoint_per_vertical(self):
        self.assertEqual(ws.endpoint("search"), "https://google.serper.dev/search")
        self.assertEqual(ws.endpoint("news"), "https://google.serper.dev/news")
        self.assertEqual(ws.endpoint("scholar"), "https://google.serper.dev/scholar")


class RenderTests(unittest.TestCase):
    def test_render_search_lists_organic_with_date_and_extras(self):
        text = ws.render(SAMPLE_SEARCH, "search")
        self.assertIn("1. Apple", text)
        self.assertIn("https://www.apple.com/", text)
        self.assertIn("Aug 20, 2026", text)
        self.assertIn("Answer box: Cupertino", text)
        self.assertIn("Knowledge graph: Apple", text)
        self.assertIn("Who founded Apple?", text)
        self.assertIn("apple stock", text)

    def test_render_news_uses_news_key(self):
        text = ws.render(SAMPLE_NEWS, "news")
        self.assertIn("Apple event", text)
        self.assertIn("Example News", text)
        self.assertIn("2 hours ago", text)

    def test_render_empty_says_no_results(self):
        self.assertIn("No results", ws.render({"organic": []}, "search"))


class MainTests(unittest.TestCase):
    def test_missing_key_exits_2_with_setup_line(self):
        code, out, err = run_main(["apple"], env={})
        self.assertEqual(code, ws.EXIT_NO_KEY)
        self.assertIn("SERPER_API_KEY", err)
        self.assertEqual(out, "")

    def test_fetcher_error_exits_1(self):
        def boom(url, payload, key, timeout):
            raise ws.FetchError("HTTP 429 Too Many Requests")
        code, out, err = run_main(["apple"], env={"SERPER_API_KEY": "k"}, fetcher=boom)
        self.assertEqual(code, ws.EXIT_ERROR)
        self.assertIn("429", err)

    def test_success_renders_text_and_passes_payload(self):
        seen = {}
        def ok(url, payload, key, timeout):
            seen.update(url=url, payload=payload, key=key, timeout=timeout)
            return SAMPLE_SEARCH
        code, out, err = run_main(["apple inc", "--since", "m", "--gl", "it"],
                                  env={"SERPER_API_KEY": "k"}, fetcher=ok)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertEqual(seen["url"], "https://google.serper.dev/search")
        self.assertEqual(seen["payload"]["q"], "apple inc")
        self.assertEqual(seen["payload"]["tbs"], "qdr:m")
        self.assertEqual(seen["payload"]["gl"], "it")
        self.assertEqual(seen["key"], "k")
        self.assertIn("1. Apple", out)

    def test_json_flag_prints_raw_response(self):
        code, out, err = run_main(["apple", "--json"], env={"SERPER_API_KEY": "k"},
                                  fetcher=lambda *a: SAMPLE_SEARCH)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertEqual(json.loads(out)["organic"][0]["link"], "https://www.apple.com/")

    def test_num_above_10_notes_credit_cost_on_stderr(self):
        code, out, err = run_main(["apple", "--num", "30"], env={"SERPER_API_KEY": "k"},
                                  fetcher=lambda *a: SAMPLE_SEARCH)
        self.assertEqual(code, ws.EXIT_OK)
        self.assertIn("2 credits", err)

    def test_news_vertical_hits_news_endpoint(self):
        seen = {}
        def ok(url, payload, key, timeout):
            seen["url"] = url
            return SAMPLE_NEWS
        code, out, err = run_main(["apple", "--vertical", "news"], env={"SERPER_API_KEY": "k"},
                                  fetcher=ok)
        self.assertEqual(seen["url"], "https://google.serper.dev/news")
        self.assertIn("Apple event", out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_websearch -v`
Expected: errors at import time (`FileNotFoundError` or `AttributeError`: the script does not exist yet).

- [ ] **Step 3: Write the script**

Create `plugins/research/scripts/websearch.py`:

```python
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
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_websearch -v`
Expected: all 14 tests `ok`. If `sys.stdout.buffer` makes the import fail under the test runner's captured stdout, wrap both `TextIOWrapper` lines in `if hasattr(sys.stdout, "buffer"):` guards (same intent as `webfetch.py`) and re-run.

- [ ] **Step 5: Smoke the CLI without a key**

Run: `python plugins/research/scripts/websearch.py "test" ; echo "exit=$?"`
Expected: the setup line on stderr and `exit=2`.

- [ ] **Step 6: Commit**

```bash
git add plugins/research/scripts/websearch.py tests/test_websearch.py
git commit -m "Add websearch.py, the optional serper.dev backend for research agents"
```

---

### Task 2: `web-search-techniques` skill: backends section

**Files:**
- Modify: `plugins/research/skills/web-search-techniques/SKILL.md`

**Interfaces:**
- Consumes: the `websearch.py` CLI from Task 1.
- Produces: section headers `## Search Backends`, `## Reading, Not Skimming` that Tasks 3-5 reference by name.

- [ ] **Step 1: Rewrite the frontmatter description**

Replace the `description:` block with:

```yaml
description: >
  Knowledge base for web research: query formulation, source authority ranking, the two search backends (native WebSearch, optional serper.dev through websearch.py), reading pages with WebFetch and the webfetch.py bot-block fallback, and the anti-loop rules. Used by quick-searcher, deep-researcher and /research:team-research.
  TRIGGER WHEN: performing web research with WebSearch, WebFetch, or the research plugin's scripts.
  DO NOT TRIGGER WHEN: searching a local codebase (use Grep or Glob directly).
```

- [ ] **Step 2: Replace the `## WebSearch Techniques` section with the backends section**

Replace the whole `## WebSearch Techniques` section (header through its last bullet) with:

```markdown
## Search Backends

Two backends produce candidate pages. Neither produces claims: only a page that was read does.

| Backend | When | How |
|---|---|---|
| Native `WebSearch` | Default. Always available when the tool is in the toolset | The tool call, with the operators below |
| serper.dev (Google) | `SERPER_API_KEY` is set, or `--backend serper` | `python ${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py "<query>" [--vertical search|news|scholar] [--num N] [--since h|d|w|m|y] [--gl CC] [--hl LANG] [--page P] [--json]` via Bash |

Selection rule (the lead decides once per run and writes it into every spawn prompt): `auto` means serper when the key is set, else native. The chosen backend is stated in the plan, in each researcher report and in the final report header. A run never silently falls back: if serper was forced and the key is missing the script exits 2 with the setup line, and the run stops there.

What serper earns its call for:
- `--vertical scholar` for academic threads, `--vertical news --since w|m` for recency threads
- `--num 30` to `50` on the orient round, to map a topic's vocabulary in one call (above 10 results costs 2 credits; the script says so on stderr)
- `--since` for "what changed lately" questions; `before:YYYY-MM-DD` / `after:YYYY-MM-DD` inside the query for exact windows
- Cross-index corroboration: a claim whose sources surface on both indexes ranks above one found on one index only

Operators both backends honour: `site:` (restrict to a domain), `"exact phrase"`, `-term` (exclude), `filetype:pdf`, a year token (`2026`) for temporal queries, `official` or `documentation` to bias toward primary sources, version numbers when relevant (`react 19`).

Cost note (checked 2026-08-23): serper.dev gives 2,500 free queries, then $1.00 per 1,000 on the entry plan, down to $0.30 per 1,000 at volume; credits are deducted only on successful responses. A `standard` run makes on the order of 50-80 calls, a `deep` run 150-300. Tavily and Exa are LLM-oriented alternatives (LLM-ready snippets, neural search) that would slot behind the same script interface; not built.

## Reading, Not Skimming

A search result is a candidate. A claim enters a researcher's ledger only from a page that was read:
1. `WebFetch` the page (prefer docs and primary sources; target anchors on long pages)
2. On a bot-block (403, 429, challenge page) or thin content (under ~200 useful characters), `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/webfetch.py <url>`
3. If the `playwright-skill` plugin is installed and the page is a primary source the answer depends on, drive a real browser with it as the last resort; if it is not installed, record the URL under limitations and move on. This is a pointer, not a dependency.
4. Record: URL, title, the date the page carries, authority rank (below), and the claims taken from it
```

- [ ] **Step 3: Keep the remaining sections and fix their wording**

Keep `## Query Formulation`, `## Source Authority Ranking`, `## WebFetch Guidance`, `## webfetch.py Fallback`, `## Anti-Loop Rules` as they are, with two edits: in the opening paragraph under `# Web Search Techniques`, replace "Shared knowledge base for `research:quick-searcher` and `research:deep-researcher`." with "Shared knowledge base for `research:quick-searcher`, `research:deep-researcher` and the `/research:team-research` lead."; replace every ` -- ` in the whole file with `: ` (the six ranked lines in `## Source Authority Ranking` and the two bullets in `## WebFetch Guidance`), so the file carries no dash-aside.

- [ ] **Step 4: Verify**

Run: `grep -n -- " -- \|—" plugins/research/skills/web-search-techniques/SKILL.md`
Expected: no output.
Run: `python scripts/lint_bundled_paths.py`
Expected: passes (the `${CLAUDE_PLUGIN_ROOT}` form is the accepted one).

- [ ] **Step 5: Commit**

```bash
git add plugins/research/skills/web-search-techniques/SKILL.md
git commit -m "Teach web-search-techniques the two search backends and the read-not-skim rule"
```

---

### Task 3: `deep-researcher`, the iterative investigator

**Files:**
- Modify: `plugins/research/agents/deep-researcher.md` (full rewrite)

**Interfaces:**
- Consumes: the spawn block fields `Role`, `Objective`, `Boundaries`, `Source families`, `Domain hint`, `Backend`, `Budget`, `Return format` (written by the lead in Task 5); `websearch.py` from Task 1; skill sections from Task 2.
- Produces: the researcher report format (`## Researcher report: <sub-question>` with `Exit reason`, `Rounds`, `### Claims`, `### Sources read`, `### Contradictions seen`, `### Open threads`, `### Searched and not found`) that Task 5's lead parses and Task 9's evals assert on.

- [ ] **Step 1: Replace the file with this content**

````markdown
---
name: deep-researcher
description: >
  Iterative web investigator for one research sub-question: orients with broad queries, reads the pages that matter, keeps a ledger of claims with sources and dates, narrows round by round and stops at saturation, then returns a compressed cited report. The worker that /research:team-research spawns in parallel, one per sub-question; also usable alone for a single focused investigation.
  TRIGGER WHEN: spawned by /research:team-research with a spawn block, or the user asks for one question to be investigated in depth across several sources with citations.
  DO NOT TRIGGER WHEN: the question is a single-fact lookup (use quick-searcher), the user wants a whole multi-question research run with a plan and a report file (use /research:team-research), the task is about local code or files, or the user is implementing or editing code.
tools: Read, WebSearch, WebFetch, Bash
model: inherit
color: pink
---

# ROLE

Investigator for ONE sub-question. You search, read, keep a ledger, and return a compressed report with every claim sourced. You never orchestrate: the lead that spawned you owns the plan, the other sub-questions and the synthesis.

Load `research:web-search-techniques` first: backends, operators, authority ranking, reading rules, anti-loop. Do not duplicate it here.

# INPUT

Two ways in:

- **Spawned by the lead**: the prompt carries a spawn block (`Role`, `Objective`, `Boundaries`, `Source families`, `Domain hint`, `Backend`, `Budget`, `Return format`). Follow it literally.
- **Direct invocation**: no spawn block. Treat the user's question as the objective, no boundaries, backend `auto` (serper if `SERPER_API_KEY` is set, else `WebSearch`), budget `15 searches / 12 pages / 4 rounds`, and return the same report format.

Budget is a planning-time cap: plan queries before launching them; do not count runtime calls one by one.

# THE LOOP

## 1. Orient (round 1)

- 2-3 broad, short queries that map the terrain: the vocabulary, the obvious primary sources, the competing claims
- With serper: one `--num 30` call on the main phrasing does most of this; add `--vertical scholar` when the objective names a research question, `--vertical news --since m` when it is about what changed
- Note the 3-6 pages worth reading now

## 2. Read

- Read the pages that matter, per the skill's reading rules (`WebFetch`, then `webfetch.py` on a block, browser only when `playwright-skill` is installed and the page is load-bearing)
- A page enters the ledger only after it is read. A snippet is a pointer, never a claim
- On entry record: URL, title, the date the page carries, authority rank 1-5, and each claim taken, as one sentence with numbers carrying date and unit

## 3. Ledger (after every round)

Keep it private; it is the material for the final report.

```
Claims: <id> <claim> [S<n>...]
Sources: S<n> <title> | <site> | <date> | <URL> | rank
Contradictions: <claim> [S<a>] vs <claim> [S<b>]
Open threads: <what surfaced, not yet pursued>
Queries tried: <query> -> <useful | nothing>
```

## 4. Narrow (rounds 2..R)

- Next queries come from open threads and from vocabulary found in read pages, not from the original phrasing again
- Never repeat a query; after 2 empty attempts on a thread, pivot or drop it and log it under searched-and-not-found
- Stay inside `Boundaries`: a thread that belongs to a neighbouring sub-question goes to `Open threads` with one line, unread
- Prefer a primary source over a secondary one stating the same thing; keep both when they disagree

## 5. Stop

Stop when ANY holds, and name which in `Exit reason`:

| Exit reason | Condition |
|---|---|
| `saturated` | Two consecutive rounds added no new claim, or every load-bearing claim has 2+ independent sources (different sites) |
| `budget-exhausted` | Searches, pages or rounds reached the cap |
| `target-not-found` | The objective could not be answered from what exists online within budget |
| `error` | Tools unavailable or every fetch failed; say which |

## 6. Compress

Return the report below and nothing else. Raw page text never goes back to the lead.

# SOURCE QUALITY

Apply the skill's authority ranking before a source enters the ledger. Discard SEO farms, AI rewrites and scraped aggregators on sight. When two sources agree, record both ids on the claim: independent agreement is what the lead's confidence grading reads. Two pages on the same site count as one source.

# RETURN FORMAT

```
## Researcher report: <sub-question>
Exit reason: saturated | budget-exhausted | target-not-found | error
Rounds: R, searches: N, pages read: M, backend: websearch | serper

### Claims
1. <claim, one sentence> [S1][S3]
2. ...

### Sources read
| id | title | site | date carried | URL | rank |
|---|---|---|---|---|---|
| S1 | ... | ... | ... | ... | 1 |

### Contradictions seen
- <claim A> [S2] vs <claim B> [S5]: <which is later / primary / more specific, or unresolved>

### Open threads
- <what surfaced that this report did not pursue, and why (boundary, budget)>

### Searched and not found
- <queries or sources that returned nothing useful; paywalled or bot-blocked URLs>
```

Rules for the report:
- Every claim carries at least one `[S<n>]`; a claim with no read source is not a claim, it is an open thread
- `Sources read` lists only pages actually read, each once
- Dates are the date the page carries, not today's date; write `undated` when the page has none
- Keep it under ~1,500 words at `standard`, ~2,500 at `deep`: the lead reads up to twelve of these

# FAILURE RESPONSE

If you cannot run at all, return:

```
## Researcher report: <sub-question>
Exit reason: error
Reason: <one line: tool missing, every fetch blocked, key missing for forced serper>
Tools available: <list>
```

No apology, no partial prose: the lead needs the structured signal to re-spawn or record the gap.

# ANTI-LOOP

- Never the same query twice, in either backend
- 2 empty attempts on a thread, then pivot or drop
- Never fetch the same URL twice
- When `websearch.py` exits non-zero, do not retry it; continue with `WebSearch` if the backend was `auto`, stop with `error` if it was forced `serper`
````

- [ ] **Step 2: Verify conventions**

Run: `grep -n -- " -- \|—\|agent-teams\|quick-searcher sub-agents\|Mode A\|Mode B" plugins/research/agents/deep-researcher.md`
Expected: no output.
Run: `python scripts/lint_plugin_registration.py && python scripts/lint_bundled_paths.py`
Expected: both pass.

- [ ] **Step 3: Commit**

```bash
git add plugins/research/agents/deep-researcher.md
git commit -m "Rebuild deep-researcher as an iterative single-sub-question investigator"
```

---

### Task 4: `quick-searcher`: direct mode plus verifier mode

**Files:**
- Modify: `plugins/research/agents/quick-searcher.md` (full rewrite)

**Interfaces:**
- Consumes: verifier spawn block fields `Role: verifier`, `Claim A`, `Source A`, `Claim B`, `Source B`, `Budget` (written by the lead in Task 5).
- Produces: the verifier report (`## Verifier report` with `Ruling`, `Third source`, `Confidence`) that Task 5 folds into the contradictions section.

- [ ] **Step 1: Replace the file with this content**

````markdown
---
name: quick-searcher
description: >
  Lite web search agent for single-fact lookups and quick web answers on any topic; also the verifier /research:team-research spawns to settle one contested claim with a third independent source.
  TRIGGER WHEN: the user asks for a single fact, definition, stat, URL, or quick confirmation answerable by 1-3 web searches from one source; or spawned with a verifier block.
  DO NOT TRIGGER WHEN: the question needs synthesis across 3+ sources (use deep-researcher or /research:team-research), the task is about local code or files, or the user is implementing or editing code.
tools: Read, WebFetch, WebSearch, Bash
model: sonnet
color: pink
---

# ROLE

Fast-track web searcher. Two modes:
- **Direct mode**: user-invoked, one-fact lookup. 3-10 tool calls. Lead with the answer.
- **Verifier mode**: spawned by the `/research:team-research` lead with a verifier block. Settle one contested claim with a third, independent source.

Priority: speed over exhaustiveness. One good source beats five mediocre rounds.

Load `research:web-search-techniques` for operators, backends, source ranking, reading rules and the `webfetch.py` fallback. Do not duplicate it here.

# DIRECT MODE

1. Identify the single core fact needed
2. Pick the most direct path: search for discovery, `WebFetch` for extraction; with `SERPER_API_KEY` set, `python ${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py "<query>"` is an equivalent discovery step
3. Execute 1-3 focused searches, read the one page that answers
4. Return the answer with source URL, the date the page carries, and access date

Target: 3-10 tool calls total. Past 10, deliver what you have and flag the gap. If the question turns out to need several sources or angles, say so: the caller may run `/research:team-research`.

# VERIFIER MODE

Activated by a prompt of this shape:

```
Role: verifier
Claim A: <one sentence> (Source A: <URL>, <date>)
Claim B: <one sentence> (Source B: <URL>, <date>)
Backend: websearch | serper
Budget: 5 searches / 3 pages
Return format: verifier report
```

Rules:
- Find a THIRD source on a different site from A and B, primary where possible (official docs, spec, vendor page, dataset, paper)
- Read it; do not rule from a snippet
- Prefer the later and the more primary source when they conflict, and say which rule you applied
- If no third source settles it within budget, rule `unsettled` and say what would settle it
- Never re-read A or B as the third source

Return format:

```
## Verifier report
Claim A: <as received>
Claim B: <as received>
Ruling: A stands | B stands | both hold (different scope: <how>) | unsettled
Third source: <title>, <site>, <date carried>, <URL>, rank <1-5>
Reason: <one or two sentences: later, primary, more specific, or why unsettled>
Confidence: high | medium | low
Budget used: ~N searches / M pages
```

# TOOL QUICK REFERENCE

- **WebSearch**: discovery. Broad first, then narrow. Operators in the shared skill.
- **WebFetch**: extraction. Docs and primary sources first.
- **Bash**: only for `${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py` (serper backend) and `${CLAUDE_PLUGIN_ROOT}/scripts/webfetch.py` (bot-block fallback).
- **Read**: for re-opening locally saved fetches, never for codebase search.

# ANTI-LOOP

Never repeat the exact same query. If a search returns nothing:
- Change terminology
- Broaden the query
- Switch to a different authoritative domain via `site:`
- After 2 failed attempts on the same sub-topic, stop and report the gap

# OUTPUT

Direct mode: lead with the answer; source URL, page date, access date; confidence if uncertain; flag when the question needs a deeper run.

Verifier mode: the verifier report above, exactly.
````

- [ ] **Step 2: Verify conventions**

Run: `grep -n -- " -- \|—\|Sub-unit\|angle" plugins/research/agents/quick-searcher.md`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add plugins/research/agents/quick-searcher.md
git commit -m "Give quick-searcher a verifier mode and drop the angle sub-unit mode"
```

---

### Task 5: `/research:team-research`, the lead

**Files:**
- Modify: `plugins/research/commands/team-research.md` (full rewrite)

**Interfaces:**
- Consumes: `deep-researcher` spawn block and report (Task 3), `quick-searcher` verifier block and report (Task 4), `websearch.py` (Task 1), skill sections (Task 2).
- Produces: the report file layout and the companion file name `<stem>.researchers.md` that Tasks 7 and 9 describe and assert on.

- [ ] **Step 1: Replace the file with this content**

````markdown
---
description: "Deep web research run: clarify scope only when needed, show a plan of sub-questions for approval, spawn one iterative researcher per sub-question in parallel, verify contradictions, synthesize a long-form cited report and write it to disk. Web only."
argument-hint: "\"<question>\" [--depth auto|quick|standard|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto|websearch|serper] [--domain <hint>]"
---

# Team Research

You are the lead of a deep web research run. You clarify, plan, delegate, cross-check, synthesize and deliver. You do not search during the waves: researchers do.

**This command researches the web, and only the web.** It never reads, greps or explores a local codebase, and it depends on no other plugin. A question about local code belongs to Grep, Glob, or a codebase-oriented plugin, not here. Say so and stop if the question is about local code.

Load `research:web-search-techniques` before planning: it names the two backends, the operators and the reading rules the spawn blocks refer to.

## Flags

| Flag | Default | Meaning |
|---|---|---|
| `--depth` | `auto` | `auto` picks the tier from the question (Tiers below); `quick`, `standard`, `deep` force it |
| `--no-clarify` | off | Skip Phase 1; the plan gate still runs |
| `--auto` | off | Skip both gates: print the plan and run. For unattended use |
| `--out` | `research/<YYYY-MM-DD>-<slug>.md` under the current working directory | A file path, or a directory (the default filename goes inside it) |
| `--backend` | `auto` | `auto`: serper when `SERPER_API_KEY` is set, else native `WebSearch`; `serper` forces serper (stops with the setup line when the key is missing); `websearch` forces native search |
| `--domain` | detected | Free-form hint (security, law, finance, nutrition, anything) shaping vocabulary, source families and the synthesis persona |

Slug: the restated question, lowercased, ASCII letters and digits with hyphens, at most 60 characters.

## Tiers

| Tier | `auto` picks it when | Researchers | Pages read (target) | Waves | Per-researcher budget (searches / pages / rounds) |
|---|---|---|---|---|---|
| `quick` | One well-defined question with a small number of authoritative answers | 1-2 | ~10 | 1 | 8 / 6 / 2 |
| `standard` | A comparison, a "how do people do X", a bounded survey | 3-5 | 30-60 | 1 + verifiers | 15 / 12 / 4 |
| `deep` | Open-ended, multi-faceted, decision-grade, or the user says thorough / exhaustive | 6-12 across two waves | 100+ | 2 + verifiers | 25 / 20 / 6 |

A one-fact question (single answer, one source suffices) is not a tier: spawn `research:quick-searcher` directly in direct mode, print its answer, and say that no research run was needed.

## Phase 0: Pre-flight

1. Parse `$ARGUMENTS` into the question and the flags above.
2. Backend: if `--backend serper` or (`auto` and `SERPER_API_KEY` is set in the environment), the backend is `serper`; otherwise `websearch`. Check `serper` works before planning: `python ${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py "test" --num 1`; exit 2 means no key (stop with its setup line if serper was forced; fall to `websearch` only when `auto`), exit 1 means the service failed (same rule).
3. If the backend is `websearch` and `WebSearch` is not in your toolset, stop: "No search backend available: WebSearch is not in this session's toolset and SERPER_API_KEY is not set."
4. If the question is about local code, stop and say so.

## Phase 1: Clarify

Skipped by `--no-clarify` and `--auto`.

Read the question for what is genuinely open: scope; audience and purpose (decision, overview, teaching); time window; geography or jurisdiction; what a good answer looks like (facts, comparison table, recommendation). If at least one is open, ask 2-4 questions in ONE `AskUserQuestion` call, multiple choice where possible, and fold the answers into the restated question. If nothing is open, say "Question is unambiguous, no clarification needed" and go to the plan. Never ask for the sake of asking.

## Phase 2: Plan

Write the plan:

```
## Research plan
Question (restated): <one sentence>
Tier: quick | standard | deep (<one-line reason>)
Backend: websearch | serper (<approx. call count when serper>)
Output: <path>

Sub-questions:
1. <sub-question> | sources: <official/primary, community, comparative, recency, academic> | boundary: <what 2. covers, not this>
2. ...

Researchers: <N> in wave 1 (<one per sub-question, or which share one at quick>)
Estimated pages read: <range>   Estimated time: <range>
```

Unless `--auto`, present it with `AskUserQuestion`: options `Approve`, `Change depth`, `Edit the plan` (free text; merge it, re-show once, then run). With `--auto`, print the plan and continue. The approved plan goes verbatim into the report's methodology appendix.

## Phase 3: Wave 1

Spawn one `research:deep-researcher` per sub-question, **all in a single message** (parallel). Each prompt is exactly this block, filled:

```
Role: researcher (wave 1)
Objective: <the sub-question as one paragraph, with what a complete answer contains>
Boundaries: <what the neighbouring sub-questions cover; do not investigate it>
Source families: <in priority order>
Domain hint: <--domain or detected>
Backend: websearch | serper   (serper: python ${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py ...)
Budget: <N> searches / <M> pages read / <R> rounds
Return format: the researcher report (## Researcher report, Exit reason, Rounds, ### Claims, ### Sources read, ### Contradictions seen, ### Open threads, ### Searched and not found), nothing else
```

Do not search yourself during the wave.

## Phase 4: Gap analysis

Read every report. Build three lists:
- **Contradictions**: claims that conflict across researchers, or inside one report
- **Thin or uncovered**: exit reason `budget-exhausted`, `target-not-found` or `error`; or a load-bearing claim with fewer than two independent sources
- **New threads**: open threads the plan did not anticipate and the question needs

Then, by tier:
- `quick`: no second wave; everything goes to limitations.
- `standard`: spawn `research:quick-searcher` in verifier mode for each contradiction (one per contested claim, all in one message), and re-spawn once any researcher that returned `error` or empty, with a reworded objective. New threads go to limitations.
- `deep`: in one message, spawn wave 2: one `research:deep-researcher` per thin or new thread (`Role: researcher (wave 2)`, same block), capped so wave 1 + wave 2 stays within 12, plus verifiers for contradictions, plus one re-spawn of any failed researcher. Wave 2 is the last wave.

Verifier block:

```
Role: verifier
Claim A: <one sentence> (Source A: <URL>, <date>)
Claim B: <one sentence> (Source B: <URL>, <date>)
Backend: websearch | serper
Budget: 5 searches / 3 pages
Return format: verifier report
```

If more than half the researchers of a wave failed, stop: print which failed and why, and do not synthesize.

## Phase 5: Synthesis

Write the report from the researcher and verifier reports only, in prose. Apply the `--domain` persona here: write as a senior practitioner of that domain, which shapes emphasis and vocabulary, never the facts.

```
# <Question as finally scoped>

Date: <YYYY-MM-DD> | Tier: <tier> | Researchers: <n wave 1> + <n wave 2> + <n verifiers> | Pages read: <sum> | Backend: <backend> | Wall time: <approx> | Citation check: done

## Executive summary
<5-10 sentences: the answer, overall confidence high|medium|low and the one-line reason>

## Key findings
1. <one sentence> [n][m]
...

## <One section per sub-question>
<prose; a table for comparisons; numbers with date and unit; disagreements written out with both citations and the resolution>

## Contradictions and resolutions
- <claim A> [a] vs <claim B> [b]: <verifier ruling or reasoning>

## Confidence and limitations
- Rests on one source: ...
- Could not be verified: ...
- Out of scope: ...
- Paywalled or bot-blocked: <URLs>

## Sources
[1] <title>, <site>, <date carried>, <URL>, rank <1-5>
...

## Methodology
<the approved plan verbatim; per researcher: objective, exit reason, budget used, queries compressed; failures and re-spawns>
```

Length by tier: quick 1-2 pages, standard 4-8, deep 10-25. Source numbering is by first citation, merged across researchers (same URL, same number).

## Phase 6: Citation check

One pass over the draft against the merged source table:
- Every factual claim carries at least one `[n]` resolving to a source some researcher read
- A claim with no resolvable source is rewritten as explicitly unverified or moved to limitations; never silently kept
- Every `[n]` in Sources is cited at least once
- Dates and numbers in the text match their source row

Record "Citation check: done" in the header only after this pass.

## Phase 7: Deliver

1. Resolve `--out`: a directory gets `<YYYY-MM-DD>-<slug>.md` inside it; no flag means `research/<YYYY-MM-DD>-<slug>.md` under the current working directory. Create the directory.
2. Write the report file.
3. Write the companion `<stem>.researchers.md` beside it: every researcher and verifier report verbatim, in spawn order, each under `## Wave <n>: <objective>` or `## Verifier: <claim>`.
4. Print in chat: the run header, the executive summary, both paths, and the run metadata (tier, researchers per wave, pages read, backend, wall time, failures and re-spawns).
5. If the file cannot be written, print the whole report in chat and say why.

## Failure rules

- Researcher `error` or empty: recorded in Methodology; one re-spawn with a reworded objective (standard and deep); then a gap in limitations.
- More than half of a wave failed: stop and report, no synthesis.
- `--backend serper` without a key, or serper failing at pre-flight: stop with the script's message.
- No search backend at all: stop at pre-flight.
- Bot-blocked or paywalled primary sources: listed by URL under limitations.

## Examples

```
/research:team-research "Best practices for WebSocket reconnection in 2026"
/research:team-research "GDPR retention rules for transaction logs" --domain law --depth deep
/research:team-research "Should we migrate from REST to gRPC?" --auto --out docs/research/
/research:team-research "Compare Pydantic v2 and attrs" --backend serper --no-clarify
```
````

- [ ] **Step 2: Verify no forbidden references remain**

Run: `grep -n -- "agent-teams\|CLAUDE_CODE_EXPERIMENTAL\|TaskCreate\|TaskList\|shutdown_request\|angle\| -- \|—" plugins/research/commands/team-research.md`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add plugins/research/commands/team-research.md
git commit -m "Restructure /research:team-research into the clarify-plan-wave-cite-deliver lead"
```

---

### Task 6: Registry: versions, description, dependencies

**Files:**
- Modify: `.claude-plugin/marketplace.json` (the `research` entry and `metadata.version`)

- [ ] **Step 1: Edit the `research` entry**

In the `research` plugin object:
- `"description"` becomes: `"Deep web research (any topic) modelled on the commercial deep-research products: /research:team-research clarifies scope only when needed, shows a plan of sub-questions for approval, spawns one iterative deep-researcher per sub-question in parallel, verifies contradictions with quick-searcher, synthesizes a long-form cited report and writes it to disk; tiers quick/standard/deep scale effort; optional serper.dev backend via websearch.py when SERPER_API_KEY is set, native WebSearch otherwise. quick-searcher (sonnet) also answers single-fact lookups directly"`
- `"version"` `"5.0.0"` -> `"6.0.0"`
- `"dependencies"` -> `[]`
- Add `"serper"` and `"citations"` to `keywords`.

- [ ] **Step 2: Bump the marketplace version**

`metadata.version` `"24.1.0"` -> `"25.0.0"`.

- [ ] **Step 3: Verify**

Run: `python -c "import json;d=json.load(open('.claude-plugin/marketplace.json'));p=[x for x in d['plugins'] if x['name']=='research'][0];print(d['metadata']['version'],p['version'],p['dependencies'])"`
Expected: `25.0.0 6.0.0 []`.
Run: `python scripts/lint_dependency_graph.py && python scripts/lint_plugin_registration.py && python scripts/check_version_bumps.py origin/master HEAD`
Expected: all pass (the version check sees the plugin change and both bumps in the range).

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "Release research 6.0.0 without the agent-teams dependency (marketplace 25.0.0)"
```

---

### Task 7: Documentation: CLAUDE.md, README, docs/plugins, CHANGELOG

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `docs/plugins/research.md` (full rewrite)
- Modify: `exports/vscode/CHANGELOG.md` (new top section)

- [ ] **Step 1: CLAUDE.md, three edits**

(a) In the paragraph beginning "The same policy applies to the team pipelines:", replace

`/senior-review:team-review`, `/codebase-xray:team-analyze`, `/codebase-mapper:team-codebase-map`, and `/research:team-research` declare the upstream `agent-teams` plugin (wshobson/agents) as a hard prerequisite in their Prerequisites blocks, and as of marketplace 13.2.0 all four owning plugins also declare it

with

`/senior-review:team-review`, `/codebase-xray:team-analyze`, and `/codebase-mapper:team-codebase-map` declare the upstream `agent-teams` plugin (wshobson/agents) as a hard prerequisite in their Prerequisites blocks, and as of marketplace 13.2.0 all three owning plugins also declare it

and replace "The four pipelines and the `senior-review:review-quality-gates` skill are local content with no upstream sync." with "The three pipelines, `/research:team-research` (which dropped agent-teams in marketplace 25.0.0 and runs on plain subagents) and the `senior-review:review-quality-gates` skill are local content with no upstream sync."

(b) Replace the whole paragraph beginning "**`research` is a web-research tool and nothing else, as of research 5.0.0 (marketplace 21.3.0).**" with:

**`research` is a web-research tool and nothing else, as of research 5.0.0 (marketplace 21.3.0), and as of research 6.0.0 (marketplace 25.0.0) it depends on nothing at all.** It reads no local codebase, spawns no agent from another local plugin, and declares no dependency, local or cross-marketplace. `/research:team-research` is the lead of a deep-research run modelled on the commercial products (design in `docs/superpowers/specs/2026-08-23-research-deep-research-parity-design.md`): it clarifies scope only when the question is ambiguous, shows a plan of sub-questions for approval (`--auto` skips both gates), spawns one `research:deep-researcher` per sub-question in parallel through the plain `Agent` tool, runs `research:quick-searcher` verifiers on contradictions and a targeted second wave at `--depth deep`, synthesizes a long-form cited report, runs a citation check, and writes the report plus a `<stem>.researchers.md` companion of raw researcher reports to `research/<date>-<slug>.md` (or `--out`). The old fixed source angles survive only as a per-sub-question source-family checklist; the unit of work is the sub-question. Search runs through native `WebSearch` or, when `SERPER_API_KEY` is set, `scripts/websearch.py` (serper.dev, Google index, `news`/`scholar` verticals, date filters): optional, never required, always stated in the plan and the report header. The `agent-teams@claude-code-workflows` dependency and the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` prerequisite are gone; do not reintroduce them, and do not re-add a codebase dimension: a question about local code belongs to Grep, Glob, or a codebase-oriented plugin. `evals/research/` holds eight behavioural-invariant cases for this pipeline (plan shown before any search, no citation outside the sources table, every source actually read, backend stated, tier bands respected).

(c) In the `docs/plugins/` paragraph, after "`evals/ai-tooling/` is a different shape, ... keeps its case forever.", append: " `evals/research/` follows the `ai-tooling` shape for the deep-research pipeline (marketplace 25.0.0)."

- [ ] **Step 2: README.md, three edits**

(a) Row for `research` in the plugin table: description becomes "Deep web research with clarification, plan approval, parallel iterative researchers, citation check and a report file; quick single-fact lookups; optional serper.dev backend". Counts stay `2 | 1 | 1`.

(b) In the Mermaid dependency graph, delete the line `    research --> agentteams`.

(c) In the agent-teams section: replace "The four pipelines this marketplace built on top of the old `agent-teams` plugin were relocated rather than removed. Their commands live locally, but each of the four plugins declares" with "The three pipelines this marketplace built on top of the old `agent-teams` plugin were relocated rather than removed (the fourth, `/research:team-research`, dropped the dependency in marketplace 25.0.0 and runs on plain subagents). Their commands live locally, but each of the three plugins declares"; and change the bullet `- `/agent-teams:team-research` -> [`/research:team-research`](docs/plugins/research.md)` to `- `/agent-teams:team-research` -> [`/research:team-research`](docs/plugins/research.md) (no longer needs agent-teams)`. In the paragraph under the graph, replace "`research` depends on no local plugin at all, deliberately: it researches the web and nothing else." with "`research` depends on nothing at all, deliberately: it researches the web and nothing else."

- [ ] **Step 3: Rewrite `docs/plugins/research.md`**

````markdown
# Research Plugin

> Deep web research modelled on the commercial deep-research products (clarify, plan, parallel iterative researchers, citation check, report file), plus quick single-fact lookups. Web only: it reads no local codebase and depends on nothing.

## Command

### `/research:team-research`

| | |
|---|---|
| **Invoke** | `/research:team-research "<question>" [--depth auto\|quick\|standard\|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto\|websearch\|serper] [--domain <hint>]` |
| **Writes** | `research/<YYYY-MM-DD>-<slug>.md` (or `--out`) and `<stem>.researchers.md` beside it |

Phases: pre-flight (backend detection), clarify (2-4 questions in one call, only when the question is ambiguous; `--no-clarify` skips), plan (sub-questions with source families and boundaries, shown for approval; `--auto` skips both gates), wave 1 (one `deep-researcher` per sub-question, parallel), gap analysis (verifiers on contradictions; at `deep` a targeted wave 2), synthesis (long-form report in prose), citation check (every claim resolves to a source a researcher read), deliver (file + companion + chat summary).

| Tier | Researchers | Pages read | Waves | Per-researcher budget |
|---|---|---|---|---|
| `quick` | 1-2 | ~10 | 1 | 8 searches / 6 pages / 2 rounds |
| `standard` | 3-5 | 30-60 | 1 + verifiers | 15 / 12 / 4 |
| `deep` | 6-12 | 100+ | 2 + verifiers | 25 / 20 / 6 |

`auto` picks the tier from the question; a one-fact question is answered by `quick-searcher` directly with no run. Report sections: run header, executive summary, key findings, one section per sub-question, contradictions and resolutions, confidence and limitations, sources (only pages actually read), methodology (the approved plan verbatim, per-researcher budgets and exit reasons).

```
/research:team-research "Best practices for WebSocket reconnection in 2026"
/research:team-research "GDPR retention rules for transaction logs" --domain law --depth deep
/research:team-research "Should we migrate from REST to gRPC?" --auto --out docs/research/
```

## Agents

### `deep-researcher`

Iterative investigator for one sub-question: orient with broad queries, read the pages that matter, keep a ledger (claims, sources with dates and authority rank, contradictions, open threads), narrow round by round, stop at saturation or budget, return a compressed cited report. Spawned by the command; directly invokable for one focused investigation.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, WebSearch, WebFetch, Bash |

### `quick-searcher`

Single-fact lookups (1-3 searches, lead with the answer) and the verifier the command spawns to settle one contested claim with a third independent source.

| | |
|---|---|
| **Model** | `sonnet` |
| **Tools** | Read, WebFetch, WebSearch, Bash |

## Skill

### `web-search-techniques`

Query formulation, source authority ranking, the two search backends, reading rules (WebFetch, then `webfetch.py` on a bot-block, browser only if `playwright-skill` happens to be installed), anti-loop rules. Loaded by both agents and the command.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/websearch.py` | Optional serper.dev backend. Used when `SERPER_API_KEY` is set or `--backend serper`; `--vertical search\|news\|scholar`, `--num`, `--since h\|d\|w\|m\|y`, `--gl`, `--hl`, `--json`. Exit 2 with a setup line when the key is missing, 1 on HTTP errors. Stdlib only |
| `scripts/webfetch.py` | Bot-block fallback fetcher (Chrome TLS impersonation via curl_cffi, httpx fallback) |

Backend rule: `auto` uses serper when the key is set, native `WebSearch` otherwise; the choice is stated in the plan, in each researcher report and in the report header. Serper never replaces reading: snippets qualify a page for fetching, only read pages are cited.

---

**Related:** [digital-marketing](digital-marketing.md) (SEO research and content strategy) | [learning](learning.md) (turn findings into a mind map)
````

- [ ] **Step 4: CHANGELOG section**

Insert at the top of `exports/vscode/CHANGELOG.md`, above `## 24.1.0`:

```markdown
## 25.0.0

- `research` 6.0.0 brings `/team-research` to the shape of the commercial deep-research products. The prompt, driven by `research-orchestrator`, clarifies scope only when the question is ambiguous, shows a plan of sub-questions for approval (`--auto` skips both gates), dispatches one `deep-researcher` per sub-question in parallel, verifies contradictions with `quick-searcher`, runs a targeted second wave at `--depth deep`, synthesizes a long-form report with inline citations, checks that every claim resolves to a page a researcher actually read, and writes the report to `research/<date>-<slug>.md` (or `--out`) with a companion file of the raw researcher reports. Tiers `quick` / `standard` / `deep` scale researchers (1-2 / 3-5 / 6-12) and pages read (~10 / 30-60 / 100+).
- `deep-researcher` is now an iterative single-sub-question investigator (orient, read, ledger, narrow, stop at saturation) returning a compressed cited report; its old self-orchestrating angle mode is gone. `quick-searcher` keeps single-fact lookups and gains a verifier mode that settles one contested claim with a third independent source.
- New optional search backend: `websearch.py` (stdlib only) queries serper.dev when `SERPER_API_KEY` is set, adding Google's index, the `news` and `scholar` verticals and date filters. Never required: without the key the native search tool is used, and the backend in use is stated in the plan and in the report header. `web-search-techniques` documents both backends and the read-not-skim rule.
- The `research` bundle no longer references the experimental agent-teams flow at all; the Claude Code source dropped its `agent-teams` dependency and now depends on nothing.
```

- [ ] **Step 5: Verify**

Run: `grep -n "research --> agentteams" README.md; grep -n "all four owning plugins" CLAUDE.md; grep -n -- " -- \|—" docs/plugins/research.md`
Expected: no output from any of the three.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md README.md docs/plugins/research.md exports/vscode/CHANGELOG.md
git commit -m "Document research 6.0.0: dependency-free deep-research pipeline and the serper backend"
```

---

### Task 8: VS Code export twins

**Files:**
- Modify: `exports/vscode/research/.github/agents/deep-researcher.agent.md`
- Modify: `exports/vscode/research/.github/agents/quick-searcher.agent.md`
- Modify: `exports/vscode/research/.github/agents/research-orchestrator.agent.md`
- Modify: `exports/vscode/research/.github/prompts/team-research.prompt.md`
- Modify: `exports/vscode/research/.github/skills/web-search-techniques/SKILL.md`
- Created by the mirror script: `exports/vscode/research/.github/skills/web-search-techniques/scripts/websearch.py`

**Interfaces:**
- Consumes: the five source files from Tasks 2-5 (read them from disk; they are the text to adapt).
- Produces: a bundle that passes `check_export.py` and `mirror_export.py --check --since`.

Adaptation rules (from the `downstream-exports` skill), applied to every file:

| Source | Export |
|---|---|
| `WebSearch` | `#websearch` in prose, `websearch` in `tools:` |
| `WebFetch` | `#web/fetch` in prose, `web/fetch` in `tools:` |
| `Bash` | `execute/runInTerminal` in `tools:`; in prose "run in the terminal" |
| `Read` | `read/readFile` |
| `AskUserQuestion` | `#vscode/askQuestions` |
| `Agent` tool spawning `research:deep-researcher` | `#agent/runSubagent` with agent `deep-researcher` |
| `research:quick-searcher` / `research:deep-researcher` / `research:web-search-techniques` | `quick-searcher` / `deep-researcher` / `web-search-techniques` |
| `/research:team-research` | `/team-research` |
| `${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py` | `$SKILLS/web-search-techniques/scripts/websearch.py` (same for `webfetch.py`), with the `$SKILLS` definition paragraph in every file that uses it |
| `TRIGGER WHEN: x` / `DO NOT TRIGGER WHEN: y` | `Use when x` / `Not for y` (fix grammar: "Not for a single-fact lookup ...", never "Not for the question is ...") |
| `model:` / `color:` | dropped |
| `playwright-skill` plugin pointer | "if a browser-automation MCP server is configured" |
| "Claude Code" as actor | "the agent" |

`$SKILLS` definition paragraph (verbatim, first use in each file):

> `$SKILLS` is the installed skills directory: the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists.

- [ ] **Step 1: `deep-researcher.agent.md`**

Frontmatter:

```yaml
---
name: deep-researcher
description: >
  Iterative web investigator for one research sub-question: orients with broad queries, reads the
  pages that matter, keeps a ledger of claims with sources and dates, narrows round by round and
  stops at saturation, then returns a compressed cited report. The worker /team-research dispatches
  in parallel, one per sub-question; also usable alone for a single focused investigation. Use when
  dispatched by /team-research with a spawn block, or when the user asks for one question to be
  investigated in depth across several sources with citations. Not for a single-fact lookup (use
  quick-searcher), a whole multi-question research run with a plan and a report file (use
  /team-research), local code or files (use `#search/textSearch`, `#search/fileSearch`), or
  implementing or editing code.
user-invocable: true
tools:
  - read/readFile
  - execute/runInTerminal
  - execute/getTerminalOutput
  - web/fetch
  - websearch
agents: []
---

<!-- Vendored from plugins/research/agents/deep-researcher.md in acaprino/claude-code-daodan, MIT. -->
```

Body: the body of `plugins/research/agents/deep-researcher.md` with the table above applied, the `$SKILLS` paragraph inserted before the first `$SKILLS` use, and this line kept after the skill-load sentence: "`#websearch` comes from the Web Search for Copilot extension. Without it, fall back to `#web/fetch` against known sources and say which claims could not be verified."

- [ ] **Step 2: `quick-searcher.agent.md`**

Frontmatter:

```yaml
---
name: quick-searcher
description: >
  Lite web search agent for single-fact lookups and quick web answers on any topic; also the
  verifier /team-research dispatches to settle one contested claim with a third independent
  source. Use when the user asks for a single fact, definition, stat, URL, or quick confirmation
  answerable by 1-3 web searches from one source, or when dispatched with a verifier block. Not for
  synthesis across 3+ sources (use deep-researcher or /team-research), local code or files (use
  `#search/textSearch`, `#search/fileSearch`), or implementing or editing code.
user-invocable: true
tools:
  - read/readFile
  - execute/runInTerminal
  - execute/getTerminalOutput
  - web/fetch
  - websearch
agents: []
---

<!-- Vendored from plugins/research/agents/quick-searcher.md in acaprino/claude-code-daodan, MIT. -->
```

Body: the body of `plugins/research/agents/quick-searcher.md` with the table applied and the `$SKILLS` paragraph before the first use.

- [ ] **Step 3: `research-orchestrator.agent.md` (export-only; carries the lead logic)**

Frontmatter: keep the existing `name`, `handoffs`, `user-invocable`; set:

```yaml
description: >
  Drives the /team-research pipeline: clarify scope only when the question is ambiguous, show a
  plan of sub-questions for approval, dispatch one deep-researcher per sub-question in parallel,
  verify contradictions with quick-searcher, run a targeted second wave at deep, synthesize a
  long-form cited report, check every citation and write the report to disk. Use when the user asks
  an open-ended research question that needs synthesis across many sources or a comparison of options.
argument-hint: "<question>" [--depth auto|quick|standard|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto|websearch|serper] [--domain <hint>]
tools:
  - read/readFile
  - search/fileSearch
  - edit/createFile
  - edit/createDirectory
  - execute/runInTerminal
  - execute/getTerminalOutput
  - web/fetch
  - websearch
  - agent/runSubagent
  - vscode/askQuestions
  - todos
agents:
  - deep-researcher
  - quick-searcher
```

Keep the `<!-- Export-only ... -->` comment. Body: the body of `plugins/research/commands/team-research.md` (from `# Team Research` on) with the table applied, plus: dispatch sentences say "Dispatch with `#agent/runSubagent`, using the exact name from the `agents:` list above, every researcher in one message so they run concurrently"; `AskUserQuestion` calls become `#vscode/askQuestions`; the environment check for `SERPER_API_KEY` is phrased "run `echo $SERPER_API_KEY` in the terminal (or `$env:SERPER_API_KEY` in PowerShell)"; the `$SKILLS` paragraph precedes the first script path. Delete nothing else.

- [ ] **Step 4: `team-research.prompt.md`**

```markdown
---
description: Deep web research run with clarification, plan approval, parallel iterative researchers, a citation check and a report written to disk. Web only.
argument-hint: "<question>" [--depth auto|quick|standard|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto|websearch|serper] [--domain <hint>]
agent: research-orchestrator
---

# Team Research

Run the deep research pipeline on `$ARGUMENTS` exactly as the `research-orchestrator` agent body describes: pre-flight (backend detection), clarify only when the question is ambiguous, plan for approval, wave 1 of `deep-researcher` instances in parallel, gap analysis with `quick-searcher` verifiers and a second wave at `--depth deep`, synthesis, citation check, and delivery of `research/<YYYY-MM-DD>-<slug>.md` (or `--out`) plus `<stem>.researchers.md`.

**This prompt researches the web, and only the web.** It never reads or searches a local codebase and dispatches nothing from another bundle. A question about local code belongs to `#search/textSearch`, `#search/fileSearch`, or a codebase-oriented bundle, not here.

Load the `web-search-techniques` skill before planning: it defines the two search backends (`#websearch`, and serper.dev through `websearch.py` when `SERPER_API_KEY` is set), the operators and the reading rules the dispatch blocks refer to.
```

- [ ] **Step 5: `web-search-techniques/SKILL.md`**

Keep the export frontmatter (`user-invocable`, `license`, `metadata`), rewrite `description` from the Task 2 source with the table applied. Body: the Task 2 body with the table applied (`${CLAUDE_PLUGIN_ROOT}/scripts/websearch.py` -> `$SKILLS/web-search-techniques/scripts/websearch.py`, same for `webfetch.py`) and the `$SKILLS` paragraph before the Search Backends table.

- [ ] **Step 6: Mirror byte-copies and regenerate the manifest locally**

Run: `python scripts/mirror_export.py && python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py`
Expected: `websearch.py` appears at `exports/vscode/research/.github/skills/web-search-techniques/scripts/websearch.py`; manifest counts unchanged (no agent or prompt added or renamed). Do NOT edit `exports/vscode/package.json` `version` by hand (the script sets it).

- [ ] **Step 7: Verify**

Run: `python .claude/skills/downstream-exports/scripts/check_export.py && python scripts/mirror_export.py --check && python scripts/mirror_export.py --check --since origin/master && python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check`
Expected: all pass.
Run: `grep -rn --exclude-dir=scripts "WebSearch\|WebFetch\|AskUserQuestion\|CLAUDE_PLUGIN_ROOT\|research:[a-z]" exports/vscode/research/.github/ | grep -v "Vendored from"`
Expected: no output.
Run: `cd exports/vscode && npx --yes @vscode/vsce package --no-dependencies --out /tmp/daodan.vsix; cd ../..`
Expected: packages without error.

- [ ] **Step 8: Commit**

```bash
git add exports/vscode/research/.github/agents/deep-researcher.agent.md exports/vscode/research/.github/agents/quick-searcher.agent.md exports/vscode/research/.github/agents/research-orchestrator.agent.md exports/vscode/research/.github/prompts/team-research.prompt.md exports/vscode/research/.github/skills/web-search-techniques/SKILL.md exports/vscode/research/.github/skills/web-search-techniques/scripts/websearch.py exports/vscode/package.json
git commit -m "Mirror research 6.0.0 into the VS Code bundle"
```

(Stage `exports/vscode/package.json` only if `git diff --stat exports/vscode/package.json` shows a change; otherwise leave it out of the command.)

---

### Task 9: Eval harness `evals/research/`

**Files:**
- Create: `evals/research/README.md`
- Create: `evals/research/RESULTS.md`
- Create: `evals/research/scorecard-template.md`
- Create: `evals/research/cases/<slug>/case.md` for the eight cases below

- [ ] **Step 1: README.md**

```markdown
# research eval harness

Measures whether `/research:team-research` still behaves the way it is designed to behave. The plugin has no bug ground truth to recall: its value is a set of **behavioral invariants** (a plan before any search, no citation outside the sources table, every cited page actually read, the backend stated, effort scaled to the question), and the failure mode is drift, where a later edit quietly removes one and nothing notices.

Each case states a question, the flags, and assertions that either hold or do not. Assertions target the philosophy, never the wording. This directory is a development asset of the marketplace repository: not part of the `research` plugin, not registered in `marketplace.json`, never shipped.

## Protocol

0. **Establish which version is under test, and prove it.** Check `~/.claude/plugins/cache/<marketplace>/research/` against `marketplace.json`; if they differ, update the marketplace and start a new session, or run against the working-tree files and say so in the scorecard. A run whose scorecard does not name the version it exercised is not a result.
1. **Run in a scratch directory**, never in this repository: the report file lands in `research/` under the working directory.
2. **Run the case's command in a FRESH session.** Answer the clarification or plan gate as the case says (usually `Approve`).
3. **Keep the transcript.** Several assertions read it: whether a search happened before the plan, how many researchers were spawned, what each returned.
4. **Score each assertion** `pass`, `fail`, or `n/a` (only when the case makes it conditional).
5. **Record the run** in a copy of `scorecard-template.md` inside the case directory (`scorecard-<date>.md`), and add one row to `RESULTS.md`.

MUST assertions are the invariant. A single MUST failure fails the case. SHOULD assertions describe quality and do not fail the case alone.

## Rules

- Never tell the session under test what the assertions are. Never let it read this directory.
- Whoever wrote the change should not score it; score with a reader holding only the assertions, the transcript and the files.
- Cost (wall-clock, researchers spawned, pages read from the run header) is recorded for every case; in the tier cases it IS the assertion.
- Network results vary; an assertion about content quality is SHOULD, an assertion about pipeline behaviour is MUST.

## Cases

| Case | Invariant under test |
|---|---|
| `plan-before-search` | Without `--auto`, the plan is shown and approved before the first search |
| `clarify-only-when-ambiguous` | A clear question gets no clarifying questions; an ambiguous one gets at most four, in one call |
| `citations-resolve` | No claim in the report cites a source absent from the sources table |
| `sources-were-read` | Every source in the table appears in some researcher's "Sources read" in the companion file |
| `backend-stated` | The backend is in the header; `--backend serper` without a key stops with the setup line |
| `tier-bands` | Researcher counts stay inside the tier band; `deep` runs at most two waves |
| `one-fact-routes-to-quick` | A one-fact question goes to quick-searcher with no research run |
| `majority-failure-stops` | A wave where more than half the researchers fail stops the run instead of synthesizing |
```

- [ ] **Step 2: RESULTS.md and scorecard-template.md**

`RESULTS.md`:

```markdown
# Runs

| Date | Case | Plugin version | Result | MUST passed | Scorecard |
|---|---|---|---|---|---|
```

`scorecard-template.md`:

```markdown
# Scorecard: <case>

- **Date:**
- **Command run:** `/research:team-research ...`
- **Model / session:**
- **Plugin version under test:**
- **Scratch directory and output files:**
- **Backend in use:**

## Assertions

| # | Type | Outcome (pass / fail / n/a) | Evidence |
|---|------|-----------------------------|----------|

Evidence is a quote from the transcript or a file read, not a summary. An assertion scored `pass` with no evidence is unscored.

## Cost

- Wall-clock:
- Researchers spawned (wave 1 / wave 2 / verifiers):
- Pages read (from the run header):

## Observations

[Near misses, invariants held for the wrong reason, assertions that turned out to encode a preference.]

## Verdict

- MUST assertions: N passed / M total
- Case result: PASS (all MUST passed) | FAIL
```

- [ ] **Step 3: The eight case files**

`cases/plan-before-search/case.md`:

````markdown
# Case: plan-before-search

## Run
Fresh session, scratch directory:
```
/research:team-research "What are the trade-offs between SQLite and PostgreSQL for a single-node web app in 2026?" --no-clarify
```
Answer the plan gate with `Approve`.

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | A plan listing sub-questions is shown through a question tool and approval is awaited before any WebSearch, WebFetch or websearch.py call appears in the transcript |
| 2 | MUST | The plan names the tier, the backend and the output path |
| 3 | MUST | The approved plan appears verbatim in the report's Methodology section |
| 4 | SHOULD | Sub-questions are derived from the question (not a fixed list of source angles) |
````

`cases/clarify-only-when-ambiguous/case.md`:

```markdown
# Case: clarify-only-when-ambiguous

## Run
Two fresh sessions, scratch directory.
Run A: `/research:team-research "What is the maximum payload size of an AWS Lambda synchronous invocation, and has it changed since 2024?"`
Run B: `/research:team-research "best database"`
In B, answer the clarification with any consistent choices, then `Approve`.

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Run A asks no clarifying question (it may state that none was needed) and goes to the plan |
| 2 | MUST | Run B asks clarifying questions, at most four, in a single question-tool call, before the plan |
| 3 | MUST | Run B's plan restates the question using the answers given |
| 4 | SHOULD | Run A is routed to `quick` or to a direct quick-searcher answer rather than `standard` |
```

`cases/citations-resolve/case.md`:

````markdown
# Case: citations-resolve

## Run
Fresh session, scratch directory:
```
/research:team-research "How do Rust, Go and Zig handle error propagation, and what do practitioners complain about in each?" --auto --depth standard
```

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every `[n]` in the report body resolves to an entry `[n]` in the Sources section |
| 2 | MUST | Every entry in Sources is cited at least once in the body |
| 3 | MUST | The header carries "Citation check: done" |
| 4 | MUST | No factual sentence in Key findings lacks a citation, or it is explicitly marked unverified |
| 5 | SHOULD | Source entries carry title, site, the date the page carries, URL and an authority rank |
````

`cases/sources-were-read/case.md`:

```markdown
# Case: sources-were-read

## Run
Same run as `citations-resolve` (score both from one run), reading `<stem>.researchers.md`.

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Every URL in the report's Sources section appears in some researcher's or verifier's "Sources read" / "Third source" in the companion file |
| 2 | MUST | The companion file contains one section per researcher and verifier spawned, in spawn order |
| 3 | MUST | No researcher report cites a claim with zero `[S<n>]` ids |
| 4 | SHOULD | No URL is cited from a search snippet alone (a source in the table with no corresponding fetch in the transcript) |
```

`cases/backend-stated/case.md`:

```markdown
# Case: backend-stated

## Run
Two fresh sessions, scratch directory, with `SERPER_API_KEY` UNSET in both.
Run A: `/research:team-research "Current status of WebGPU support across browsers" --auto --depth quick`
Run B: `/research:team-research "Current status of WebGPU support across browsers" --auto --backend serper`

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Run A's plan and report header both state `Backend: websearch` |
| 2 | MUST | Run B stops before any researcher is spawned and prints the websearch.py setup line (names `SERPER_API_KEY`) |
| 3 | MUST | Run A's spawn prompts each carry a `Backend:` line |
| 4 | SHOULD | If a key IS available on the machine, a third run with `--backend auto` states `Backend: serper` in plan and header (n/a otherwise) |
```

`cases/tier-bands/case.md`:

```markdown
# Case: tier-bands

## Run
Two fresh sessions, scratch directory.
Run A: `/research:team-research "Compare Pydantic v2 and attrs for a data-validation layer" --auto --depth quick`
Run B: `/research:team-research "How should a small team evaluate, adopt and govern AI coding assistants in 2026: productivity evidence, security and IP risk, licensing, and rollout practice?" --auto --depth deep`

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Run A spawns 1-2 deep-researcher instances and no second wave |
| 2 | MUST | Run B spawns 6-12 deep-researcher instances in total, across at most two waves, all instances of a wave in one message |
| 3 | MUST | Every spawn prompt in B carries a Budget line matching the deep tier (25 searches / 20 pages / 6 rounds) |
| 4 | MUST | Run B's header reports pages read and researchers per wave |
| 5 | SHOULD | Run B's pages read is 100 or more |
```

`cases/one-fact-routes-to-quick/case.md`:

````markdown
# Case: one-fact-routes-to-quick

## Run
Fresh session, scratch directory:
```
/research:team-research "What is the default port of PostgreSQL?" --auto
```

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | No deep-researcher is spawned; quick-searcher answers directly (or the lead answers with one source and says no run was needed) |
| 2 | MUST | The answer carries a source URL |
| 3 | MUST | No report file is written for a one-fact question, and the session says so |
````

`cases/majority-failure-stops/case.md`:

````markdown
# Case: majority-failure-stops

## Setup
Simulate failing researchers by running with network access blocked for subagents, or in an environment where WebFetch and WebSearch fail (e.g. offline), with `SERPER_API_KEY` unset. If that cannot be arranged, score every assertion n/a and say so.

## Run
```
/research:team-research "Compare the three most used Python web frameworks" --auto --depth standard
```

## Assertions
| # | Type | Assertion |
|---|---|---|
| 1 | MUST | If pre-flight detects no backend, the run stops at pre-flight with the reason and no researcher is spawned |
| 2 | MUST | If researchers are spawned and more than half return `error` or empty, the lead stops, names the failed researchers, and writes no report |
| 3 | MUST | No synthesis is produced from fewer than half of the planned researchers |
````

- [ ] **Step 4: Verify**

Run: `ls evals/research/cases | wc -l && grep -rn -- " -- \|—" evals/research/ | head`
Expected: `8`, then no grep output.

- [ ] **Step 5: Commit**

```bash
git add evals/research
git commit -m "Add the research eval harness: eight behavioural invariants for the deep-research pipeline"
```

---

### Task 10: Whole-repo verification

**Files:** none modified unless a check fails.

- [ ] **Step 1: Run every consistency check**

```bash
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_plugin_registration.py
python scripts/lint_fact_anchors.py
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/check_version_bumps.py origin/master HEAD
python scripts/mirror_export.py --check --since origin/master
python -m unittest discover -s tests -v
python scripts/extension_release_notes.py 25.0.0
```

Expected: every command exits 0; the last prints the `## 25.0.0` changelog section. Note: `extension_release_notes.py` compares against `exports/vscode/package.json` `version`, which the local `mirror_export.py` run in Task 8 set to 25.0.0; if it still reads 24.1.0 because that step was skipped, run `python scripts/mirror_export.py` and stage `exports/vscode/package.json` in the Task 8 commit rather than here.

- [ ] **Step 2: Dash-aside sweep over everything this plan touched**

```bash
grep -n -- " -- \|—" plugins/research/agents/*.md plugins/research/commands/*.md plugins/research/skills/web-search-techniques/SKILL.md plugins/research/scripts/websearch.py docs/plugins/research.md exports/vscode/research/.github/agents/*.md exports/vscode/research/.github/prompts/*.md exports/vscode/research/.github/skills/web-search-techniques/SKILL.md evals/research -r
```

Expected: no output.

- [ ] **Step 3: Fix and commit anything the checks found**

If a check failed, fix the declaration or the file (never the linter), re-run Step 1, and commit with a message naming the check. If everything passed, there is nothing to commit: report the green run. Do not push.
