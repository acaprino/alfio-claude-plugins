---
name: grabber-development
description: >
  Comprehensive Python web scraping knowledge base covering stealth browser automation (Patchright, Camoufox, Nodriver),
  TLS/HTTP fingerprint impersonation (curl_cffi, primp), anti-bot bypass (Cloudflare, DataDome, PerimeterX),
  CAPTCHA solving, proxy architecture, AI-assisted extraction (Crawl4AI, Firecrawl, ScrapeGraphAI),
  framework selection (Scrapy, Crawlee), rate limiting, and production observability.
  TRIGGER WHEN: building, implementing, writing, coding, creating, optimizing, or debugging Python web scrapers.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Python Web Scraping

Knowledge base for building production-grade Python web scraping systems. Covers the full stack from target assessment through production observability.

## First Tool Call on Every Scraping Task

This section overrides everything else in this skill if there is any conflict. Read it first, act on it first.

When this skill activates on a scraping task, **your next non-question tool call MUST launch a visible browser with the capture surface attached**. Not `Write pyproject.toml`. Not `Write models.py`. Not "let me sketch the architecture first". Browser first, then code.

The default path is **user-driven navigation with live capture**, not Claude-clicks. The user knows their data and their portal better than you do, and authenticated SaaS sites need them anyway. Steps:

1. Ask the bare minimum to start: target URL, what data is wanted, authenticated yes/no. One short batch of questions, then stop asking.
2. Immediately invoke `playwright-skill` (preferred; it is a declared dependency of this plugin, installed from its upstream marketplace: `claude plugin marketplace add lackeyjb/playwright-skill`, then `claude plugin install playwright-skill@playwright-skill`) or write an inline Patchright script via `Bash`. The script must run with `headless=False`, attach every handler in the Capture Surface below, and park on `input()` waiting for the user.
3. Tell the user verbatim: "Browser is open with full network capture (XHR + fetch + WebSocket + SSE + workers + cookies + main-frame navigations). Log in, navigate to the data, apply the filters you'd use day-to-day, then press Enter here so I can dump the capture and reason from real endpoints."
4. While the user navigates, you watch the capture stream. When they press Enter you have: real URLs, real endpoint paths, real field names, real WebSocket frames, real auth cookies. *Now* you can scaffold.

The Claude-drives variant is fine only when there is no login, no 2FA, and no UI-knowledge gap. Same launch, same capture handlers; you call `page.goto` / `page.click` yourself instead of parking on `input()`.

Writing project files (`pyproject.toml`, `src/<pkg>/...`, `models.py`) before the capture is in your hands is the failure mode this section exists to prevent. If you catch yourself drafting field-name `alias` tuples from "common patterns" (Italian + English, REST conventions, framework defaults), stop and launch the browser instead.

The full capture surface, output checklist, and anti-patterns are in the **Discovery Gate** section below. Read those too. But the imperative is here: **browser before code, every time, user navigates by default.**

## When to Use

- Assessing a target site's protection level and choosing the right tools
- Discovering API endpoints via network traffic interception (Playwright/Patchright)
- Extracting data from rendered pages when no API is available
- Bypassing anti-bot systems (Cloudflare, DataDome, PerimeterX)
- Configuring TLS/HTTP fingerprint impersonation (curl_cffi, primp)
- Setting up stealth browser automation (Patchright, Camoufox, Nodriver)
- Designing proxy architecture with tiered escalation
- Solving CAPTCHAs programmatically (CapSolver, 2Captcha, playwright-captcha)
- Building production scraping pipelines (Scrapy, Crawlee)
- Adding rate limiting and observability to scraping systems

## Discovery Gate (READ BEFORE WRITING ANY CODE)

**Phase 1 (Target Assessment) and Phase 2 (Data Discovery) are blocking gates, not optional steps.** You MUST execute them yourself and have their concrete outputs in hand before scaffolding any project file (`pyproject.toml`, modules, models, CLI). No exceptions.

**You always control the browser session and the capture.** The deliverable of discovery is not a script you hand over; it is a live capture you watched. Always launch the browser yourself (via `playwright-skill` or inline Patchright) with `headless=False` and the full capture surface attached, and keep the session open inside your turn.

**Who clicks depends on the task. The capture is yours either way:**

- **Claude clicks** when the target is reachable without the user: no login, no 2FA, you know the UI, you can guess the right filters.
- **User clicks, you watch in-loop** when the target needs the user: login, 2FA / OTP, navigation choices only the user can make, or the user wants to drive the filters / dates / screens visited. This is the gold-standard path for authenticated SaaS portals because the user knows exactly which screens hold the target data. Launch the browser visibly, park on an `input()` checkpoint, let the user navigate while the network capture streams live, then dump the capture when they signal "done".
- The actual anti-pattern is writing `scripts/discover.py` and telling the user "run this and paste the output back". That breaks the loop: by the time the user runs it, you have no eyes on the session and no chance to ask "wait, click that filter again, I lost the payload".

**Capture surface (attach all of these from page launch):**

- `page.on("request")` / `page.on("response")` for XHR + fetch (URL, method, status, headers, cookies, request body, response body when JSON or text)
- `page.on("websocket")` then `ws.on("framesent")` / `ws.on("framereceived")` for WebSocket traffic in both directions
- Response content-type sniff for `text/event-stream` (SSE) and chunked transfer
- `page.on("worker")` for service-worker- and dedicated-worker-initiated requests
- GraphQL detection: URL ends in `/graphql`, request body has `operationName` / `variables` / `extensions.persistedQuery.sha256Hash`
- `context.cookies()` after login, plus any anti-bot cookies (`cf_clearance`, `__cf_bm`, `datadome`, `_px3`, `ak_bmsc`, `incap_ses`)
- `page.on("framenavigated")` filtered to the main frame, to record every landing URL after redirects

