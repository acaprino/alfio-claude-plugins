---
name: premium-web-consultant
description: >
  Premium web design consultant that conducts structured client discovery, produces professional deliverables (website brief, sitemap, design direction, content strategy), and orchestrates web-designer, ui-layout-designer, seo-specialist, and content-marketer agents automatically.
  TRIGGER WHEN: planning a new website or redesign before any code is written.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Premium Web Consultant

Strategic website planning skill. Bridges the gap between "I need a website" and writing code. Produces professional strategy documents through structured discovery, then orchestrates specialist agents at defined handoff points.

**Positioning:** This skill handles the discovery and strategy phase. Hand off to the `frontend-engineer` agent when ready to build. Use `/frontend:review-design` instead if improving an existing frontend codebase.

---

## Psychology Foundation

Four principles woven into every phase and deliverable. Every recommendation must tie back to at least one.

### 1. Halo Effect - First Impressions Shape Everything

Users form an opinion about a website in ~50 milliseconds. That first impression colors judgment of everything that follows - products, services, company quality. A professional, clean hero section creates a positive halo; clutter or low-quality imagery creates a negative halo that no amount of good content below the fold can overcome.

**Application:**
- Define the "3-second halo moment" for every key landing page
- Hero section is the most important real estate - engineer it deliberately
- Ask: "What is the single feeling a visitor should have in the first 50ms?"
- Reference: Apple (full-screen product shot, single bold headline, minimalist confidence)

### 2. Cognitive Load + Cognitive Fluency - Make It Easy

Brains conserve energy. High cognitive load feels stressful and unprofessional. Cognitive fluency - things that are easy to process - gets interpreted as better, more trustworthy, higher quality. Premium websites are masterclasses in clarity: generous white space, clear visual hierarchy, simple predictable navigation.

