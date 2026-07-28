# Digital Marketing Plugin

> Drive organic traffic and conversions. Technical SEO audits, content strategy, and marketing optimization with Playwright-powered analysis and persistent reports.

## Agents

### `seo-specialist`

Expert SEO strategist specializing in technical SEO, content optimization, and search engine rankings.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Technical SEO audits, keyword research, on-page optimization, structured data |

**Invocation:**
```
Use the seo-specialist agent to [audit/optimize/research] [target]
```

**Expertise:**
- Technical SEO audits (crawl errors, broken links, redirect chains)
- Keyword research and competition analysis
- On-page optimization and content structure
- Structured data / schema markup implementation
- Core Web Vitals and performance optimization
- E-E-A-T factors and algorithm update recovery

---

### `content-marketer`

Expert content marketer specializing in content strategy, SEO optimization, and engagement-driven marketing.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Content strategy, editorial calendars, campaign management, lead generation |

**Invocation:**
```
Use the content-marketer agent to [plan/create/optimize] [content/campaign]
```

**Expertise:**
- Content strategy and editorial planning
- Multi-channel content creation (blog, email, social, video)
- SEO-optimized content production
- Lead generation and conversion optimization
- Analytics, A/B testing, and ROI measurement
- Brand voice consistency and thought leadership

---

> **Moved:** prose humanization (the `text-humanizer` agent, the `/humanize-text` command, and the `anti-ai-writing-patterns` knowledge base) now lives in the standalone [text-humanizer](text-humanizer.md) plugin, a hard dependency of this one. SEO flows route to `/text-humanizer:humanize-text`.

---

### `ga4-implementation-expert`

GA4 + GTM implementation expert with deep focus on EU/GDPR Consent Mode v2 compliance, custom event tracking, conversion (Key Event) configuration, remarketing audiences, and diagnostic analysis.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | GA4 / GTM deployment, Consent Mode v2 compliance, CMP integration (iubenda, Cookiebot, Orestbida CookieConsent), Key Event + Google Ads conversion import, Enhanced Conversions, remarketing audiences, "why isn't my site converting" diagnostics |

**Invocation:**
```
Use the ga4-implementation-expert agent to [implement/audit/debug] [GA4 or GTM setup]
```

**Frameworks covered:** vanilla HTML, Next.js / React, WordPress. Handles dataLayer event taxonomy design, server-side vs client-side tagging, and the full `gtag('consent', 'default' | 'update', ...)` flow with the 4-granular-signal EU pattern (`ad_storage`, `ad_user_data`, `ad_personalization`, `analytics_storage`).

---

### `llm-seo-optimize`

Answer-engine optimization (AEO) specialist for Google AI Overviews / SGE, Perplexity, ChatGPT Search, Claude with web search, and Bing Copilot. Different from traditional SEO: AEO optimizes for getting **cited inside the LLM-generated answer**, not just ranking on a SERP.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Auditing a site for AI-search discoverability, checking E-E-A-T signals, optimizing passage-level extractability, reviewing JSON-LD / Schema.org, diagnosing low citation rate in LLM answers |

**Invocation:**
```
Use the llm-seo-optimize agent to audit [url or local path] for answer-engine optimization
```

**6-phase audit:**
1. **Crawler access** - full robots.txt user-agent matrix for 12 AI bots (GPTBot, ChatGPT-User, OAI-SearchBot, PerplexityBot, Perplexity-User, Google-Extended, Googlebot, ClaudeBot, anthropic-ai, Applebot-Extended, Bytespider, CCBot) with train-vs-retrieve distinction
2. **E-E-A-T signals** - author bylines with credentials, publication + last-updated dates in ISO + JSON-LD, primary-source citations, first-hand experience markers, fact-check structure
3. **Passage-level extractability** - direct-answer first paragraphs, one-question-per-H2, bulleted fact lists, tables with captions, numbers with unit + date + source
4. **Structured data** - JSON-LD for Article / HowTo / FAQPage / Product / Dataset / ClaimReview / SoftwareApplication / Organization + sameAs
5. **Citation readiness** - canonical URL, section-anchor permalinks, cite-this-article block, clear licensing, downloadable data
6. **Prompt-injection hardening** - audit hidden text, invisible CSS, JSON-LD / alt-text / comment payloads that reach the LLM context

**Also covers:** `llms.txt` / `llms-full.txt` proposed standards, AI-referral analytics setup (chatgpt.com / perplexity.ai / claude.ai / copilot.microsoft.com hostnames), weekly brand-mention citation-share tracking, GSC AI Overviews impression metrics.

---

## Skills

### `brand-naming`

Brand naming strategist. Generates, filters, scores, and validates brand names through a lateral thinking workflow.

| | |
|---|---|
| **Invoke** | Skill reference or `/brand-naming` |
| **Trigger** | "brand name", "naming", "name my app", "name my product", "startup name" |

**Workflow:** Uses 4 lateral thinking techniques (semantic collision, vocabulary shift, invisible hinge, polarization) for creative generation, then filters with 7 naming archetypes, linguistic/phonotactic rules, weighted scoring, domain availability checks, market saturation analysis, trademark pre-screening, and SEO analysis.

---

### `domain-hunter`

Search domains, compare registrar prices, find promo codes, and get purchase recommendations.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | "buy a domain", "domain prices", "domain deals", "compare registrars", ".ai domain", ".com domain" |

