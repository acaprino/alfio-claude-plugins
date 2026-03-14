---
description: "Marketing material and conversion optimization audit — UX patterns, CTAs, social media, copy quality, product presentation, and visual media with parallel analysis and persistent report"
argument-hint: "<url or local path> [--focus <areas>] [--competitor <url>] [--social] [--strict-mode]"
---

# Content Strategy Audit

## CRITICAL RULES

1. **Execute phases in order.** Scope → Parallel Audit → Synthesis → Approval → Apply → Report.
2. **Write output files.** Each phase writes to `.content-strategy/` for persistence.
3. **Run audit agents in parallel.** Phase 2 fires multiple agents simultaneously.
4. **Stop at checkpoint.** Get user approval before applying any changes.
5. **Use Playwright for live sites.** Browser tools for DOM, screenshots, responsive testing.
6. **Never enter plan mode.** Execute immediately.

## Pre-flight

### Dependency check (live sites only)

For live URL targets, this command uses Playwright MCP tools for browser-based analysis. If Playwright MCP tools (`browser_navigate`, `browser_snapshot`, etc.) are not available, warn the user:

```
Optional plugin missing: playwright-skill

Live site analysis works best with Playwright MCP tools for DOM inspection,
screenshots, and responsive testing. Without it, analysis will be limited
to what can be fetched via WebFetch/curl.

Install it with:
  claude plugin marketplace add acaprino/anvil-toolset --plugin playwright-skill
```

If Playwright tools are unavailable, fall back to WebFetch for fetching pages and analyze the raw HTML instead. Skip browser-specific checks (screenshots, responsive resize).

### Initialize

Create `.content-strategy/` directory. If it exists, ask to archive or overwrite.

Use the `content-marketer` agent for analysis.

## Phase 1: Audit Scope

1. **Read target** — navigate to URL (Playwright) or read local files
2. **Identify page types** — landing, product, blog, about, pricing, checkout, FAQ
3. **Understand the business** — extract value proposition, target audience, offering
4. **Baseline metrics** — page count, CTA count, form count, social links

**Output file:** `.content-strategy/01-scope.md`

Present scope summary and confirm focus areas.

---

## Phase 2: Parallel Audit (3 agents)

Run all three audit agents **in parallel** in a single response:

### Agent A: UX & Conversion Analysis

```
Task:
  subagent_type: "content-marketer"
  description: "UX and conversion optimization audit"
  prompt: |
    Audit the UX patterns and conversion elements of this website/page.

    ## Scope
    [Insert contents of .content-strategy/01-scope.md]

    ## Page Contents
    [Insert key page content or Playwright snapshot]

    ## Instructions
    Evaluate:
    1. **Page Layout**: Visual hierarchy, above-the-fold content, whitespace, content flow
    2. **CTAs**: Presence, clarity, contrast, placement, urgency, primary/secondary hierarchy
    3. **Social Proof**: Testimonials, reviews, trust badges, client logos, case studies, numbers
    4. **Pricing**: Clarity, comparison table, anchoring, free trial CTA, FAQ, guarantee
    5. **Forms**: Field count, labels, error handling, progress indicators, mobile-friendly
    6. **Navigation**: Hierarchy, breadcrumbs, search, mobile menu, sticky header, footer

    For each finding: severity (Critical/Important/Nice-to-have), element, issue, specific fix.
    Note what's working well.

    Return structured findings.
```

### Agent B: Content & Copy Analysis

```
Task:
  subagent_type: "content-marketer"
  description: "Content and copy quality audit"
  prompt: |
    Audit the written content and copy of this website/page.

    ## Scope
    [Insert contents of .content-strategy/01-scope.md]

    ## Page Contents
    [Insert key page text content]

    ## Instructions
    Evaluate:
    1. **Headlines**: Clarity (5-second test), benefit-driven, keyword presence, emotional triggers
    2. **Body Copy**: Scannable, benefit-focused, objection handling, specificity, reading level
    3. **Tone & Voice**: Consistency, audience-appropriate, brand alignment, authenticity
    4. **SEO Copy**: Keyword density, internal links, meta descriptions, featured snippet targeting
    5. **Microcopy**: Button labels, form hints, error messages, empty states, confirmations
    6. **Product Descriptions**: Feature→benefit framing, specifications, comparisons, use cases

    For each finding: severity, location, issue, specific rewrite suggestion.
    Note what's working well.

    Return structured findings.
```

### Agent C: Social Media & Visual Audit

