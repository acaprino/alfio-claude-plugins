# Design: Business Planner Agent + SaaS Business Plan Skill

**Date:** 2026-03-20
**Plugin:** `business`
**Components:** Agent `business-planner` + Skill `saas-business-plan`

---

## Summary

Add a Fractional CMO / GTM Strategist agent to the `business` plugin that guides users through a 7-phase SaaS business plan creation process. The agent operates socratically (one phase at a time, asks questions, waits for answers) and draws on a modular knowledge base stored as a skill with 8 reference files.

## Structure

```
plugins/business/
  agents/
    legal-advisor.md              (existing)
    privacy-doc-generator.md      (existing)
    business-planner.md           (NEW - ~180 lines)
  skills/
    saas-business-plan/
      SKILL.md                    (NEW - ~40 lines)
      references/
        market-sizing.md          (~60 lines)
        audience-personas.md      (~70 lines)
        competitive-analysis.md   (~60 lines)
        pricing.md                (~50 lines)
        positioning-pmf.md        (~60 lines)
        go-to-market.md           (~50 lines)
        advertising-metrics.md    (~60 lines)
        tools-resources.md        (~50 lines)
```

## Agent: `business-planner.md`

### Frontmatter

- **name:** `business-planner`
- **description:** Fractional CMO and GTM Strategist for SaaS business planning. Socratic approach: one phase at a time, targeted questions, data-driven benchmarks. Use PROACTIVELY for business plan, GTM strategy, SaaS positioning, pricing strategy, market sizing, TAM/SAM/SOM, or PMF. DO NOT TRIGGER for legal/compliance (use legal-advisor), privacy docs (use privacy-doc-generator), or tactical marketing (use digital-marketing agents).
- **model:** `opus`
- **tools:** `Read, Write, Edit, Glob, Grep, WebFetch, WebSearch`
- **color:** `green`

### Body structure (~180 lines)

1. **Role** - Fractional CMO e GTM Strategist, highest-level consultant
2. **Behavioral rules**
   - Socratic and sequential: one phase at a time, ask questions, wait for answers
   - Ruthless on positioning: reject "the product is for everyone", cite 70% failure rate
   - Data-driven: cite metrics/benchmarks from KB references
   - Language: detect and match the user's language from their first message
3. **Phase navigation** - Users can skip phases (`skip`) or revisit previous ones (`go back to phase N`). The agent confirms and adjusts.
4. **Web tools usage** - `WebFetch` and `WebSearch` are available for live market research when the user's sector needs fresh data (e.g., checking current market size reports, competitor websites, pricing pages). The agent may suggest using them during Phase 1 (market sizing) and Phase 3 (competitive analysis).
5. **7-phase workflow** - Each phase specifies:
   - What to ask the user
   - Which `references/` file to Read
   - Expected output of the phase
   - Gate: do not advance without user response
   - Phase 1: Market sizing (Read market-sizing.md) - ask idea, sector, estimated ACV, calculate TAM/SAM/SOM
   - Phase 2: Audience & JTBD (Read audience-personas.md) - define ICP, P1/P2/P3, JTBD statement
   - Phase 3: Competitive analysis (Read competitive-analysis.md) - Love/Hate/Want, positioning map
   - Phase 4: Positioning (Read positioning-pmf.md) - April Dunford 5 steps, UVP, positioning statement
   - Phase 5: Pricing (Read pricing.md) - model selection, page structure
   - Phase 6: Go-to-market (Read go-to-market.md) - PLG/SLG/hybrid, channels, launch sequence
   - Phase 7: Metrics & KPI (Read advertising-metrics.md) - North Star Metric, financial targets
6. **Startup message** - Greets the user in their language, introduces itself as SaaS GTM Advisor, asks "What does your SaaS do and who is it for?"
7. **Anti-patterns to flag** - Positioning for everyone, under-pricing, skipping customer research, never revisiting positioning

## Skill: `saas-business-plan`

### SKILL.md (~40 lines)

- **name:** `saas-business-plan`
- **description:** Strategic knowledge base for SaaS business planning and GTM strategy (2025-2026). Contains market sizing methodologies, audience/persona frameworks, competitive analysis tools, pricing models, positioning frameworks (April Dunford, Blue Ocean, Crossing the Chasm), GTM motions (PLG/SLG/hybrid), advertising benchmarks, and KPI targets. Used by the business-planner agent.
- Body: lists the 8 reference files with one-line descriptions

### References (8 files)

**Source document:** User-provided KB file (`compass_artifact_wf-e910cffe-5482-4bfb-b519-0f2f0322256b_text_markdown.md`) -- a comprehensive SaaS GTM guide with 10 sections covering market sizing through launch planning. All metrics, percentages, tables, and frameworks are extracted verbatim from this document into the reference files below.

| File | Source sections | Key content |
|------|----------------|-------------|
| `market-sizing.md` | Sez. 1 | TAM/SAM/SOM (3 methods), +-15% validation, saturation (5 indicators), tools table |
| `audience-personas.md` | Sez. 2 | ICP vs buyer persona, T2D3 P1/P2/P3, JTBD statement, Mom Test, quali/quanti research, early adopter platforms table |
| `competitive-analysis.md` | Sez. 3 | Porter's 5 Forces in SaaS, Strategic Group Mapping, Feature Matrix, Perceptual Map, reverse engineering, Love/Hate/Want, tools table |
| `pricing.md` | Sez. 4 | Tiered/usage/hybrid/credits, value-based vs cost-plus, Van Westendorp, Conjoint, pricing page best practices |
| `positioning-pmf.md` | Sez. 5 | UVP (setup/conflict/resolution), April Dunford 5 steps, Crossing the Chasm, Blue Ocean ERRC, Sean Ellis test, Superhuman Engine |
| `go-to-market.md` | Sez. 6 | PLG vs SLG vs hybrid, PQL, channel-market fit by ACV, community-led growth, launch sequence |
| `advertising-metrics.md` | Sez. 7-8 | Ad libraries, programmatic SEO, email ROI, KPI benchmarks table, North Star Metric, SOV |
| `tools-resources.md` | Sez. 9-10 | Tools map by phase, downloadable templates, communities, books, 7-week timeline, final positioning document |

**Note:** Tools, templates, communities, and books listed in `tools-resources.md` are informational text the agent presents to the user -- not files written to disk. The agent does not produce a final business plan document; it guides the user through the process interactively.

## Marketplace changes

In `.claude-plugin/marketplace.json`:
- Add `./agents/business-planner.md` to `business` plugin `agents` array
- Add new `skills` array with `./skills/saas-business-plan`
- Update plugin `description` to include business planning and GTM strategy
- Add keywords: `saas`, `gtm`, `business-plan`, `pricing`, `positioning`
- Bump plugin `version`
- Bump `metadata.version`

## Design decisions

1. **Agent-heavy, skill-light** - Agent contains all behavioral logic and workflow. Skill is a pure KB. Consistent with existing `legal-advisor` pattern.
2. **KB split by phase** - 8 reference files aligned to the 7 workflow phases. Agent loads only the relevant file per phase, saving tokens.
3. **Plugin `business`** - Strategic consulting fits alongside legal-advisor and privacy-doc-generator. Avoids plugin proliferation.
4. **Socratic flow** - One phase at a time, explicit gates. The agent never dumps the entire plan at once.
