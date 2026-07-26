# Docs Plugin

> Craft magnetic, top-tier README.md files that capture attention in 3 seconds, prove value in 10, and get developers running code in 60.

## Skills

### `readme-craft`

Produces polished README.md files following open-source best practices: progressive disclosure, hero section with badges, visual proof, quick start, feature tables, collapsible advanced config, Mermaid architecture diagrams, and community sections.

| | |
|---|---|
| **Trigger** | "readme", "write a readme", "create readme", "scrivi il readme" |
| **Auto-detects** | Project name, tech stack, license, version, install commands, features, logo, CI/CD |
| **Asks user for** | Only what it cannot infer - logo, Discord link, demo GIF, badge style, copyright holder |

**How it works:**

1. **Scans the project** silently - reads manifests, LICENSE, README, source files, assets, CI config
2. **Presents a pre-filled brief** with everything it inferred
3. **Asks only for missing metadata** (license, logo, community link, sponsor link)
4. **Generates the README** following a strict progressive disclosure funnel

**README structure generated:**

| Section | Purpose |
|---------|---------|
| Hero (centered) | Logo with dark/light mode, title, one-liner, 4-6 shields.io badges |
| Visual proof | Demo GIF or screenshot (skipped if none available) |
| Why this project? | 3-5 emoji bullet points with key features |
| Quick Start | Copy-pasteable install + run commands (60-second rule) |
| Features & Config | Command tables + collapsible advanced config |
| Architecture | Mermaid.js diagram (optional, only if meaningful) |
| Community | Contributing link, Discord, good-first-issue, contributors wall |
| Sponsors | GitHub Sponsors badge (optional) |
| Star History | Star history chart (optional) |
| Footer | License link, author credit |

**Quality rules:**
- No placeholder images - text-only hero if no logo exists
- Badges point to real URLs constructed from project metadata
- All code blocks are copy-pasteable (no `$` prefix)
- Collapsible `<details>` for anything over 15 lines
- Under 300 lines total for most projects
- Dark/light mode support via `<picture>` tags

---

## Commands

### `/maintain-readme`

Audit, restructure, and improve an existing README.md - verifies accuracy against the codebase, fixes stale links and stats, improves structure, and optionally rewrites sections.

| | |
|---|---|
| **Use for** | Stale stats/badges, outdated feature lists, structural improvements, full restructure |

**Audit levels:**

| Level | What it does |
|-------|-------------|
| **A) Fix facts only** | Correct counts, versions, paths, badges, links |
| **B) Fix facts + improve structure** | Reorder sections, add missing sections, apply progressive disclosure |
| **C) Full restructure** | Rewrite following readme-craft best practices, rebuild information architecture |

---

**Related:** [codebase-mapper](codebase-mapper.md) (technical documentation) | [project-setup](project-setup.md) (CLAUDE.md files)