```
Task:
  subagent_type: "content-marketer"
  description: "Social media and visual media audit"
  prompt: |
    Audit the social media presence and visual assets of this website/page.

    ## Scope
    [Insert contents of .content-strategy/01-scope.md]

    ## Page Contents
    [Insert page content and OG/meta tag data]

    ## Instructions
    Evaluate:
    1. **OG/Twitter Tags**: Presence, quality, share preview appearance
    2. **Social Profiles**: Linked from site, consistent branding, active presence
    3. **Share Buttons**: Placement, platform selection, mobile-friendly
    4. **Images**: Quality, relevance, consistency, alt text, performance
    5. **Product Gallery**: Count, angles, zoom, lifestyle shots, consistency
    6. **Video**: Hero video, demos, testimonials, thumbnails, loading behavior
    7. **Icons & Illustrations**: Consistent style, meaningful, accessible

    For each finding: severity, element, issue, specific fix.
    Note what's working well.

    Return structured findings.
```

Consolidate all agent findings into **`.content-strategy/02-audit.md`**:

```markdown
# Phase 2: Content Strategy Audit

## UX & Conversion Findings
[From Agent A, organized by severity]

## Content & Copy Findings
[From Agent B, organized by severity]

## Social & Visual Findings
[From Agent C, organized by severity]

## What's Working Well
[Positives from all agents]
```

---

## Phase 3: Synthesize & Prioritize

Read `.content-strategy/02-audit.md` and create actionable plan.

**Output file:** `.content-strategy/03-plan.md`

```markdown
# Content Strategy Plan

## Findings Summary
| Category | Critical | Important | Nice-to-have |
|----------|----------|-----------|--------------|
| UX & Conversion | X | X | X |
| Content & Copy | X | X | X |
| Social & Visual | X | X | X |
| **Total** | **X** | **X** | **X** |

## Quick Wins (high impact, low effort)
[Numbered list with specific before/after examples]

## Medium Effort
[Changes requiring moderate work]

## Major Recommendations
[Bigger changes requiring design/content decisions]

## Estimated Conversion Impact
[Which changes are most likely to improve conversion, ordered by expected impact]
```

---

## PHASE CHECKPOINT -- User Approval Required

```
Content strategy audit complete.

Findings: [X critical, Y important, Z nice-to-have]
Quick wins available: [count]

Please review:
- .content-strategy/02-audit.md
- .content-strategy/03-plan.md

1. Apply quick wins — implement high-impact, low-effort changes
2. Apply all fixable items — implement everything that doesn't need design decisions
3. Choose specific improvements — I'll tell you which ones
4. Report only — skip implementation, generate final report
```

Do NOT proceed until the user approves.

---

## Phase 4: Apply Changes

Implement approved changes in logical order:
1. Copy improvements first (headlines, CTAs, microcopy)
2. Structure changes (layout, navigation, form optimization)
3. Media optimization (images, OG tags, social)

Log changes to **`.content-strategy/04-changes.md`**:

```markdown
# Changes Applied

## Change 1: [description]
- Category: [UX/Content/Social]
- Before: [state]
- After: [state]
- Expected impact: [description]
```

---

## Phase 5: Final Report

Read all `.content-strategy/*.md` files and generate consolidated report.

**Output file:** `.content-strategy/05-report.md`

```markdown
# Content Strategy Audit Report

## Target: [URL or path]
## Date: [timestamp]

## Executive Summary
[2-3 sentences on marketing effectiveness]

## Findings by Category
| Category | Critical | Important | Nice-to-have | Fixed |
|----------|----------|-----------|--------------|-------|
| UX & Conversion | X | X | X | X |
| Content & Copy | X | X | X | X |
| Social & Visual | X | X | X | X |

## Changes Applied
[Summary with before/after highlights]

## Remaining Recommendations
[Items requiring manual intervention: photography, video, design work, A/B testing]

## Ongoing Strategy
- Content calendar suggestions
- A/B testing opportunities
- Metrics to track
- Review frequency

## Audit Metadata
- Agents used: 3 (UX, Content, Social)
- Total findings: [count]
- Fixes applied: [count]
```

---

## Completion

```
Content strategy audit complete for: $ARGUMENTS

Output Files:
- Scope: .content-strategy/01-scope.md
- Audit: .content-strategy/02-audit.md
- Plan: .content-strategy/03-plan.md
- Changes: .content-strategy/04-changes.md
- Report: .content-strategy/05-report.md

Findings: [X critical, Y important, Z nice-to-have]
Changes applied: [count]
```

## Quick Examples

- `/content-strategy https://example.com` — Full marketing audit
- `/content-strategy https://example.com/pricing` — Pricing page conversion optimization
- `/content-strategy src/pages/landing.html` — Audit local landing page
- `/content-strategy https://example.com --focus cta,social-proof` — Focused audit
- `/content-strategy https://example.com --social` — Social media presence focus
- `/content-strategy https://example.com --competitor https://rival.com` — Comparative audit