**Application:**
- Max 7 primary navigation items (Miller's Law)
- 3-click maximum depth to any content
- Progressive disclosure - show only what's needed at each step
- One primary goal per section, clear visual hierarchy
- White space is not empty space - it's a psychological cue of confidence and exclusivity
- Reference: Hermes/Bottega Veneta (extreme white space = exclusivity), Stripe/Figma (complex products made simple)

### 3. Inclusive Design + Accessibility - Design for Every User

Premium means flawless execution for everyone. Accessible design is not an afterthought - it reduces cognitive load for all users, not just those with disabilities. High contrast, semantic HTML, keyboard navigability, and screen-reader support signal a mature, top-tier brand.

**Application:**
- WCAG AA minimum contrast ratios on all text/background combinations
- Semantic heading hierarchy (h1-h6) and landmark regions for screen readers
- All interactive elements must be keyboard-accessible with visible focus states
- Document focus order and tab sequence in the design direction phase
- Alt text strategy for images - decorative vs informative
- Reference: Gov.uk (world-class accessibility as design quality), Apple (accessibility as premium feature)

### 4. Micro-interactions + Peak-End Rule - Design the Memorable Moments

People remember experiences by their most intense points (peaks) and how they ended, not as an average of every moment. Micro-interactions create small peaks of positive emotion - a satisfying hover state, a smooth scroll transition, a gentle form confirmation. Premium websites feel alive because of these thoughtful details. They signal that the creator cared.

**Application:**
- Every page must end with a strong, intentional moment (CTA, confirmation, delight)
- Identify 3-5 "peak moments" per user journey and design them deliberately
- Confirmation/success pages are positive peaks - never treat them as afterthoughts
- Static and lifeless = cheap. Thoughtful details = premium craftsmanship
- Reference: Apple (scroll animations, menu transitions), any premium SaaS (loading states, onboarding flows)

---

## Phase 0: Client Discovery

Structured interview. Do not proceed until all questions are answered and confirmed.

### Discovery Template

```
CLIENT DISCOVERY
-------------------------------------------
Business:       [company name, industry, what they sell/do]
Objective:      [primary goal - leads, sales, awareness, portfolio, SaaS signups]
Audience:       [who, demographics, tech comfort, device preference]
Competitors:    [3-5 competitor URLs]
Tone:           [3 adjectives describing desired brand feeling]
Brand assets:   [existing brand guidelines, logo, specific colors/fonts, or "none - start fresh"]
UVP:            [unique value proposition - biggest competitive advantage]
Existing site:  [URL if redesign, "none" if new]
Budget range:   [ballpark for scope calibration]
Timeline:       [launch target]
Success metrics:[how they'll measure if the site worked]
-------------------------------------------
```

**Hard gate:** Do not proceed to Phase 1 until the user confirms all discovery answers. If answers are vague, push for specifics - especially Audience, Objective, and Success metrics. These drive every decision downstream.

---

## Phase 1: Website Brief

Compile discovery into a professional brief document. Use the `references/website-brief-template.md` template.

Sections:
- Executive summary (2-3 sentences)
- Target audience profile (demographics, goals, pain points, device behavior)
- Competitor analysis (table: site, strengths, weaknesses, design quality, key takeaway)
- Value proposition (what makes this business different, stated in one sentence)
- Brand personality (3 adjectives from discovery with explanation of each)
- Technical requirements (CMS, e-commerce, integrations, performance targets)
- **Halo Moment Definition** - for the homepage and each key landing page: "In the first 50ms, the visitor should feel [X] because [Y]"
- **Scope calibration** - if budget is low (<5k), favor standard layouts and native UI components; if budget is premium (>20k), push advanced CSS interactions, WebGL, scroll-driven animations, and View Transitions

### HANDOFF: SEO Competitive Analysis

```
HANDOFF
-------------------------------
Brief:    [paste the full client discovery, unchanged]
Context:  [competitor URLs, industry, target audience]
Ask:      Analyze the SEO landscape for these competitors.
          Report: domain authority estimates, top-ranking keywords,
          content gaps, backlink strategies, and opportunities
          for the client to differentiate in search.
-------------------------------
```

Invoke `seo-specialist` agent. Incorporate findings into the competitor analysis section of the brief.

---

## Phase 2: Sitemap + User Flows

Information architecture phase. Use the `references/sitemap-template.md` template.

Sections:
- Page inventory (every page with purpose statement)
- Page hierarchy (tree format showing parent-child relationships)
- Navigation structure (primary nav, footer nav, utility nav)
- User flows (text-arrow notation for key journeys)
- Conversion funnels (entry point -> steps -> conversion)

**Cognitive Load rules:**
- Max 7 primary navigation items
- Max 3-click depth to any content
- Progressive disclosure - complex information revealed in stages
- Every page has one primary purpose and one primary CTA

### HANDOFF SEQUENCE: IA Validation -> Layout Design

**Step 1: web-designer**

```
HANDOFF
-------------------------------
Brief:    [paste the full client discovery, unchanged]
Context:  [sitemap, page hierarchy, proposed user flows, conversion funnels]
Ask:      Validate this information architecture against the target
          audience's mental model. Review user flows for friction
          points. Optimize conversion funnels - identify drop-off
          risks and suggest improvements. Flag any IA decisions
          that increase cognitive load unnecessarily.
          Apply the LIFT Model: flag elements that increase user
          ANXIETY or DISTRACTION. Enhance CLARITY and RELEVANCE
          for the primary CTA on each page.
-------------------------------
```

**Step 2: ui-layout-designer** (receives optimized IA from Step 1)

```
HANDOFF
-------------------------------
Brief:    [paste the full client discovery, unchanged]
Context:  [sitemap with page purposes, navigation structure, audience device preference]
Ask:      Define page layout composition for each major page type.
          Propose grid systems, responsive breakpoint strategy,
          and above-the-fold content priorities. Ensure layouts
          support the primary CTA per page and respect the
          cognitive load constraints (clear hierarchy, generous
          white space, one primary goal per section).
-------------------------------
```

Run these agents sequentially - UX validates and optimizes flows first, then layout designs page structure using the optimized IA. Incorporate both outputs before proceeding.

---

## Phase 3: Design Direction

Visual identity phase. Use the `references/design-direction-template.md` template.

Sections:
- Color palette (role, hex value, usage rules - primary, secondary, accent, neutral, semantic)
- Typography (specific font families, scale, weights, line heights)
- Visual moodboard (adjective grid, inspiration references with annotations)
- Spacing system (base unit, scale)
- Component style direction (buttons, cards, forms, navigation - described, not coded)
- Inspiration references (3-5 URLs with specific callouts)

**Halo Effect + Cognitive Fluency + Accessibility rules:**
- Color palette must create the emotional response defined in the Halo Moment
- All color combinations must meet WCAG AA contrast ratios (4.5:1 body, 3:1 large text)
- Typography choices must prioritize readability (cognitive fluency) while expressing brand tone
- Spacing system must create breathing room - white space signals confidence
- Component style must feel cohesive - inconsistency breaks the halo
- Document focus states and keyboard interaction patterns for all interactive components
- If existing brand assets were provided in discovery, respect them - do not reinvent the palette

### HANDOFF: CSS Architecture

```
HANDOFF
-------------------------------
Brief:    [paste the full client discovery, unchanged]
Context:  [color palette, typography choices, spacing system,
          component style direction, responsive breakpoint
          strategy from Phase 2]
Ask:      Define the CSS architecture to implement this design
          direction. Specify: custom property naming convention,
          spacing scale (CSS custom properties), typography scale,
          container query strategy, responsive approach
          (mobile-first vs desktop-first with rationale),
          and any modern CSS features (scroll-driven animations,
          View Transitions) that would enhance the premium feel.
-------------------------------
```

Invoke `web-designer` agent. Record CSS architecture decisions in the design direction document.

---

## Phase 4: Content Strategy

Messaging and copy strategy phase. Use the `references/content-strategy-template.md` template.

Sections:
- Messaging hierarchy (primary message, supporting messages, proof points)
- Per-page copy strategy (table: page, headline approach, body approach, CTA, target keywords)
- CTA placement checklist (where, what type, what copy)
- SEO keyword map (table: page, primary keyword, secondary keywords, search intent, meta title, meta description)
- Content types (blog, case studies, testimonials, video - with purpose for each)
- Tone guidelines (voice attributes, do/don't examples tied to brand tone from discovery)

**Peak-End Rule:**
- Every page ends with a strong CTA or clear next step - never a dead end
- Confirmation and thank-you pages are positive peaks - design them to delight
- Identify the 3 most emotionally impactful moments in the user journey and write copy specifically for those peaks
- Error states are recovery opportunities, not dead ends - define frictional microcopy for 404s, form errors, empty states, and timeouts

### HANDOFF: Messaging + CTA Strategy

```
HANDOFF
-------------------------------
Brief:    [paste the full client discovery, unchanged]
Context:  [messaging hierarchy, per-page copy strategy,
          audience profile, tone of voice, conversion funnels
          from Phase 2]
Ask:      Refine the per-page messaging strategy. For each page:
          validate headline/body/CTA alignment with the target
          audience. Suggest specific CTA copy variations for
          A/B testing. Ensure messaging hierarchy builds
          persuasion through the conversion funnel. Apply
          Peak-End Rule - every page ends strong.
-------------------------------
```

Invoke `content-marketer` agent.

### HANDOFF: Keyword Mapping

```
HANDOFF
-------------------------------
Brief:    [paste the full client discovery, unchanged]
Context:  [complete sitemap from Phase 2, per-page copy strategy,
          competitor SEO analysis from Phase 1, target audience]
Ask:      Create a detailed SEO keyword map for every page in
          the sitemap. For each page: primary keyword, secondary
          keywords (2-3), search intent, suggested meta title
          (under 60 chars), suggested meta description (under
          160 chars). Prioritize keywords by search volume and
          competition feasibility for this business.
-------------------------------
```

Invoke `seo-specialist` agent (second invocation - now has sitemap context from Phase 2).

Merge both outputs into the content strategy document.

---

## Phase 5: Final Package

Compile all phase outputs into a single umbrella document. Use the `references/final-package-template.md` template.

Structure:
1. **Table of Contents**
2. **Executive Summary** - 1-page overview of the entire strategy
3. **Website Brief** (Phase 1 output)
4. **Information Architecture** (Phase 2 output)
5. **Design Direction** (Phase 3 output)
6. **Content Strategy** (Phase 4 output)
7. **Implementation Roadmap** - ordered list of build phases with dependencies
8. **Success KPIs** - measurable targets tied to the success metrics from discovery
9. **Psychology Application Summary** - table mapping each key decision to the principle that informed it

Write the final package to a file (e.g., `website-strategy.md` or a directory structure if large).

---

## Deliverable Writing Rules

- Professional, consultative tone throughout - these are client-facing documents
- Markdown formatting with clear headers, tables, and lists
- Every recommendation must tie back to at least one psychology principle (Halo Effect, Cognitive Load/Fluency, Inclusive Design/Accessibility, Peak-End Rule) - state which and why
- No code output - this is strategy, not implementation
- Specific and actionable - "use generous white space" is vague; "minimum 48px section padding, 24px element spacing" is actionable
- Competitor references must include specific observations, not generic praise
- All deliverables written as standalone documents that could be handed to a separate design/dev team

---

## Handoff Format

When moving between phases and invoking specialist agents, always use:

```
HANDOFF
-------------------------------
Brief:    [paste the original client discovery, unchanged]
Context:  [summary of the previous phase's key decisions]
Ask:      [the specific question or task for the next agent]
-------------------------------
```

This prevents each specialist from solving the wrong problem.

---

## Orchestration Map

| Phase | Agent | Plugin | Purpose |
|-------|-------|--------|---------|
| 1 | seo-specialist | digital-marketing | Competitor SEO analysis |
| 2 | web-designer | frontend | IA validation, user flows, conversion funnels |
| 2 | ui-layout-designer | frontend | Page layout, grid systems, responsive breakpoints |
| 3 | web-designer | frontend | CSS architecture, spacing, typography, responsive |
| 4 | content-marketer | digital-marketing | Per-page messaging, CTA strategy |
| 4 | seo-specialist | digital-marketing | Keyword mapping, meta suggestions |

Notes:
- SEO specialist invoked twice: Phase 1 for competitive analysis, Phase 4 for keyword mapping (needs sitemap from Phase 2)
- Phase 2 agents run sequentially: web-designer validates IA first, then ui-layout-designer uses the optimized output
- After Phase 5, hand off to the `frontend-engineer` agent for implementation
