# Business Planner Agent + SaaS Business Plan Skill -- Implementation Plan

> **For agentic workers:** Use subagent-driven execution (if subagents available) or ai-tooling:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a socratic SaaS GTM Advisor agent and modular knowledge base skill to the `business` plugin.

**Architecture:** Agent `business-planner.md` contains all behavioral logic (role, rules, 7-phase workflow). Skill `saas-business-plan` is a pure KB with `SKILL.md` index and 8 reference files extracted from the user-provided source document.

**Tech Stack:** Markdown (agent + skill), JSON (marketplace.json)

---

## File Structure

```
plugins/business/
  agents/
    business-planner.md           (CREATE - agent with frontmatter + ~180-line body)
  skills/
    saas-business-plan/
      SKILL.md                    (CREATE - skill index ~40 lines)
      references/
        market-sizing.md          (CREATE - from source doc sez. 1)
        audience-personas.md      (CREATE - from source doc sez. 2)
        competitive-analysis.md   (CREATE - from source doc sez. 3)
        pricing.md                (CREATE - from source doc sez. 4)
        positioning-pmf.md        (CREATE - from source doc sez. 5)
        go-to-market.md           (CREATE - from source doc sez. 6)
        advertising-metrics.md    (CREATE - from source doc sez. 7-8)
        tools-resources.md        (CREATE - from source doc sez. 9-10)
  .claude-plugin/marketplace.json (MODIFY - add agent, skill, update metadata)
```

**Source document** (read-only, content already in conversation context): User-provided KB file with 10 sections, ~350 lines of SaaS GTM strategy content.

---

## Chunk 1: Reference Files

### Task 1: Create `market-sizing.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/market-sizing.md`

- [ ] **Step 1: Create the reference file**

Extract verbatim from source document Section 1 ("Analisi del mercato: dimensionare l'opportunita' reale"). Include:
- TAM calculation (3 methods: top-down, bottom-up, value-based)
- Validation rule (top-down and bottom-up converge within +-15%)
- SAM and SOM definitions (SOM = 0.5-2% of TAM in first 3 years)
- 5 saturation indicators
- Tools table (Google Trends, Statista, Crunchbase, SimilarWeb, IBISWorld, G2, Gartner, CB Insights, Grand View Research, SEC EDGAR)
- University library tip

- [ ] **Step 2: Verify** -- file exists, contains all metrics and the tools table

---

### Task 2: Create `audience-personas.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/audience-personas.md`

- [ ] **Step 1: Create the reference file**

Extract from source Section 2 ("Audience e User Persona"). Include:
- ICP vs buyer persona distinction
- T2D3/Kalungi framework: P1 (daily user), P2 (decision maker), P3 (executive)
- Enterprise 5-role buying committee
- B2C psychographics
- JTBD statement formula and 3 dimensions (functional, personal emotional, social emotional)
- JTBD interview technique (timeline method, 10-20 interviews)
- Mom Test principles
- Qualitative research (5-20 interviews per segment)
- Quantitative: micro-surveys 12% response rate, tool stack by stage (GA4+Hotjar -> Amplitude/Mixpanel -> PostHog)
- Early adopter platforms table (Product Hunt, BetaList 12.7% conv., Indie Hackers, HN, Reddit, AppSumo)
- LinkedIn outreach sequence (100 early adopters from 600 contacts)

- [ ] **Step 2: Verify** -- all frameworks, metrics, and tables present

---

### Task 3: Create `competitive-analysis.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/competitive-analysis.md`

- [ ] **Step 1: Create the reference file**

Extract from source Section 3 ("Analisi della concorrenza"). Include:
- Porter's 5 Forces applied to SaaS (new entrants HIGH, supplier power LOW, buyer power HIGH, rivalry INTENSE, 400-450 new SaaS/year, 15k+ in USA)
- Strategic implication: build switching costs
- Strategic Group Mapping
- Feature Comparison Matrix
- Perceptual Map 2x2 (how to create: 2 attributes, 6-10 competitors, data from G2/NPS)
- Reverse engineering: pricing intelligence (Visualping), messaging (email sequences, Wayback Machine), product (free trials, changelog, hiring signals), growth strategies (SEMrush/Ahrefs, SimilarWeb, BuzzSumo)
- Love/Hate/Want framework (100+ reviews from G2/Capterra/TrustRadius)
- Competitive analysis tools table (SEMrush, Ahrefs, SpyFu, SimilarWeb, BuiltWith, Crayon/Klue, Visualping)