Redact `Authorization`, `Cookie`, and password fields in anything saved to disk. Keep them in the in-memory capture you reason from.

**Discovery outputs you MUST collect before scaffolding** (treat as a checklist; if any item is still a guess, you have not finished discovery):
- Real URL of every page that holds target data (not assumed paths, not `/#/...` guesses)
- Real XHR/fetch endpoint URLs, methods, status codes, request headers, cookies
- Real field names and shapes from at least one captured JSON response (paste a redacted sample into the design notes)
- For any WebSocket the page opens: handshake URL, subprotocol, first frames in each direction (auth + subscribe), recurring message schema
- For any SSE / EventSource stream: endpoint URL, event types, payload shape
- For GraphQL: exact `operationName` and `variables`, persisted-query SHA if present
- For service-worker / dedicated-worker requests: the worker URL and the requests it issues
- Anti-bot fingerprint check: `cf_clearance`, `__cf_bm`, `datadome`, `_px3`, `ak_bmsc`, `incap_ses` present or absent
- SPA framework / DOM structure of any page where API discovery fails and a DOM fallback is needed

If any of those is still a guess, you have not finished discovery; do not proceed to scaffolding.

### Anti-Patterns (do not do these)

- Scaffolding `pyproject.toml` and module skeleton before observing one real network request from the target
- Inferring endpoint URLs from "common patterns" (e.g. `/api/invoices`, `/#/fatture-ricevute`) without observation
- Building a regex / filter list of "common field names" (e.g. `(fatture|invoice|received|ricevute|passive)`) as a substitute for the real endpoint name
- Writing a Pydantic model with `Field(alias=...)` tuples of "Italian + English likely names" instead of the names actually returned by the API
- Handing the user a `discover.py` script as the *first* discovery step when you could open the browser yourself
- Marking Phase 1 / Phase 2 as "skipped, will refine later" and proceeding to write code anyway

## Core Workflow

For every scraping task, follow this sequence (the Discovery Gate above governs steps 1 and 2):

### 1. Target Assessment (YOU execute this)
- Load the target URL in a stealth browser (via `playwright-skill` or inline Patchright)
- Identify: static HTML vs JS-rendered, anti-bot service (check for cf_clearance, DataDome cookies, px cookies), data volume needed, update frequency
- Capture: real landing URL after any redirects, SPA framework if any, presence/absence of anti-bot cookies

### 2. Data Discovery (API-first, YOU execute this)
- Navigate the site with Playwright/Patchright **yourself**
- Intercept all network traffic via `page.on("request")` and `page.on("response")`
- Filter for XHR/fetch requests returning JSON, GraphQL, or structured data
- Classify: REST endpoints, WebSocket streams, GraphQL queries, SSE feeds
- Record (do not guess): URLs, methods, headers, cookies, response shapes, real field names
- If structured API found: generate curl_cffi replay code (skip browser entirely)
- If the page is gated by credentials you have and 2FA you can prompt for, log in via the browser session and continue discovery in the authenticated area

### 3. DOM Fallback (only if no API)
- If data exists only in rendered HTML: extract via CSS/XPath selectors
- Check for JSON-LD, microdata, or inline `<script>` JSON before parsing DOM
- For unstable DOM: use LLM-based extraction (Crawl4AI, ScrapeGraphAI) as final fallback
- Hybrid pattern: CSS selectors for stable fields ($0/extraction) + LLM for unstable fields (~$0.01/repair)

### 4. Stealth & Evasion (layer minimally)
- No protection: plain curl_cffi with `impersonate="chrome"` -- done
- Basic Cloudflare: Patchright persistent context + real Chrome channel
- Heavy Cloudflare/Turnstile: stealth browser + CAPTCHA solver + residential proxy
- DataDome: Camoufox + ghost-cursor behavioral simulation + residential proxy
- PerimeterX: organic navigation pattern + session warming + residential proxy

### 5. Production Hardening
- Rate limiting: pyrate-limiter v4 with Redis backend for distributed scraping
- Proxy rotation: tiered escalation (datacenter -> ISP -> residential -> mobile)
- Observability: structlog + Prometheus + Grafana
- Error handling: retry with backoff, proxy failover, session rotation

## Tool Selection Quick Reference

| Target Profile | HTTP Client | Browser | Framework |
|---------------|-------------|---------|-----------|
| No JS, no protection | curl_cffi | none | Scrapy / httpx |
| JS-rendered, no protection | none | Playwright | Crawlee |
| Basic Cloudflare | curl_cffi + cf_clearance | Patchright (for cookie) | Scrapy |
| Heavy Cloudflare | none | Patchright persistent | Crawlee |
| DataDome | none | Camoufox + ghost-cursor | custom |
| PerimeterX | none | Nodriver / Patchright | custom |
| AI extraction needed | none | Crawl4AI / Firecrawl | standalone |

## Proxy Tier Quick Reference

| Tier | Type | Price Range | Use When |
|------|------|-------------|----------|
| 0 | No proxy | free | Unprotected targets, development |
| 1 | Datacenter | $0.10-0.50/GB | Light protection, high volume |
| 2 | ISP (static residential) | $0.53-1.47/IP | Account management, login flows |
| 3 | Residential | $0.49-8.00/GB | Anti-bot bypass, geo-targeting |
| 4 | Mobile | $4-13/GB | Highest trust, last resort |

## Reference Materials

- `field-guide.md` -- full 2025-2026 Python web scraping field guide covering browser stealth, TLS fingerprinting, behavioral biometrics, anti-bot bypass, CAPTCHA solving, proxy landscape, frameworks, AI-assisted scraping, GraphQL reverse engineering, rate limiting, and observability
