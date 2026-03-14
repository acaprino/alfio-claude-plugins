---
description: "Comprehensive technical SEO audit with Playwright-powered analysis, scoring, prioritized fixes, and a persistent markdown report"
argument-hint: "<url or local path> [--focus <categories>] [--competitor <url>] [--local] [--strict-mode]"
---

# SEO Audit

## CRITICAL RULES

1. **Execute phases in order.** Discovery → Audit → Score → (Approval) → Fix → Report.
2. **Write output files.** Each phase writes to `.seo-audit/` for persistence.
3. **Stop at checkpoint.** Get user approval before applying any fixes (Phase 4).
4. **Use Playwright for live sites.** Browser tools for DOM, console, network, responsive testing.
5. **Never enter plan mode.** Execute immediately.

## Pre-flight

### Dependency check (live sites only)

For live URL targets (not `--local`), this command uses Playwright MCP tools for browser-based analysis. If Playwright MCP tools (`browser_navigate`, `browser_snapshot`, etc.) are not available, warn the user:

```
Optional plugin missing: playwright-skill

Live site analysis works best with Playwright MCP tools for DOM inspection,
responsive testing, and network analysis. Without it, analysis will be
limited to what can be fetched via WebFetch/curl.

Install it with:
  claude plugin marketplace add acaprino/anvil-toolset --plugin playwright-skill
```

If Playwright tools are unavailable, fall back to WebFetch for fetching pages and analyze the raw HTML instead. Skip browser-specific checks (console messages, network requests, responsive resize).

### Initialize

Create `.seo-audit/` directory. If it exists with a previous audit, ask to archive or overwrite.

Use the `seo-specialist` agent for all analysis.

## Phase 1: Discovery

Gather baseline information before auditing.

1. **Fetch target** — navigate to URL with Playwright, or read local files
2. **Robots.txt** — fetch `/robots.txt`, check rules, crawl-delay
3. **Sitemap** — fetch `/sitemap.xml`, count URLs, check lastmod dates
4. **Tech detection** — identify CMS/framework from headers, meta generators, DOM patterns
5. **Site structure** — map primary navigation, identify page types

**Output file:** `.seo-audit/01-discovery.md`

Present discovery summary and confirm scope before proceeding.

---

## Phase 2: Technical Audit

Run every check below. Use Playwright `browser_snapshot` for DOM, `browser_evaluate` for JS checks, `browser_network_requests` for resources, `browser_console_messages` for errors, `browser_resize` for responsive testing.

**Core SEO** — Meta title (50-60 chars), meta description (120-160 chars), canonical URL, Open Graph tags, Twitter Cards

**Headings** — Exactly 1 H1, proper hierarchy, keywords in H1

**Links** — Internal link depth, broken links (sample top 20), redirect chains, orphan pages

**Images** — Alt text, descriptive filenames, lazy loading, WebP/AVIF, dimensions

**Performance** — Transfer size, request count, Core Web Vitals hints, caching, compression

**Security** — HTTPS enforced, security headers (CSP, HSTS, X-Frame-Options), no mixed content

**Structured Data** — JSON-LD present, valid schema, Rich Results eligibility

**Mobile** — Viewport meta, responsive (375px/768px/1280px), touch targets 44px+, no horizontal scroll

**Crawlability** — robots.txt not blocking important pages, valid sitemap, noindex only on intended pages

**Content Quality** — Word count (flag <300), duplicate titles/descriptions, keyword density

**URL Structure** — Clean slugs, under 75 chars, keywords in path

**Accessibility** — ARIA landmarks, alt text, color contrast, skip nav, form labels, focus indicators

**E-E-A-T Signals** — Author info, about page, contact page, trust signals, citations

**Local SEO** (if applicable) — NAP consistency, LocalBusiness schema, geo tags

**Internationalization** (if applicable) — hreflang tags, lang attribute

**Output file:** `.seo-audit/02-technical-audit.md`

---

## Phase 3: Score & Prioritize

Calculate scores from Phase 2 findings.

1. **Health score**: 0-100 with letter grade (A: 90+, B: 80+, C: 70+, D: 60+, F: <60)
2. **Category breakdown**: score each section
3. **Issue severity**:
   - **Error** (red): broken functionality, missing critical elements, security issues
   - **Warning** (yellow): suboptimal but functional, missed opportunities
   - **Notice** (blue): nice-to-have, best practices
