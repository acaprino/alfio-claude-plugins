# Python web scraping in 2025–2026: the definitive field guide

The web scraping landscape has undergone a fundamental shift since 2024. **Behavioral biometrics now outweigh fingerprinting** as the primary bot detection vector, TLS fingerprinting has migrated from JA3 to JA4+, and an entirely new category of **agentic AI scrapers** has emerged with tools like Browser Use (84K GitHub stars) and Crawl4AI (51K stars) redefining what "scraping" means. The old playbook of `requests` + `BeautifulSoup` + free proxies is functionally dead against any protected target. Success in 2026 demands a layered approach: TLS-fingerprint-matched HTTP clients, stealth browser automation, residential proxies, behavioral simulation, and increasingly, LLM-driven extraction that survives DOM changes without selector maintenance.

This guide covers every major development across 12 areas -- from browser stealth and TLS impersonation to legal precedent and observability -- with specific library versions, GitHub URLs, code examples, and a clear distinction between what's genuinely new and what was already established.

---

## Browser automation stealth has consolidated around four tools

The stealth browser automation space, previously fragmented across dozens of partial solutions, has consolidated in 2025–2026 around four primary tools, each addressing a different layer of the detection stack.

**Patchright** (GitHub: [Kaliiiiiiiiii-Vinyzu/patchright-python](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python), PyPI: `patchright`, latest v1.58.2, March 2026) is now the go-to Playwright replacement for Chromium stealth. It patches the critical `Runtime.enable` leak by executing JavaScript in isolated ExecutionContexts, disables `Console.enable`, removes `--enable-automation` flags, and injects init scripts via Playwright Routes rather than standard methods. It emerged in late 2024 and has become the default recommendation, surpassing the older `playwright-stealth`. It is Chromium-only and works best with a persistent context using real Chrome (`channel="chrome"`) rather than bundled Chromium.

```python
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="/tmp/profile",
        channel="chrome",
        headless=False,
        no_viewport=True
    )
    page = browser.new_page()
    page.goto("https://www.browserscan.net/")
```

