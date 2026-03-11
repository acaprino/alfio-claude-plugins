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

## Commands

### `/seo-audit`

5-phase technical SEO audit with Playwright analysis, scoring, checkpoint before fixes, and persistent report.

```
/seo-audit https://example.com
```

**Phases:** Discovery -> Technical Audit -> Score -> (Checkpoint) -> Fix -> Report

**Output:** `.seo-audit/` directory with discovery, audit, scorecard, fixes, and final report.

---

### `/content-strategy`

Marketing and conversion audit using 3 parallel agents (UX/Conversion, Content/Copy, Social/Visual) with checkpoint before changes and persistent report.

```
/content-strategy https://example.com
```

**Phases:** Scope -> Parallel Audit (3 agents) -> Synthesis -> (Checkpoint) -> Apply -> Report

**Output:** `.content-strategy/` directory with scope, audit, plan, changes, and final report.
