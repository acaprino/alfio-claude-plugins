# Grabber Development Plugin

> Expert Python web scraping - coordinator plus three specialists covering stealth browser automation, TLS/HTTP fingerprint impersonation, AI-assisted extraction, anti-bot bypass, proxy architecture, API discovery, and production observability.

## Agents

### `grabber-architect`

Lead architect / coordinator for production Python scraping systems. Handles upstream work (target assessment, discovery, framework choice, cost, observability, legal guardrails) and routes specialist tasks.

| | |
|---|---|
| **Model** | `inherit` |
| **Color** | pink |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch |
| **Use for** | Designing a new scraping pipeline end-to-end, assessing target protection before tool choice, API reverse-engineering via network interception, framework selection (Scrapy / Crawlee / Crawl4AI / Firecrawl), rate limiting + observability, cost modelling, routing to specialists |

**Decision frameworks:**
- Tool selection matrix (target profile -> HTTP client + browser + framework)
- Proxy tier selection (protection level -> tier + provider)
- Extraction strategy (data location -> method + cost + stability)
- Framework choice (Scrapy 2.14, Crawlee v1.0, Crawl4AI v0.8+, Firecrawl)

**Legal / ethical guardrails:** Documents robots.txt, ToS, GDPR/CCPA, CNIL guidance, EU AI Act Art. 50, copyright considerations. Refuses to generate code that bypasses paywalls or auth without documented permission.

---

### `stealth-browser-expert`

Specialist for stealth browser automation: Patchright, Camoufox, Nodriver, rebrowser-patches, selenium-driverless, behavioral biometrics, and browser-level CAPTCHA integration.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Picking / configuring stealth browser driver (Patchright for Chromium, Camoufox for Firefox / DataDome, Nodriver for PerimeterX / Cloudflare); behavioral biometrics (ghost-cursor); `cf_clearance` extraction for HTTP replay; persistent context strategy; browser-level CAPTCHA (playwright-captcha, playwright-recaptcha) |

**Driver matrix:** Patchright (Chromium, general) / Camoufox (Firefox, DataDome) / Nodriver (PerimeterX, advanced CF) / rebrowser-patches (existing Puppeteer codebases).

**Key content:** driver selection by target protection level, behavioral biometrics (velocity/acceleration curves, typing rhythm, scroll momentum), CAPTCHA-before-environment rule (environment signals matter more than puzzle-solve quality), cf_clearance handoff to `http-fingerprint-expert`.

---

### `http-fingerprint-expert`

Specialist for HTTP/TLS fingerprinting and impersonation: curl_cffi, primp, async-tls-client, JA3 / JA4 / JA4+ suite, HTTP/2 fingerprinting, proxy tier selection (datacenter / ISP / residential / mobile), and managed Web Unlocker APIs.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Picking HTTP client that impersonates a browser TLS fingerprint; debugging why httpx/requests gets blocked; reverse-engineering an API for `curl_cffi` replay; choosing proxy tier; integrating a Web Unlocker API (Bright Data / Oxylabs / ZenRows) |

**Client matrix:** curl_cffi (default for protected targets, Chrome 99-135 / FF 102-135 / Safari 15-18 / HTTP/3), primp (Rust-powered, 2-3x faster), async-tls-client v2.2+ (historical profiles), plus Go alternatives.

**Key content:** JA4+ suite vs deprecated JA3, HTTP/2 fingerprinting (SETTINGS, WINDOW_UPDATE, pseudo-header order), browser session replay rules (TLS family must match browser, UA must match exactly, IP must match), proxy tier cost table (datacenter $0.10-0.50/GB -> mobile $4-13/GB), Web Unlocker API cost/benefit (~$3.40/1K requests for Bright Data, ~97.9% success).

---

### `ai-scraping-expert`

Specialist for AI-assisted extraction: Crawl4AI, Firecrawl, ScrapeGraphAI, Browser Use, Stagehand, Skyvern, Jina Reader, Spider.cloud; Pydantic schema-driven extraction; LLM-repair hybrid pipelines; GraphQL reverse engineering; cost modelling for LLM-based extraction at scale.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Picking between LLM-based scraping frameworks; designing schema-driven extraction with Pydantic; building a CSS + LLM-fallback hybrid; reverse-engineering a GraphQL API (persisted query bypass); estimating extraction cost at 1M+ pages/month scale |

**Framework matrix:** Crawl4AI (LLM-ready markdown, deep crawl) / Firecrawl (strongest Pydantic integration) / ScrapeGraphAI (graph-based LLM pipelines) / Browser Use (85K stars, 89% WebVoyager) / Stagehand (self-healing) / Skyvern (vision-first) / Jina Reader (100B tokens/day).

**Key content:** when LLM extraction vs CSS vs JSON-LD (CSS ~$0, LLM ~$0.01/page), hybrid CSS+LLM fallback pattern (10x cost reduction), Pydantic schema-driven extraction, GraphQL persisted-query bypass via mitmproxy sha256Hash replacement, cost formulas for 1M pages/month pipelines.

---

## Skills

### `grabber-development`

Comprehensive Python web scraping knowledge base covering the full stack from target assessment through production observability.

| | |
|---|---|
| **Trigger** | Building, optimizing, or debugging Python web scrapers |

**Core workflow:**

1. **Target Assessment** - Identify protection level, data volume, update frequency
2. **Data Discovery (API-first)** - Intercept network traffic, find REST/GraphQL/WebSocket endpoints
3. **DOM Fallback** - CSS/XPath selectors, JSON-LD, LLM extraction as last resort
4. **Stealth & Evasion** - Layer minimally: plain curl_cffi -> Patchright -> Camoufox + ghost-cursor
5. **Production Hardening** - Rate limiting, proxy rotation, observability, error handling

**Quick reference tables:**

| Target Profile | HTTP Client | Browser | Framework |
|---------------|-------------|---------|-----------|
| No JS, no protection | curl_cffi | none | Scrapy / httpx |
| JS-rendered, no protection | none | Playwright | Crawlee |
| Basic Cloudflare | curl_cffi + cf_clearance | Patchright | Scrapy |
| Heavy Cloudflare | none | Patchright persistent | Crawlee |
| DataDome | none | Camoufox + ghost-cursor | custom |
| PerimeterX | none | Nodriver / Patchright | custom |

**Reference docs included:**

| Reference | Content |
|-----------|---------|
| `field-guide.md` | Full 2025-2026 Python web scraping field guide - browser stealth, TLS fingerprinting, behavioral biometrics, anti-bot bypass, CAPTCHA solving, proxy landscape, frameworks, AI-assisted scraping, GraphQL reverse engineering |

---

**Related:** [python-development](python-development.md) (async patterns, system architecture) | [opentelemetry](opentelemetry.md) (distributed tracing for scraping observability) | [playwright-skill](https://github.com/lackeyjb/playwright-skill) (upstream plugin, required for live-capture discovery; install: `claude plugin marketplace add lackeyjb/playwright-skill`, then `claude plugin install playwright-skill@playwright-skill`)
