---
description: >
  Answer-engine optimization (AEO) audit: optimize for being cited inside AI-generated answers (ChatGPT, Perplexity, Google AI Overviews / SGE, Claude, Bing Copilot), not classic Google ranking. Checks AI-bot crawler access, E-E-A-T signals, passage-level extractability, JSON-LD / Schema.org structured data, citation readiness, prompt-injection hardening, and llms.txt. Produces a prioritized fix list with concrete code. For traditional Google and Bing SERP ranking use /digital-marketing:seo-audit instead.
  TRIGGER WHEN: the user asks to audit for AI search / answer engines, check Google AI Overviews / SGE visibility, optimize for Perplexity / ChatGPT Search / Claude Search / Bing Copilot, verify crawler allowlist for AI bots, check E-E-A-T signals, or diagnose low citation rate in LLM answers.
  DO NOT TRIGGER WHEN: the task is traditional organic / SERP ranking SEO (use /digital-marketing:seo-audit), paid search, content tone / voice only (use content-marketer agent), or generic copywriting with no search dimension.
argument-hint: "<url or local path> [--focus <comma-separated: crawlers,eeat,schema,passages,injection | all>] [--strict-mode]"
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
- `--focus`: restrict the audit to a subset of dimensions. Values are comma-combinable (`--focus schema,eeat`). Default: `all`, which runs every phase
  - `crawlers` -- the AI-bot robots.txt allowlist check
  - `eeat` -- E-E-A-T signal audit (authorship, citations, dates)
  - `schema` -- JSON-LD / Schema.org structured data, plus citation readiness
  - `passages` -- passage-level extractability (direct-answer paragraphs, tables, bullet lists)
  - `injection` -- prompt-injection hardening (hidden text, invisible CSS, comment payloads)
- `--strict-mode`: report-level severity escalation. Every Warning is raised to Critical and the report opens with an explicit `VERDICT: PASS` / `VERDICT: FAIL` line, FAIL when any Critical remains

### 2. Spawn the agent

Invoke `digital-marketing:llm-seo-optimize` with the target, focus, and strict-mode flag. The agent loads its own knowledge base and runs the 6-phase protocol.

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
- Analytics filters for AI-referral hostnames: chatgpt.com (legacy chat.openai.com), perplexity.ai, claude.ai, copilot.microsoft.com, gemini.google.com
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

# Strict grading: warnings become critical, report opens with PASS/FAIL
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

- Deep knowledge base -> `digital-marketing:llm-seo-optimize` agent (the actual worker)
- Structured data validation alongside broader checks -> `/digital-marketing:seo-audit`
- Measurement setup -> `digital-marketing:ga4-implementation-expert` agent (AI-referrer tracking)
- Humanizing AI-sounding copy to raise E-E-A-T -> `/text-humanizer:humanize-text` (text-humanizer plugin)
- Playwright-based live verification -> `playwright-skill`