4. **Prioritized fix list**: rank by impact x effort, group into quick wins / medium effort / major projects

**Output file:** `.seo-audit/03-scorecard.md`

```markdown
# SEO Scorecard

## Overall: [X]/100 — Grade [A-F]

| Category | Score | Errors | Warnings | Notices |
|----------|-------|--------|----------|---------|
| Core SEO | X/100 | X | X | X |
| Headings | X/100 | X | X | X |
| Links | X/100 | X | X | X |
| Images | X/100 | X | X | X |
| Performance | X/100 | X | X | X |
| Security | X/100 | X | X | X |
| Structured Data | X/100 | X | X | X |
| Mobile | X/100 | X | X | X |
| Crawlability | X/100 | X | X | X |
| Content | X/100 | X | X | X |
| URLs | X/100 | X | X | X |
| Accessibility | X/100 | X | X | X |
| E-E-A-T | X/100 | X | X | X |

## Quick Wins
[High impact, low effort fixes]

## Medium Effort
[Moderate impact improvements]

## Major Projects
[Significant changes requiring design/content decisions]
```

---

## PHASE CHECKPOINT -- User Approval Required

Present the scorecard and ask:

```
SEO Audit scored: [X]/100 (Grade [letter])

Errors: [count] | Warnings: [count] | Notices: [count]
Quick wins available: [count]

Please review:
- .seo-audit/02-technical-audit.md
- .seo-audit/03-scorecard.md

1. Fix quick wins — apply high-impact, low-effort fixes
2. Fix all — apply all fixable issues
3. Choose specific fixes — I'll tell you which ones
4. Report only — skip fixes, generate final report
```

Do NOT proceed to Phase 4 until the user approves. If `--strict-mode` and Errors exist, recommend fixing all errors.

---

## Phase 4: Fix & Iterate

Apply approved fixes only.

1. **Batch fixes**: group related changes, apply in logical order
2. **Re-audit changed elements**: verify fixes resolved the issues
3. **Log changes**: before/after for each fix

**Output file:** `.seo-audit/04-fixes.md`

```markdown
# Fixes Applied

## Fix 1: [description]
- Category: [category]
- Before: [state]
- After: [state]
- Impact: [score change]

## Fix 2: ...
```

---

## Phase 5: Final Report

Read all `.seo-audit/*.md` files and generate the consolidated report.

**Output file:** `.seo-audit/05-report.md`

```markdown
# SEO Audit Report

## Target: [URL or path]
## Date: [timestamp]

## Executive Summary
[2-3 sentences on overall SEO health]

## Score Summary
| | Before | After | Change |
|---|--------|-------|--------|
| Overall | X/100 | Y/100 | +Z |
| Grade | [letter] | [letter] | |

## Category Scores
[Table from Phase 3, updated with post-fix scores]

## Issues Fixed
[Summary from Phase 4]

## Remaining Issues
[Items requiring manual intervention: content rewrites, design decisions, server config]

## Recommendations
1. [Prioritized next steps]
2. [Monitoring recommendations: tools, frequency, key metrics]

## Audit Metadata
- Tool: Playwright + seo-specialist agent
- Categories audited: [count]
- Total checks: [count]
- Fixes applied: [count]
```

---

## Completion

```
SEO audit complete for: $ARGUMENTS

Output Files:
- Discovery: .seo-audit/01-discovery.md
- Technical Audit: .seo-audit/02-technical-audit.md
- Scorecard: .seo-audit/03-scorecard.md
- Fixes: .seo-audit/04-fixes.md
- Report: .seo-audit/05-report.md

Score: [X]/100 (Grade [letter]) → [Y]/100 (Grade [letter])
Fixes applied: [count]
Remaining issues: [count]
```

## Quick Examples

- `/seo-audit https://example.com` — Full technical SEO audit
- `/seo-audit https://example.com/products` — Audit specific section
- `/seo-audit src/pages --local` — Audit local HTML/template files
- `/seo-audit https://example.com --focus security,performance` — Focused audit
- `/seo-audit https://example.com --competitor https://rival.com` — Comparative audit
