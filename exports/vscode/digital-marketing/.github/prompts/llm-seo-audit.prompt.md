---
description: Answer-engine optimization (AEO) audit: optimize for being cited inside AI-generated answers (ChatGPT, Perplexity, Google AI Overviews / SGE, Claude, Bing Copilot), not classic Google ranking. Checks AI-bot crawler access, E-E-A-T signals, passage-level extractability, JSON-LD / Schema.org structured data, citation readiness, prompt-injection hardening, and llms.txt. Produces a prioritized fix list with concrete code. For traditional Google and Bing SERP ranking use /seo-audit instead. Use when the user asks to audit for AI search / answer engines, check Google AI Overviews / SGE visibility, optimize for Perplexity / ChatGPT Search / Claude Search / Bing Copilot, verify crawler allowlist for AI bots, check E-E-A-T signals, or diagnose low citation rate in LLM answers. Not for traditional organic SERP-ranking SEO, which /seo-audit covers, paid search, content tone and voice alone, which the content-marketer agent covers, or generic copywriting with no search dimension.
argument-hint: <url or local path> [--focus crawlers|eeat|schema|passages|injection|all] [--strict-mode]
---

# LLM SEO / Answer Engine Optimization Audit

Invokes the `llm-seo-optimize` agent to audit a site for answer-engine discoverability and citation-worthiness. Different from `/seo-audit` (traditional SERP ranking) -- this optimizes for getting **quoted inside an LLM-generated answer**.

## CRITICAL RULES

1. **Delegate to the `llm-seo-optimize` agent**. This command is a thin wrapper -- the agent owns the full 6-phase audit.
2. **Verify live, not just code**. If Playwright MCP is available, use it to confirm crawler access (`robots.txt` live fetch), JSON-LD presence, and rendered passage extractability.
3. **Write output to `.aeo-audit/` for persistence** so re-runs can diff against the baseline.
4. **Never fabricate crawler policies**. If `robots.txt` cannot be fetched, state the gap explicitly.
5. **Complementary to `/seo-audit`, not a replacement**. Traditional SEO and AEO require different optimizations -- flag the overlap, not duplication.

## Procedure

### 1. Parse arguments

- `<url or local path>`: required target -- live URL or path to static site / built HTML output
- `--focus`: restrict audit to a subset of dimensions (default: `all` -- runs every phase)
  - `crawlers` -- only the AI-bot robots.txt allowlist check
  - `eeat` -- only E-E-A-T signal audit (authorship, citations, dates)
  - `schema` -- only JSON-LD / Schema.org structured data
  - `passages` -- only passage-level extractability (direct-answer paragraphs, tables, bullet lists)
  - `injection` -- only prompt-injection hardening (hidden text, invisible CSS, comment payloads)
- `--strict-mode`: treat warnings as blockers and exit 1 if any critical finding remains (useful for CI)

### 2. Spawn the agent

Invoke `llm-seo-optimize` with the target, focus, and strict-mode flag. The agent loads its own knowledge base and runs the 6-phase protocol.

### 3. Report

Agent writes `.aeo-audit/REPORT.md` with:

```
# AEO Audit -- <site/page> -- <date>

## Summary
- Pages audited: N
- Blocked from: <list of engines with robots.txt denies>
- E-E-A-T score: X/5
- Extractability score: X/5
- JSON-LD coverage: P%

## Critical findings
- [CRITICAL] <page:line / selector> <issue>

## Per-page findings
...

## Cross-cutting recommendations
...

## Tracking setup
- Analytics filters for AI-referral hostnames (chatgpt.com, perplexity.ai, claude.ai, copilot.microsoft.com, gemini.google.com)
- Weekly brand-mention query set for citation-share tracking
```

## Typical flow

```
# Full audit against a live URL
/llm-seo-audit https://example.com

# Focus on Schema + E-E-A-T only
/llm-seo-audit https://example.com --focus schema,eeat

# Static site audit
/llm-seo-audit ./dist/

# CI-mode with strict blockers
/llm-seo-audit https://example.com --strict-mode
```

## Complementary commands

Run alongside traditional SEO tooling for a complete picture:

| Command | Purpose | Overlap with AEO |
|---------|---------|------------------|
| `/seo-audit` | Technical SEO (Core Web Vitals, meta tags, sitemap, redirects, SERP ranking) | Low -- traditional ranking signals |
| `/content-strategy` | Conversion / CTA / tone / funnel audit | Medium -- answer-worthiness often correlates with clarity |
| `/ga4-audit` | GA4 + GTM + Consent Mode v2 verification | Measurement only -- AEO needs AI-referrer tracking set up in GA4 |
| **`/llm-seo-audit`** | **AEO / answer-engine optimization** | -- |

## Synergies

- Deep knowledge base -> `llm-seo-optimize` agent (the actual worker)
- Structured data validation alongside broader checks -> `/seo-audit`
- Measurement setup -> `ga4-implementation-expert` agent (AI-referrer tracking)
- Humanizing AI-sounding copy to raise E-E-A-T -> `/humanize-text in the `text-humanizer` bundle` (text-humanizer plugin)
- Browser-based live verification -> the playwright-mcp MCP server
