---
description: Reviews whether the material actually persuades a visitor, not whether it is well built. Use when the user asks for a content, marketing, conversion, or CRO audit of a website, landing page, or funnel. Not for technical-SEO-only audits (use /seo-audit).
argument-hint: <url or local path> [--focus <comma-separated areas>] [--social] [--strict-mode]
agent: content-marketer
---

# Content Strategy Audit

## CRITICAL RULES

1. **Execute phases in order.** Scope → Audit Passes → Synthesis → Approval → Apply → Report.
2. **Write output files.** Each phase writes to `.content-strategy/` for persistence.
3. **Run the three audit passes sequentially.** Phase 2 works through UX, content, and social one pass at a time.
4. **Stop at checkpoint.** Get user approval before applying any changes.
5. **Use Playwright for live sites.** Browser tools for DOM, screenshots, responsive testing.
6. **Never enter plan mode.** Execute immediately.

## Pre-flight

### Dependency check (live sites only)

For live URL targets, this command uses Playwright MCP tools for browser-based analysis. If Playwright MCP tools (`browser_navigate`, `browser_snapshot`, etc.) are not available, warn the user:

```
Playwright MCP tools are not available.

Live browser analysis needs them for DOM inspection, screenshots, and
responsive testing. Add the playwright-mcp server under
Settings > AI > Manage MCP Servers, then re-run this command.

  https://github.com/microsoft/playwright-mcp
```

If Playwright tools are unavailable, fall back to `#web/fetch` for fetching pages and analyze the raw HTML instead. Skip browser-specific checks (screenshots, responsive resize).

### Initialize

Create `.content-strategy/` directory. If it already exists, automatically rename the old one to `.content-strategy-archive-[timestamp]/` to prevent data loss, then create a fresh one. Do NOT ask for permission for this step.

Use the `content-marketer` agent for analysis.

## Phase 1: Audit Scope

### Parse flags

- `--focus <areas>`: comma-separated area names, resolved against the Phase 2 ownership map. Only the passes owning a requested area run; every area not requested is marked `not audited` in the Phase 3 table. Default: all areas
- `--social`: shorthand for `--focus social,images,video`, which runs Pass 3 alone
- `--strict-mode`: in Phase 3, promote every Important finding to Critical and open the plan with an explicit `VERDICT: PASS` / `VERDICT: FAIL` line. FAIL when any Critical remains

### Gather scope

1. **Read target** -- navigate to URL (Playwright) or read local files
2. **Identify page types** -- landing, product, blog, about, pricing, checkout, FAQ
3. **Understand the business** -- extract value proposition, target audience, offering
4. **Baseline metrics** -- page count, CTA count, form count, social links

**Output file:** `.content-strategy/01-scope.md`

### Shared context block

Assemble this once at the end of Phase 1. Every Phase 2 pass reuses it verbatim, so it is written here and nowhere else:

```
## Scope
[Contents of .content-strategy/01-scope.md]

## Target
[URL or local path, plus the resolved focus areas]

## Page Contents
[Key page content: Playwright snapshot or file text, including OG and meta tag data]
```

Present scope summary and confirm focus areas.

---

## Phase 2: Audit (3 passes)

Run the three passes below in order. Each is a distinct lens on the same target; keep their findings separate until Phase 3.

Area ownership, used to resolve `--focus`: Pass 1 owns `ux`, `cta`, `social-proof`, `pricing`, `forms`, `navigation`. Pass 2 owns `copy`, `seo-copy`, `microcopy`, `product-descriptions`. Pass 3 owns `social`, `images`, `video`. Skip any pass whose areas were all excluded, and report only on the requested areas in the passes that do run.

### Pass 1: UX & Conversion Analysis

Audit the UX patterns and conversion elements of this website/page.

[Shared context block from Phase 1, verbatim]

### Instructions
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

### Pass 2: Content & Copy Analysis

Audit the written content and copy of this website/page.

[Shared context block from Phase 1, verbatim]

### Instructions
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

### Pass 3: Social Media & Visual Audit

Audit the social media presence and visual assets of this website/page.

[Shared context block from Phase 1, verbatim]

### Instructions
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

Consolidate the findings of all three passes into **`.content-strategy/02-audit.md`**:

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

Read `.content-strategy/02-audit.md` and create actionable plan. If `--strict-mode` was passed, promote every Important finding to Critical before building the table, and open the plan with the `VERDICT:` line.

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

1. Apply quick wins -- implement high-impact, low-effort changes
2. Apply all fixable items -- implement everything that doesn't need design decisions
3. Choose specific improvements -- I'll tell you which ones
4. Report only -- skip implementation, generate final report
```

Do NOT proceed until the user approves. You MUST stop generating text completely at this point -- do NOT simulate the user's response or continue autonomously. Wait for explicit user input before starting Phase 4.

---

## Phase 4: Apply Changes

**Target type determines behavior:**
- **If local target** (e.g., `src/pages/landing.html`): use `#edit/editFiles` tools to implement changes directly in the source code
- **If remote URL** (e.g., `https://example.com`): do NOT attempt to edit local files. Generate improved code/copy as standalone files inside `.content-strategy/improvements/` (e.g., `optimized-hero-copy.md`, `rebuilt-pricing-table.html`)

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
- Audit passes: 3 (UX, Content, Social)
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

- `/content-strategy https://example.com` -- Full marketing audit
- `/content-strategy https://example.com/pricing` -- Pricing page conversion optimization
- `/content-strategy src/pages/landing.html` -- Audit local landing page
- `/content-strategy https://example.com --focus cta,social-proof` -- Focused audit
- `/content-strategy https://example.com --social` -- Social media presence focus