- [ ] **Step 2: Verify** -- Porter forces, frameworks, tools table all present

---

### Task 4: Create `pricing.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/pricing.md`

- [ ] **Step 1: Create the reference file**

Extract from source Section 4 ("Strategia di pricing"). Include:
- Tiered pricing (avg 3.5 tiers, 3 tiers convert 31% better)
- Usage-based (38-39% adoption, +10% NRR, -22% churn, 2x growth)
- Hybrid model (31% adoption)
- Credit-based pricing trend 2025 (+126% YoY, 79 of top 500 SaaS)
- AI monetization (74% monetizing/testing, bundling trend e.g. Notion $15->$20)
- Value-based (78% prefer, +11% profit per 1% improvement, +32% LTV)
- Cost-plus and competitor-based tradeoffs
- Van Westendorp (4 questions, 100+ respondents per segment, plot cumulative curves)
- Conjoint Analysis (200+ respondents, $15k-50k+, 30% monetization improvement, tools: Sawtooth, Conjointly, Qualtrics)
- Pricing page best practices (4 sections, 3 tiers, annual default +19%, money-back +12-18%, 30-second choice benchmark)

- [ ] **Step 2: Verify** -- all percentages and benchmarks present

---

### Task 5: Create `positioning-pmf.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/positioning-pmf.md`

- [ ] **Step 1: Create the reference file**

Extract from source Section 5 ("Posizionamento e differenziazione"). Include:
- UVP 3-act structure (Setup, Conflict, Resolution)
- Kalungi 3 questions (Why change? Why us? Why now?)
- April Dunford "Obviously Awesome" 5 steps (alternatives, unique attributes, differentiated value, best-fit customers, market category)
- Key insight: start from best customers, don't create new category without $200M+ revenue
- Crossing the Chasm: beachhead market, whole product, success stories
- Blue Ocean ERRC framework with SaaS examples
- Finding niches: 3 questions, Loomly 66% example, Lemkin quote on $100M ARR, Veeva $30B+
- Sean Ellis PMF test (>40% "very disappointed", min 30 responses, quarterly testing)
- Superhuman PMF Engine (started 22%, reached 58%, 50/50 roadmap split)
- Complementary PMF metrics (retention 20-50%, Quick Ratio >4, NPS >50, logo retention >85% SMB / >95% enterprise)

- [ ] **Step 2: Verify** -- all frameworks and metrics present

---

### Task 6: Create `go-to-market.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/go-to-market.md`

- [ ] **Step 1: Create the reference file**

Extract from source Section 6 ("Strategie di go-to-market"). Include:
- PLG characteristics (ACV <5k, +15-20% NRR, 60% fail in 18 months)
- SLG characteristics (ACV >50k, complex, enterprise)
- Hybrid 2025 "Product-Led, Sales-Assisted" (PQL convert 2-3x better than MQL)
- Channel-Market Fit table by ACV (<1k, 1-10k, 10-50k, 50-250k, 250k+)
- Community-Led Growth (2.1x faster revenue, +46% LTV, 1 EUR -> 6.40 EUR return, Lighthouse->Port->City model, Notion example)
- Launch sequence: pre-launch (3-6 months), beta (1-2 months), public launch (1-2 months), post-launch (6-12 months) with activities for each

- [ ] **Step 2: Verify** -- PLG/SLG/hybrid, ACV table, community-led, launch sequence present

---

### Task 7: Create `advertising-metrics.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/advertising-metrics.md`

- [ ] **Step 1: Create the reference file**