**Source:** Ported from [ReScienceLab/opc-skills](https://github.com/ReScienceLab/opc-skills).

**Includes:** `references/registrars.md` (registrar comparison) and `references/spaceship-api.md` (Spaceship API docs).

---

### `reply-to-customer-review`

Generate professional, empathetic, on-brand replies to online customer reviews. Sentiment analysis, severity detection, adaptive tone, operational suggestions.

| | |
|---|---|
| **Invoke** | Skill reference or `/reply-to-customer-review` |
| **Trigger** | "reply to review", "respond to customer", "review response", Airbnb / Booking / Tripadvisor / Amazon / App Store / Trustpilot reviews |

**Sectors covered:** hospitality (Airbnb, Booking, Tripadvisor) and e-commerce / app (Amazon, App Store, Trustpilot) with sector-specific phrasing patterns. Detects negative / neutral / positive sentiment and calibrates tone (formal / friendly / casual). Flags operational issues (repeated complaint pattern) worth escalating.

---

### `ga4-implementation`

Knowledge base for implementing GA4 + GTM with EU/GDPR Consent Mode v2 compliance. Referenced by the `ga4-implementation-expert` agent.

| | |
|---|---|
| **Invoke** | Skill reference (auto-loaded by ga4-implementation-expert) |
| **Trigger** | GA4 / GTM deployment, Consent Mode v2, CMP selection, event taxonomy, conversion config, remarketing audiences |

**Content:** CMP selection guide (iubenda, Orestbida CookieConsent, Cookiebot comparison), Consent Mode v2 default + update templates, event taxonomy (recommended + custom), Key Event configuration, Google Ads conversion import, Enhanced Conversions, Predictive Audiences 28-day backfill note, framework-specific integration (Next.js / React, WordPress, vanilla HTML).

---

## Commands

### `/brand-naming`

Generate, filter, score, and validate brand names through a structured naming workflow.

```
/brand-naming "fitness app for busy professionals"
/brand-naming "sustainable fashion marketplace" --style evocative --tlds .com,.co,.app
```

| Flag | Effect |
|------|--------|
| `--style` | Focus on descriptive, abstract, evocative, or all (default: all) |
| `--languages` | Languages to check for cultural conflicts (default: en,it,es,fr,de,pt) |
| `--tlds` | TLDs to check for domain availability (default: .com,.app,.io,.co) |

---

### `/seo-audit`

5-phase technical SEO audit with Playwright analysis, scoring, a checkpoint before applying fixes, and a persistent report.

```
/seo-audit https://example.com
```

**Phases:** Discovery -> Technical Audit -> Score -> (Checkpoint) -> Fix -> Report

**Output:** `.seo-audit/` directory with discovery, audit, scorecard, fixes, and final report.

---

### `/content-strategy`

Marketing and conversion audit. Runs 3 parallel agents (UX/Conversion, Content/Copy, Social/Visual) with a checkpoint before applying changes and a persistent report.

```
/content-strategy https://example.com
```

**Phases:** Scope -> Parallel Audit (3 agents) -> Synthesis -> (Checkpoint) -> Apply -> Report

**Output:** `.content-strategy/` directory with scope, audit, plan, changes, and final report.

---

### `/reply-to-customer-review`

Generate a sentiment-calibrated, sector-aware reply to a customer review.

```
/reply-to-customer-review "Stay was ok but WiFi was slow" --brand "Hotel X" --tone friendly --sector hospitality
/reply-to-customer-review "App crashed on checkout" --brand "MyApp" --lang en --sector ecommerce
```

| Flag | Effect |
|------|--------|
| `--brand` | Brand / product name to reference |
| `--tone` | `formal` / `friendly` / `casual` (auto-detected if omitted) |
| `--lang` | Response language (ISO 639-1 code) |
| `--sector` | `hospitality` / `ecommerce` / `auto` |

---

### `/ga4-audit`

Playwright-verified GA4 + GTM audit covering Consent Mode v2 compliance, Key Event configuration, remarketing audiences, Ads linking, and CMP integration.

```
/ga4-audit https://example.com
/ga4-audit https://example.com --gtm GTM-XXXXXX
/ga4-audit https://example.com --strict-mode       # CI: exit 1 on any critical finding
```

**5-phase audit:** Discovery (CMP + GTM / GA4 ID detection) -> Live verification via Playwright (dataLayer state pre-consent vs post-consent, event coverage per page type) -> Configuration audit (GA4 property, Key Events, Audiences, Ads linking) -> Consent Mode v2 deep check (default / update calls, granular 4-signal mapping, `wait_for_update`) -> Report with prioritized fixes.

**Output:** `.ga4-audit/` directory with discovery, verification log, config audit, consent-mode findings, and final REPORT.md.

---

### `/llm-seo-audit`

Answer-engine optimization (AEO) audit. Different from `/seo-audit` - optimizes for getting cited inside LLM-generated answers (Google AI Overviews, Perplexity, ChatGPT Search, Claude Search, Bing Copilot) rather than ranking on traditional SERPs.

```
/llm-seo-audit https://example.com
/llm-seo-audit https://example.com --focus schema,eeat    # target two dimensions
/llm-seo-audit ./dist/                                    # static site audit
/llm-seo-audit https://example.com --strict-mode          # CI-friendly
```

| Flag | Effect |
|------|--------|
| `--focus` | `crawlers` / `eeat` / `schema` / `passages` / `injection` / `all` (default) |
| `--strict-mode` | Treat warnings as blockers, exit 1 on any critical finding |

Delegates to the `llm-seo-optimize` agent (6-phase protocol). Output: `.aeo-audit/REPORT.md` with crawler-access matrix, E-E-A-T and extractability scores, JSON-LD coverage, priority fixes, AI-referral tracking setup.

---

**Related:** [research](research.md) (deep research for content strategy) | [playwright-skill](https://github.com/lackeyjb/playwright-skill) (upstream plugin, required for browser-based SEO / GA4 / AEO audits; install: `claude plugin marketplace add lackeyjb/playwright-skill`, then `claude plugin install playwright-skill@playwright-skill`)
