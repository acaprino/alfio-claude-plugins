# Digital Marketing Plugin

> Drive organic traffic and conversions. Technical SEO audits, content strategy, and marketing optimization with Playwright-powered analysis and persistent reports.

## Agents

### `seo-specialist`

Expert SEO strategist specializing in technical SEO, content optimization, and search engine rankings.

| | |
|---|---|
| **Model** | `opus` |
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
| **Model** | `opus` |
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

**Related:** [research](research.md) (deep research for content strategy) | [frontend](frontend.md) (UI/UX for marketing pages) | [playwright-skill](playwright-skill.md) (browser automation for SEO audits)
