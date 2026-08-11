---
description: Runs the whole workflow from a brief, with optional language and TLD constraints. Use when the user asks for brand, startup, product, or company names. Not for renaming source code identifiers (use the `clean-code` bundle), or picking SEO keywords (use /seo-audit).
argument-hint: <brief description or industry> [--languages <lang1,lang2>] [--tlds <.com,.app,.io>]
---

# Brand Naming

## Invocation

Invoke the `brand-naming` skill and follow its full workflow.

## Arguments

- `<brief>`: Industry, target, values, and any constraints for the naming project
- `--languages`: Languages to check for cultural conflicts (default: en,it,es,fr,de,pt)
- `--tlds`: TLDs to check for domain availability (default: .com,.app,.io,.co)

## Examples

```
/brand-naming Meal prep app for vegan athletes. Values: energy, nature, performance. Target: 20-35, international.
/brand-naming SaaS project management tool for remote teams --languages en,es,pt
/brand-naming Italian artisan coffee brand, premium positioning --tlds .com,.it,.coffee
```

## What it does

1. Analyzes the brief and asks clarifying questions if needed
2. Generates 12-15 curated candidates across 4 Strategic Directions: Etymological Hijacking, Scientific Decontextualization, Metaphorical Shift, Phonetic Real-Word
3. Filters linguistically and culturally (pronunciation, negative meanings, phonosymbolism)
4. Checks domain availability and social media handles
5. Analyzes market saturation: existing apps, websites, active businesses with same name (Google, Play Store, App Store, Crunchbase)
6. Pre-screens trademarks via EUIPO/USPTO/WIPO web searches
7. Scores top 5 on weighted criteria (memorability, distinctiveness, market saturation, SEO, legal risk, etc.)
8. Presents top 3 with full breakdown: scoring table, name story, saturation report, domain status, tagline suggestion