Extract from source Sections 7-8 ("Pubblicita' e marketing" + "Metriche e KPI"). Include:
- Competitor ad analysis: Meta Ad Library, Google Ads Transparency, LinkedIn Ad Library (all free)
- Paid tools: SpyFu, SEMrush, Adbeat
- Programmatic SEO (integration pages Zapier +300%, vs pages, alternative pages, templates, free tools)
- Content ROI ($3:$1 minimum, up to 748%, 82% have content teams)
- Content types ROI: blog, case study (73% B2B buyers), video (+49% faster ROI), webinar (73% best lead format)
- Google Ads: CTR 4.28%, CPC $5-50, budget share down 55%->40%
- LinkedIn Ads: CTR 0.62%, CPC $8-15, ROAS 113%, SQL:CW 30-33%, budget share up 31%->39%
- Meta Ads: CTR 1.43%, CPC ~$0.66, ideal B2C/prosumer
- Email: ROI 3600-4200%, triggered +320% revenue, segmented = 77% of email ROI
- Email tools: Encharge, Customer.io, ActiveCampaign, HubSpot
- North Star Metric by type (engagement: DAU/WAU/MAU; productivity: tasks/workflows; platform: transactions; infrastructure: API calls)
- KPI benchmark table (CAC $702, payback 12-15 months, LTV:CAC 3:1 / median 3.6:1, churn 3-5%, NRR >111%, MRR 10-20% MoM, gross margin 70-80%, Rule of 40)
- SOV (1.5x conversions, +30% retention, AI SOV trend for ChatGPT/Perplexity/Gemini)
- Metrics tools: ChartMogul, Baremetrics, ProfitWell, zero-cost stack

- [ ] **Step 2: Verify** -- ad channels, SEO, email, KPI table, North Star all present

---

### Task 8: Create `tools-resources.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/references/tools-resources.md`

- [ ] **Step 1: Create the reference file**

Extract from source Sections 9-10 ("Tool e risorse" + "Piano di lavoro step-by-step"). Include:
- Tools map by phase: market research, audience research, competitor analysis, pricing, SEO/content, advertising analysis, analytics/metrics (with tool names and costs)
- Framework/template resources: April Dunford Canvas, Miro templates, Notion templates, ClickUp, MRR Unlocked, PMFSurvey.com
- Communities: SaaStr, Indie Hackers, Product Hunt, ProductLed, Lenny's Podcast, Reddit subs, YC Startup Library
- 5 essential books
- 7-week step-by-step plan (week 1-2 foundations, week 3 customer research, week 4 competitive deep-dive, week 5 value prop + pricing, week 6 positioning statement, week 7 validation)
- Timeline by company stage table (pre-launch 4-8w, early-stage 6-10w, growth 8-12w, enterprise 12-16w+)
- Final positioning document structure (executive summary, market context, customer profile, category, competitive landscape, differentiators, UVP, messaging framework, pricing, channel strategy, success metrics)
- Top 5 errors to avoid (positioning for everyone, confusing positioning/messaging, under-pricing 2x more common, skipping research, never revisiting)

- [ ] **Step 2: Verify** -- tools map, communities, books, timeline, errors all present

---

### Task 9: Commit reference files

- [ ] **Step 1: Commit**

```bash
git add plugins/business/skills/saas-business-plan/references/
git commit -m "feat(business): add saas-business-plan reference files

8 knowledge base files extracted from SaaS GTM strategy guide:
market-sizing, audience-personas, competitive-analysis, pricing,
positioning-pmf, go-to-market, advertising-metrics, tools-resources"
```

---

## Chunk 2: Skill SKILL.md + Agent + Marketplace

### Task 10: Create `SKILL.md`

**Files:**
- Create: `plugins/business/skills/saas-business-plan/SKILL.md`

- [ ] **Step 1: Create SKILL.md**

