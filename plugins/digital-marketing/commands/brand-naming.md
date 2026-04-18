---
description: >
  Generate, filter, score, and validate brand names through a structured naming workflow with market saturation analysis, domain checks, trademark screening, and weighted scoring.
  TRIGGER WHEN: the user asks for brand names, startup names, product names, or company names -- typically with a brief or industry.
  DO NOT TRIGGER WHEN: renaming source code identifiers (use clean-code), naming files/tests, or picking SEO keywords (use /digital-marketing:seo-audit).
argument-hint: "<brief description or industry> [--style descriptive|abstract|evocative|all] [--languages <lang1,lang2>] [--tlds <.com,.app,.io>]"
---

# Brand Naming

## Invocation

Invoke the `brand-naming` skill and follow its full workflow.

## Arguments

- `<brief>`: Industry, target, values, and any constraints for the naming project
- `--style`: Focus on a specific name style (default: all three styles)
- `--languages`: Languages to check for cultural conflicts (default: en,it,es,fr,de,pt)
- `--tlds`: TLDs to check for domain availability (default: .com,.app,.io,.co)

## Examples

```
/brand-naming Meal prep app for vegan athletes. Values: energy, nature, performance. Target: 20-35, international.
/brand-naming SaaS project management tool for remote teams --style abstract --languages en,es,pt
/brand-naming Italian artisan coffee brand, premium positioning --style evocative --tlds .com,.it,.coffee
```

## What it does

1. Analyzes the brief and asks clarifying questions if needed
2. Generates 30+ name candidates across descriptive, abstract, and evocative styles
3. Filters linguistically and culturally (pronunciation, negative meanings, phonosymbolism)
4. Checks domain availability and social media handles
5. Analyzes market saturation: existing apps, websites, active businesses with same name (Google, Play Store, App Store, Crunchbase)
6. Pre-screens trademarks via EUIPO/USPTO/WIPO web searches
7. Scores top 5 on weighted criteria (memorability, distinctiveness, market saturation, SEO, legal risk, etc.)
8. Presents top 3 with full breakdown: scoring table, name story, saturation report, domain status, tagline suggestion