**Camoufox** (GitHub: [daijro/camoufox](https://github.com/daijro/camoufox), PyPI: `camoufox[geoip]`, latest v146.0.1-beta.25, January 2026) takes a fundamentally different approach -- it modifies Firefox's C++ internals rather than injecting JavaScript patches. This means all spoofed properties (navigator, screen, WebGL, canvas, AudioContext, fonts, timezone) appear native to detection scripts. It integrates BrowserForge for statistically realistic fingerprint generation, supports virtual display mode for headful operation on headless servers, and auto-matches GeoIP data to proxy locations. The project experienced a year-long maintenance gap in 2024–2025 due to the maintainer's personal situation. Development resumed in late 2025, but anti-bot providers exploited the gap to identify fingerprint inconsistencies.

**Nodriver** (GitHub: [ultrafunkamsterdam/nodriver](https://github.com/ultrafunkamsterdam/nodriver), PyPI: `nodriver`, v0.48.1, November 2025) is the successor to `undetected-chromedriver`. It communicates with Chrome directly via a custom CDP implementation with zero Selenium/WebDriver dependency, eliminating that entire detection surface. Fully async, it remains in alpha but achieves the highest Cloudflare bypass rates among open-source tools. Limitations include buggy headless mode, limited proxy authentication, and ~100–200MB RAM per instance.

**Rebrowser-patches** (GitHub: [rebrowser/rebrowser-patches](https://github.com/rebrowser/rebrowser-patches), 1.3K stars) provides open-source patches fixing `Runtime.enable` and `addBinding` leaks in both Puppeteer and Playwright. Available as drop-in packages (`rebrowser-playwright` for Python). The project also ships `rebrowser-bot-detector` for testing your stealth setup.

A critical development: **puppeteer-stealth was discontinued in February 2025** and Cloudflare now specifically detects its patterns. The older `playwright-stealth` (PyPI v2.0.2, February 2026) received a major rewrite but explicitly states it "won't bypass anything but the simplest bot detection." It remains useful only as a baseline layer combined with other tools.

---

## TLS fingerprinting moved to JA4+ and now spans five protocol layers

The single biggest shift in bot detection since 2024 is the migration from **JA3 to JA4+ fingerprinting**. Chrome v110 introduced TLS ClientHello extension randomization, which broke JA3's MD5 hash approach entirely. JA4 (by FoxIO, BSD 3-Clause license) counters this by sorting extensions and ciphers alphabetically before hashing and ignoring GREASE values, producing a **human-readable 36-character string** rather than an opaque hash. The JA4+ suite now includes JA4S (server response), JA4H (HTTP client headers + TLS combined), JA4T (TCP/OS fingerprint), JA4X (X.509 certificates), and JA4SSH. Cloudflare, AWS WAF, Auth0/Okta, VirusTotal, and DataDome all use JA4 in production as of 2026.

**HTTP/2 fingerprinting** has become equally important. Anti-bot services analyze the SETTINGS frame parameters (HEADER_TABLE_SIZE, INITIAL_WINDOW_SIZE, MAX_CONCURRENT_STREAMS), WINDOW_UPDATE values, PRIORITY frames, and pseudo-header order (`:method`, `:authority`, `:scheme`, `:path`). Python's `httpx` alphabetizes headers and uses `h2` library defaults for SETTINGS -- both are **instant detection vectors**. A mismatch between Chrome's TLS fingerprint and Go's HTTP/2 SETTINGS frame triggers immediate blocking.

**curl_cffi** (GitHub: [lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi), 5.2K stars, PyPI: `curl-cffi`) has become the essential Python HTTP client for 2025–2026. The stable release is **v0.14.0** (January 2026) with **v0.15.0b4** (February 2026) in pre-release. Key impersonation targets now include Chrome 99–145, Safari 15.3–260 (including iOS), Edge, and Firefox. Version 0.12 added full HTTP/3 support, and v0.15.0b4 introduced **HTTP/3 fingerprint spoofing** -- a critical capability as HTTP/3 covers 30%+ of web traffic. The shortcut `impersonate="chrome"` always uses the latest Chrome fingerprint.

```python
from curl_cffi import requests

# Impersonate latest Chrome with full TLS + HTTP/2 fingerprint matching
r = requests.get("https://tls.browserleaks.com/json", impersonate="chrome")

# HTTP/3 with fingerprint spoofing (v0.15+)
r = requests.get("https://example.com", http_version="v3", impersonate="chrome")

# Async session with proxy
from curl_cffi.requests import AsyncSession
async with AsyncSession() as s:
    r = await s.get("https://example.com", impersonate="chrome",
                    proxies={"https": "http://user:pass@proxy:port"})
```

Two strong alternatives have emerged. **primp** (GitHub: [deedy5/primp](https://github.com/deedy5/primp), PyPI: `primp`, v1.1.3) is a Rust-powered HTTP client (forked reqwest with custom TLS/HTTP stacks via PyO3) supporting Chrome 100–146, Firefox 109–133, Safari 15.3–18.2, with both sync and async APIs. It claims to be the fastest Python HTTP client and supports `impersonate="random"` for automatic browser rotation. **async-tls-client** (PyPI v2.2.0, March 2026) is the most active fork of the stagnant original `tls-client`, offering 50+ preconfigured client profiles with native asyncio. The original `tls-client` by FlorianREGAZ has **stagnated** and should be avoided.

---

## Behavioral biometrics are now the dominant detection frontier

While TLS and browser fingerprinting remain important, **behavioral biometrics have surpassed them as the primary detection signal** for sophisticated anti-bot systems in 2025–2026. DataDome collects 35+ signals per session, PerimeterX/HUMAN trains per-customer ML models on each website's traffic patterns, and Cloudflare's Bot Management ML v8 specifically targets residential proxy bots.

The signals being analyzed include mouse dynamics (velocity, acceleration, curvature -- humans move in curves, bots in straight lines), keystroke dynamics (dwell time, flight time, typing rhythm), scroll patterns (velocity, deceleration curves), navigation flow (humans browse organically, bots go directly to target URLs), and timing regularity (humans have log-normal inter-action delays, bots use fixed intervals or uniform random). A new entrant, **Roundtable Proof of Human** (YC, launched August 2025), claims 87% bot detection accuracy versus Google reCAPTCHA's 69% and Cloudflare Turnstile's 33%, using behavioral and cognitive signatures.

The practical implication is stark: **no universal bypass exists for DataDome or HUMAN/PerimeterX in 2026**. Success requires combining fingerprint spoofing + behavioral simulation (tools like `ghost-cursor` for mouse movements) + residential proxies + per-site tuning. Per-customer ML models mean a technique working on one PerimeterX-protected site may fail on another.

New fingerprinting vectors have emerged. **WebGPU fingerprinting** exploits GPU compute shader scheduling behavior and cache side channels -- academic papers demonstrated 70% device re-identification from 500 devices and 90% website fingerprinting accuracy. Most anti-detect browsers do not yet spoof WebGPU. ML-powered **fingerprint consistency analysis** at Cloudflare and PerimeterX now detects both fingerprints that change too often (randomization) and those that stay too static (spoofing), as well as cross-attribute inconsistencies (e.g., canvas claims not matching WebGL renderer).

---

## Anti-bot bypass requires layered strategies per target

The four major anti-bot services demand different approaches in 2026.

**Cloudflare** remains the most commonly encountered. Its JS challenge sets a `cf_clearance` cookie (valid ~15 days) upon successful completion. Stealth browsers (Nodriver, Camoufox, Patchright in persistent headed mode) can pass challenges automatically. For HTTP-only scraping, extract `cf_clearance` from a browser session, then replay it with curl_cffi using matching TLS fingerprint, User-Agent, and IP. Cloudflare Turnstile (the CAPTCHA replacement) does not generate `cf_clearance` -- it produces a separate token requiring solver APIs. The `cloudscraper` library still handles basic v2 challenges; the fork `cloudscraper25` adds v3 and Turnstile support but struggles against heavy TLS fingerprinting. **FlareSolverr** remains functional but increasingly unreliable.

**DataDome** is described by the scraping community as "next to impossible to reverse engineer." It analyzes 1,000+ signals per session, and LLM crawler traffic across its customer base quadrupled during 2025. The only reliable approaches combine Camoufox + ghost-cursor + residential proxies, or commercial services like ZenRows, ScrapFly, and ParallaxAPIs SDK.

**PerimeterX/HUMAN** (rebranded in 2024) uses delayed enforcement -- it allows initial access, then blocks when you attempt valuable actions. Its per-customer ML models make each protected site a unique challenge.

For all three, **managed "Web Unlocker" APIs** have become the pragmatic solution for teams without dedicated anti-bot engineers. Bright Data Web Unlocker (~$3.40/1K requests, ~97.9% success rate), Oxylabs Web Unblocker, and ZenRows handle the full proxy + fingerprint + CAPTCHA stack in a single API call.

---

## CAPTCHA solving shifted to AI-first architectures

The CAPTCHA solving market has undergone a clear split between **AI-native services** (sub-second solve times, 99%+ accuracy) and **human-powered legacy services** (15–45 seconds, broadest compatibility). CapSolver (capsolver.com) leads the AI category with a hybrid LLM + CNN architecture: the LLM handles reasoning ("click all images containing traffic lights"), the CNN handles pixel-level localization at millisecond speed. It supports reCAPTCHA v2/v3/Enterprise, hCaptcha, Cloudflare Turnstile (`AntiTurnstileTaskProxyLess`), DataDome, and Amazon WAF at ~$0.80/1K solves.

**2Captcha** ($1.00–$2.99/1K) remains the broadest-compatibility option with human workers. It cut prices in May 2025 and added DataDome and MTCaptcha support. **CapMonster Cloud** (by ZennoLab) offers the best budget AI option with sub-1-second solve times and very low per-solve pricing. **NoCaptchaAI** provides the cheapest option with a free tier of 6,000 monthly solves. New entrants include **CaptchaSonic** (claims sub-second, from $0.03/1K) and **NextCaptcha** (reCAPTCHA v3 tokens scoring above 0.9).

For browser automation integration, **playwright-captcha** (PyPI v0.1.1) is new in 2025 and supports Cloudflare Turnstile, reCAPTCHA v2/v3, with auto-detection and both click-based and API-based solving. **playwright-recaptcha** (GitHub: [Xewdy444/Playwright-reCAPTCHA](https://github.com/Xewdy444/Playwright-reCAPTCHA)) solves reCAPTCHA v2 via audio transcription and v3 via POST interception.

A critical paradigm shift: **modern anti-bot systems analyze browser environment before the CAPTCHA even renders**. The risk score from canvas fingerprints, WebGL, and mouse micro-movements determines the challenge difficulty. Solving the puzzle is secondary -- the browser environment is primary.

---

## The proxy landscape demands a tiered strategy

Raw proxies alone no longer suffice against protected targets. The industry has shifted toward **Web Unlocker/Unblocker APIs** that bundle proxy rotation, fingerprint management, CAPTCHA solving, and JS rendering in a single call.

For residential proxies, pricing in 2026 ranges from **$0.49/GB** (Evomi, budget) through **$2.25/GB** (Decodo/Smartproxy at volume) to **$8/GB** (Bright Data/Oxylabs PAYG). **Bright Data** maintains the largest pool at 150M+ IPs across 195 countries with the most comprehensive feature set. **Oxylabs** (100M+ IPs, 99.95% success rate) leads in enterprise reliability. **Decodo** (formerly Smartproxy, 125M+ IPs, rebranded 2024–2025) offers the best price-to-performance ratio at $2.25/GB at volume. **IPRoyal** (10M+ IPs, from $1/GB) is the budget pick with non-expiring bandwidth. **Webshare** (acquired by Oxylabs in 2024) offers **10 free datacenter proxies forever** with no credit card -- genuinely useful for development.

**Mobile proxies** command premium pricing ($4–$13/GB) but provide the highest trust level due to Carrier-Grade NAT -- websites cannot block mobile IPs without affecting thousands of real users. Oxylabs leads with 20M+ mobile IPs across 140+ countries. **ISP proxies** (static residential) are a hybrid: datacenter speed with residential legitimacy, ideal for account management and login flows where consistent IP is needed. Webshare offers the cheapest ISP proxies at $0.53–$1.47/IP.

New in 2025–2026: **AI-powered proxy management** is now standard at top providers, using reinforcement learning for optimal IP routing and real-time adaptation. **Decentralized proxy networks** (DePIN) like Titan Network are emerging but face regulatory scrutiny -- the Dutch Data Protection Authority began investigating non-consensual IP leasing in early 2026. The multi-provider strategy has become standard, with **43.1% of scraping professionals using 2–3 proxy providers** for redundancy (Apify 2026 report).

---

## New frameworks reshape the Python scraping ecosystem

**Scrapy 2.14** (January 2026, GitHub: [scrapy/scrapy](https://github.com/scrapy/scrapy), 55.1K stars) made the async transition real with Scrapy 2.13's replacement of `start_requests()` with `start()` (async), changed the default `DOWNLOAD_DELAY` from 0 to 1 and `CONCURRENT_REQUESTS_PER_DOMAIN` from 8 to 1 in the project template -- a clear signal that polite scraping is now the default expectation. Python 3.10+ is required. Integration with Playwright is available via `scrapy-playwright` v0.0.46.

**Crawlee for Python** (GitHub: [apify/crawlee-python](https://github.com/apify/crawlee-python), ~6K stars, reached v1.0 in September 2025) is the most significant new framework. Built by Apify, it ships anti-blocking, proxy rotation, and session management as defaults rather than plugins. It offers a unified interface across BeautifulSoupCrawler, ParselCrawler, PlaywrightCrawler, and AdaptivePlaywrightCrawler (auto-detects whether JS rendering is needed). v1.0 added OpenTelemetry instrumentation, `robots.txt` respect, SQL-based storage, and persistent browser support. It's less mature than Scrapy's ecosystem but growing rapidly.

**Scrapling** (GitHub: [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling), PyPI: `scrapling`) is the most innovative parser -- it **learns from website changes** and automatically relocates elements using an intelligent similarity system when pages update. It ships `StealthyFetcher` and `PlayWrightFetcher` for Cloudflare Turnstile bypass out-of-the-box, with speeds matching Scrapy/lxml benchmarks.

**Crawl4AI** (GitHub: [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai), **51K+ stars**, v0.8.6, March 2026) is the most-starred crawler on GitHub. It's an open-source, Apache-2.0-licensed LLM-friendly crawler with deep crawl strategies (DFS, BFS, best-first), anti-bot detection with 3-tier proxy escalation, Shadow DOM flattening, and both CSS and LLM-based extraction strategies.

**Playwright** itself (v1.58.0, January 2026) switched from Chromium to **Chrome for Testing** builds in v1.57 and added new methods for retrieving console messages and network requests. **HTTPX** (v0.28.1) has been stable since November 2024 with no major new releases. **Selectolax** (v0.4.7, March 2026) now recommends the Lexbor backend over Modest for 5–30x faster HTML parsing than BeautifulSoup.

For specialized use cases, **PyAirbnb** (PyPI v2.2.1, February 2026, GitHub: [johnbalvin/pyairbnb](https://github.com/johnbalvin/pyairbnb)) remains actively maintained with 10 releases in 2025–2026, handling Airbnb's GraphQL persisted queries by fetching live StaysSearch hashes.

---

## AI-assisted scraping became production-ready

The AI scraping category has matured from experimental to production-grade. Three patterns dominate: natural language extraction, agentic browser navigation, and self-healing scrapers.

**ScrapeGraphAI** (GitHub: [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai), 21K+ stars, v1.74.0, March 2026) uses graph-based LLM pipelines for extraction via natural language prompts -- no CSS selectors needed. It launched an Agentic Scraper mode for automated login, form filling, and navigation. In December 2025, it released a 100K-example structured extraction dataset on Hugging Face. Claims 98%+ accuracy across 10M+ pages.

**Firecrawl** (GitHub: [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl), AGPL-3.0) converts websites to LLM-ready Markdown with Pydantic schema-driven extraction. Its newest feature, the **FIRE-1 agent**, autonomously navigates complex sites -- describe what you want, no URLs needed. The `/interact` endpoint enables agentic page actions (click, type, navigate) after scraping.

```python
from firecrawl import Firecrawl
from pydantic import BaseModel

app = Firecrawl(api_key="fc-YOUR_API_KEY")

class ProductSchema(BaseModel):
    name: str
    price: float
    in_stock: bool

result = app.scrape_url("https://example.com/product", {
    "formats": ["json"],
    "jsonOptions": {"schema": ProductSchema.model_json_schema()}
})
```

**Jina AI Reader** (GitHub: [jina-ai/reader](https://github.com/jina-ai/reader), 10.4K stars) processes **100 billion tokens daily** via a simple URL prefix (`https://r.jina.ai/`). Its **ReaderLM-v2** (1.5B parameter model, ACL 2025 paper) handles HTML-to-Markdown conversion supporting 512K token inputs across 29 languages. Jina was notably acquired by Elastic in 2025–2026. **Spider.cloud** (Rust engine, GitHub: [spider-rs/spider](https://github.com/spider-rs/spider)) claims to be the cheapest crawler API at ~$0.48/1K pages average, with a built-in multimodal LLM agent for navigation and CAPTCHA solving.

The **agentic scraping** category exploded in 2025–2026. **Browser Use** (GitHub: [browser-use/browser-use](https://github.com/browser-use/browser-use), **84.9K stars**, v0.12.5, March 2026) is a Playwright-based library making websites accessible to AI agents with 89% success on WebVoyager benchmark. It supports any LLM (Gemini, Claude, GPT-4, local models) and launched a managed Cloud service. **Skyvern** (GitHub: [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern), 20K+ stars, YC-backed) takes a vision-first approach -- it understands pages via screenshots rather than DOM parsing, making it inherently resistant to layout changes. **Stagehand** (GitHub: [browserbase/stagehand](https://github.com/browserbase/stagehand), 21K stars) provides auto-caching with self-healing: it caches element locations and reinvokes AI only when layouts change.

The hybrid pattern for cost-effective production scraping has crystallized: **use CSS selectors for stable high-volume fields** ($0 per extraction) **with LLM fallback when selectors fail** (~$0.01 per repair). A 2025 DataRobot study found LLM-powered scrapers required **70% less maintenance** than traditional scrapers.

---

## GraphQL reverse engineering got powerful integrated tooling

**InQL v6.1.0** (GitHub: [doyensec/inql](https://github.com/doyensec/inql), December 2025) is the biggest development -- a complete rewrite from Jython to Kotlin integrating three previously separate tools: a **schema brute-forcer** (Clairvoyance-inspired "did you mean…" suggestion abuse), an **engine fingerprinter** (graphw00f-style), and the existing scanner/query builder. It includes built-in GraphiQL and GraphQL Voyager servers.

**Clairvoyance** (GitHub: [nikitastupin/clairvoyance](https://github.com/nikitastupin/clairvoyance)) remains the standalone tool for schema discovery when introspection is disabled, exploiting GraphQL's field suggestion feature with wordlist-based probing. An enhanced fork, **clairvoyancex**, adds httpx support for HTTP/2 and proxy compatibility. Escape.tech contributed a specialized **GraphQL wordlist** extracted from 60,000+ schemas discovered via their Goctopus reconnaissance tool.

For persisted query reverse engineering, the **mitmproxy technique** is the standard approach: intercept requests, replace the `sha256Hash` with a bogus value, force a `PersistedQueryNotFound` error, and the client retransmits with the full query text.

```python
import json
def request(flow):
    try:
        dat = json.loads(flow.request.text)
        dat[0]["extensions"]["persistedQuery"]["sha256Hash"] = "0d9e"
        flow.request.text = json.dumps(dat)
    except: pass
```

Bypass techniques against disabled introspection continue to work: regex-based blocks often fail against whitespace variations (newlines after `__schema`), some implementations only block POST (try GET), and inline fragment attacks (CVE-2026-30854, disclosed March 2026, affecting Parse Server) show that shallow security checks remain exploitable.

---

## Rate limiting, observability, and the production scraping stack

For rate limiting, **pyrate-limiter v4** (GitHub: [vutran1710/PyrateLimiter](https://github.com/vutran1710/PyrateLimiter), PyPI v4.0.2) is the most capable option with sync/async support, InMemoryBucket, RedisBucket (for distributed scraping clusters), and SQLiteBucket backends, plus built-in `httpx` and `aiohttp` transport integrations. **aiolimiter** (v1.2.1) remains the simplest asyncio rate limiter. Scrapy's AutoThrottle dynamically adjusts download delay based on server latency and remains production-proven. New in Scrapy 2.13: the template now defaults to `DOWNLOAD_DELAY=1` and `CONCURRENT_REQUESTS_PER_DOMAIN=1` -- a clear industry signal toward conservative defaults.

```python
from pyrate_limiter import Duration, Rate, Limiter, RedisBucket
from redis import Redis

# Multi-tier distributed rate limiting
hourly = Rate(500, Duration.HOUR)
daily = Rate(5000, Duration.DAY)
bucket = RedisBucket.init([hourly, daily], Redis(), "scraper-bucket")
limiter = Limiter(bucket)
limiter.try_acquire("request_id")  # Blocks until permit available
```

The recommended **production observability stack** for scrapers in 2026 centers on Prometheus + Grafana (metrics and visualization), structlog or Loguru for structured JSON logging piped to Grafana Loki, OpenTelemetry for distributed tracing to Grafana Tempo, and **Spidermon** (PyPI v1.25.0) for Scrapy-specific data validation and alerting. Apify migrated from New Relic to self-hosted Grafana in early 2025 at roughly 1/10th the cost of Grafana Cloud -- a pattern representative of the broader industry move toward open-source observability stacks. Key metrics to track: success rate (2xx vs 4xx/5xx), 429 rate, items per run, proxy error rates, field coverage (schema validation), and queue depth.

A new concept emerging is **"legal observability"** -- consent-aware routing, `robots.txt` compliance logging, and jurisdictional audit trails driven by GDPR and DSA enforcement requirements.

---

## The legal landscape crystallized around public data rights and AI training

The hiQ v. LinkedIn saga reached its conclusion. The Ninth Circuit's 2022 reaffirmation that **scraping publicly available data does not violate the CFAA** stands as precedent (reinforced by the Supreme Court's Van Buren decision). However, the December 2023 settlement saw hiQ pay $500,000, cease scraping, and destroy all data -- with the critical detail that hiQ's contractors had created fake accounts to scrape behind login walls. The lesson: **public data scraping is legally defensible; circumventing access controls is not**.

**Meta v. Bright Data** (2024) reinforced this, with a judge finding that scraping publicly available data while logged out may not violate Meta's Terms of Service since no contract was formed without login. The **Clearview AI settlement** (March 2025, $51.75 million, including a unique 23% equity stake for the class) addressed biometric privacy under Illinois BIPA for scraping 50–60 billion images.

The frontier has shifted to **AI training data**. Over **70 AI scraping lawsuits** have been filed as of early 2026. Reddit v. Perplexity AI (late 2025) invokes DMCA Section 1201 against circumvention of rate limits and anti-bot systems. NYT v. OpenAI remains in discovery. Google v. SerpApi (early 2025) alleges DMCA circumvention for systematic search result scraping. The **AI Accountability for Publishers Act** (proposed February 2026 by the IAB) would let publishers sue AI companies deploying bots that scrape without consent.

On the regulatory front, **CNIL (France) published web scraping guidelines** in June 2025, establishing that even "public" web pages containing personal data require GDPR safeguards -- mandatory exclusion of sites opposing scraping via `robots.txt`, immediate deletion of non-relevant data, and broad notification to data subjects. KASPR was fined **€240,000** for scraping LinkedIn data without consent. The **EU AI Act** (effective August 2, 2026) requires AI developers to respect machine-readable opt-outs, publish training data summaries, and maintain traceability logs, with penalties up to €10 million or 2% of annual turnover. A UK court ruled in late 2025 that Stability AI's model weights do not constitute "infringing copies" of Getty's images -- a significant precedent for AI training.

`robots.txt` is increasingly treated as a **quasi-legal consent signal** rather than merely advisory. CNIL explicitly endorses it, the proposed AI Accountability Act would make it potentially enforceable, and Crawlee v1.0 now respects it by default.

---

## Conclusion: what actually changed

Three shifts define the 2025–2026 era. First, **detection moved from static fingerprinting to dynamic behavioral analysis** -- tools that perfectly spoof every browser attribute still get caught by mouse movement patterns, scroll velocity, and navigation flow. This has made pure HTTP-level scraping (curl_cffi, primp) more valuable than ever for targets without behavioral checks, while making browser-level scraping far more complex for targets that do check behavior.

Second, **AI became bidirectional** -- it powers both detection (per-customer ML models, behavioral scoring pipelines, LLM-based traffic classification) and evasion (agentic scrapers, self-healing selectors, schema-driven extraction). The cost of maintaining scrapers dropped dramatically for teams adopting LLM-driven extraction, but the cost of evading detection increased.

Third, **the legal Overton window narrowed for commercial AI training** while remaining stable for traditional data scraping. Public data scraping retains CFAA protection, but AI training use faces escalating litigation risk and regulatory requirements, particularly in the EU under the AI Act.

The winning stack in 2026 for a production scraping operation looks like this: **curl_cffi** (with `impersonate="chrome"`) for HTTP-level requests against sites without JS challenges, **Patchright or Nodriver** for browser automation against protected targets, **Crawlee or Scrapy** for orchestration, **residential proxies** (Decodo for value, Bright Data for features) with tiered escalation, **pyrate-limiter with Redis** for distributed rate limiting, **structlog + Prometheus + Grafana** for observability, and **Crawl4AI or Firecrawl** for LLM-ready output. For each target, the key decision is how many layers of evasion are needed -- and increasingly, whether a managed Web Unlocker API makes more economic sense than building and maintaining the full stack yourself.