```markdown
---
name: saas-business-plan
description: >
  Strategic knowledge base for SaaS business planning and GTM strategy (2025-2026).
  Market sizing, audience/persona frameworks, competitive analysis, pricing models,
  positioning (April Dunford, Blue Ocean, Crossing the Chasm), GTM motions (PLG/SLG/hybrid),
  advertising benchmarks, and KPI targets. Used by the business-planner agent.
---

# SaaS Business Plan -- Knowledge Base

Strategic reference material for building a SaaS business plan and go-to-market strategy.
Updated for 2025-2026 market conditions.

## Reference Files

| File | Phase | Content |
|------|-------|---------|
| `references/market-sizing.md` | Phase 1 | TAM/SAM/SOM calculation (3 methods), market saturation indicators, research tools |
| `references/audience-personas.md` | Phase 2 | ICP, buyer persona (P1/P2/P3), JTBD framework, customer research methods, early adopter channels |
| `references/competitive-analysis.md` | Phase 3 | Porter's 5 Forces in SaaS, positioning maps, Love/Hate/Want review analysis, CI tools |
| `references/pricing.md` | Phase 5 | Tiered/usage/hybrid/credit models, value-based pricing, Van Westendorp, pricing page best practices |
| `references/positioning-pmf.md` | Phase 4 | April Dunford 5 steps, UVP, Crossing the Chasm, Blue Ocean ERRC, Sean Ellis PMF test |
| `references/go-to-market.md` | Phase 6 | PLG vs SLG vs hybrid, channel-market fit by ACV, community-led growth, launch sequence |
| `references/advertising-metrics.md` | Phase 7 | Ad channel benchmarks, SEO/content ROI, email marketing, KPI benchmarks, North Star Metric |
| `references/tools-resources.md` | All | Tools by phase, templates, communities, books, 7-week timeline, final deliverable structure |
```

- [ ] **Step 2: Verify** -- frontmatter valid, table lists all 8 files with correct paths

---

### Task 11: Create `business-planner.md` agent

**Files:**
- Create: `plugins/business/agents/business-planner.md`

- [ ] **Step 1: Create the agent file**

Write the full agent with:
- Frontmatter: name, description (from design doc), model opus, tools, color green
- Body following the legal-advisor pattern (terse, imperative, keyword-list style)
- Sections: Role, Behavioral Rules, Phase Navigation, Web Tools, 7-Phase Workflow (each phase with questions/reference/output/gate), Startup Message, Anti-patterns

The agent body must:
- Reference skill files as `Read` instructions with paths relative to the skill dir: `plugins/business/skills/saas-business-plan/references/<file>.md`
- Include the startup greeting
- Specify gate conditions per phase
- Include skip/revisit navigation rules

- [ ] **Step 2: Verify** -- frontmatter matches design doc, all 7 phases reference correct files, < 200 lines

---

### Task 12: Update `marketplace.json`

**Files:**
- Modify: `.claude-plugin/marketplace.json` (business plugin entry)

- [ ] **Step 1: Read current marketplace.json business entry**

- [ ] **Step 2: Update the business plugin entry**

Changes:
- Add `"./agents/business-planner.md"` to `agents` array
- Add new `"skills"` array: `["./skills/saas-business-plan"]`
- Update `description` to: `"Legal advisory, compliance document generation, and SaaS business planning -- Privacy Policies, Cookie Policies, DPAs, GDPR/ePrivacy/CCPA compliance, contract review, GTM strategy, market sizing, pricing, and positioning"`
- Add keywords: `"saas"`, `"gtm"`, `"business-plan"`, `"pricing"`, `"positioning"`
- Bump plugin `version` (1.8.0 -> 1.9.0)
- Bump `metadata.version` (2.95.0 -> 2.96.0)

- [ ] **Step 3: Verify** -- JSON is valid, business entry has 3 agents, 1 skill, updated description/keywords/versions

---

### Task 13: Final commit and push

- [ ] **Step 1: Commit all remaining files**

```bash
git add plugins/business/agents/business-planner.md
git add plugins/business/skills/saas-business-plan/SKILL.md
git add .claude-plugin/marketplace.json
git commit -m "feat(business): add business-planner agent and saas-business-plan skill

Fractional CMO / GTM Strategist agent with 7-phase socratic workflow:
market sizing, audience/JTBD, competitive analysis, positioning,
pricing, go-to-market, metrics/KPI. Knowledge base split into 8
reference files for token-efficient phase-by-phase loading."
```

- [ ] **Step 2: Push**

```bash
git push
```
