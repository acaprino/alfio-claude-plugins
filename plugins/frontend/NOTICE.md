# NOTICE

This `frontend` plugin vendors portions of work from multiple upstream projects.
Per Apache-2.0 4(d) and MIT attribution practice, the originating NOTICE content
and license information is preserved below.

The original upstream NOTICE files were fetched on 2026-05-11 from each project's
default branch. See `CLAUDE.md` (root of this repo) for the per-file sync table
that maps each derived file back to its upstream source.

---

## pbakaus/impeccable (Apache-2.0)

The following block is reproduced from the upstream `NOTICE.md` at
https://github.com/pbakaus/impeccable.

> # Notice
>
> Impeccable
> Copyright 2025-2026 Paul Bakaus
>
> ## Anthropic frontend-design Skill
>
> The `impeccable` skill in this project builds on Anthropic's original frontend-design skill.
>
> **Original work:** https://github.com/anthropics/skills/tree/main/skills/frontend-design
> **Original license:** Apache License 2.0
> **Copyright:** 2025 Anthropic, PBC
>
> This project extends the original with:
> - 7 domain-specific reference files (typography, color-and-contrast, spatial-design, motion-design, interaction-design, responsive-design, ux-writing)
> - 23 commands
> - Expanded patterns and anti-patterns
>
> ## Typecraft Guide Skill
>
> The `typography.md` reference in this project incorporates a set of tactical additions merged in from ehmo's `typecraft-guide-skill` at the author's request: dark-mode weight/tracking compensation, `font-display: optional` vs `swap`, preload-critical-weight-only guidance, variable fonts for 3+ weights, `clamp()` max-to-min ratio bound, responsive measure/container coupling, `text-wrap: balance` / `pretty`, `font-optical-sizing: auto`, ALL-CAPS tracking quantification, and the paragraph-rhythm rule (space OR indent, never both).
>
> **Original work:** https://github.com/ehmo/typecraft-guide-skill
> **Original license:** see upstream repo
> **Author:** ehmo

### Local impact of this NOTICE

The Anthropic `frontend-design` lineage applies to all Impeccable-derived files
listed in the sync table: the 10 reference files (typography, color-and-contrast,
motion-design, heuristics-scoring, cognitive-load, personas, brand-register,
visual-intensity, delight-and-microinteractions, production-hardening) plus the
4 appended sections inside `layout-patterns.md`, `ui-pattern-guide.md`,
`css-patterns.md`, and `ux-patterns.md`. The last three reference files were
vendored in the 2026-06-02 refresh (derived from Impeccable's `bolder.md` +
`quieter.md`, `delight.md`, and `harden.md` respectively).

The `ehmo/typecraft-guide-skill` lineage applies specifically to
`plugins/frontend/skills/frontend-css/references/typography.md`. Its attribution
header credits both Impeccable (the immediate upstream we vendored from) and
ehmo (the original author of the typography additions Impeccable merged in).

---

## nextlevelbuilder/ui-ux-pro-max-skill (MIT)

Upstream does not ship a separate `NOTICE.md`; license terms are in the
`LICENSE` file at the repo root. The MIT permission notice is preserved in the
attribution comment at the top of each derived file:

- `plugins/frontend/skills/frontend-css/references/token-architecture.md`
- `plugins/frontend/skills/frontend-css/references/component-specs.md`
- `plugins/frontend/skills/frontend-css/references/states-and-variants.md`
- `plugins/frontend/skills/frontend-css/references/tailwind-integration.md`
- `plugins/frontend/skills/frontend-css/references/primitive-tokens.md`
- `plugins/frontend/skills/frontend-css/references/semantic-tokens.md`
- `plugins/frontend/skills/frontend-css/references/component-tokens.md`
