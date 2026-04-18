---
name: maintain-readme
description: >
  Audit, restructure, and improve an existing README.md -- verifies accuracy against the codebase, fixes stale links and stats, improves structure following readme-craft best practices, and optionally rewrites sections.
  TRIGGER WHEN: the user asks to audit, update, or improve an existing README.md -- fix stale stats/links, reorganize sections, or apply readme-craft best practices.
  DO NOT TRIGGER WHEN: creating a new README from scratch (use docs:readme-craft skill) or auditing non-README docs (use /codebase-mapper:docs-maintain).
---

# Maintain README.md

## CRITICAL RULES

1. **Scan the codebase first.** Every claim, path, count, badge, and link in README.md must be verified against actual files.
2. **Show findings before changing.** Present the audit report and get approval before modifying anything.
3. **Respect the user's voice.** Preserve tone, personality, and intentional style choices unless the user asks to change them.
4. **Never enter plan mode.** Execute immediately.

## What This Does

Launches an interactive session to audit and improve your README.md. Goes beyond stale-link fixing -- evaluates structure, information architecture, adoption funnel, and overall quality against readme-craft best practices.

## Procedure

### Step 1: Codebase Scan (Silent)

Before any output, scan the project to build ground truth:

1. Read README.md (the file being audited)
2. Read CLAUDE.md, package.json, pyproject.toml, Cargo.toml, go.mod, setup.py
3. Read LICENSE, CONTRIBUTING.md, CHANGELOG.md
4. Scan source tree: entry points, key modules, exports
5. Check .github/workflows/, Dockerfile, CI configs
6. Count actual: plugins, agents, skills, commands, features, dependencies
7. Check all URLs/badges -- construct expected values from actual metadata
8. Read docs/ directory for content that README duplicates or should link to

### Step 2: Audit Report

Present findings organized by severity:

#### Critical (Factual Errors)
- Wrong counts, versions, or stats
- Non-existent file paths or broken relative links
- Badges pointing to wrong package/repo
- Commands that don't work
- Outdated tech stack claims

#### Structural (Information Architecture)
- Missing progressive disclosure (wall of text without collapsibles)
- Wrong section order for adoption funnel (hero -> proof -> why -> quickstart -> features)
- Key sections missing entirely (no quick start, no install, no feature list)
- Sections that belong in docs/ not README
- README too long (>300 lines without collapsibles)

#### Content Quality
- Value proposition unclear or buried
- Quick start not copy-pasteable or too many steps
- Feature descriptions vague or missing
- Badges missing or using wrong style
- No visual proof when screenshots/GIFs exist in the repo
- Community/contributing section missing when CONTRIBUTING.md exists

#### Freshness
- Stale version numbers in badges or text
- References to removed features or old APIs
- Links to moved or renamed files
- Stats that don't match current state (plugin count, command count, etc.)

### Step 3: User Decision

Ask the user what level of changes they want:

**A) Fix facts only** -- correct counts, versions, paths, badges, links. Keep structure as-is.

**B) Fix facts + improve structure** -- reorder sections, add missing sections, apply progressive disclosure, move deep content to collapsibles.

**C) Full restructure** -- rewrite following readme-craft best practices. Preserve content and voice but rebuild the information architecture from scratch. Apply the full adoption funnel: hero, visual proof, why, quick start, features, architecture, community, footer.

### Step 4: Apply Changes

Based on user choice:

1. Show a diff or summary of proposed changes
2. Get confirmation before writing
3. Apply changes to README.md
4. List any manual follow-ups (missing screenshots, broken external URLs, etc.)

## Audit Checklist

Verify each item against codebase ground truth:

- [ ] Project name matches manifest/repo
- [ ] Description/tagline matches actual purpose
- [ ] Badge URLs use correct repo path, package name, license
- [ ] Version numbers match manifest (package.json, Cargo.toml, etc.)
- [ ] Stats (plugin count, feature count, etc.) match actual filesystem
- [ ] Install commands work with current package manager
- [ ] Quick start steps are copy-pasteable and complete
- [ ] All relative links point to existing files
- [ ] All referenced commands exist
- [ ] Feature list matches actual capabilities
- [ ] Architecture diagram (if present) reflects current structure
- [ ] License in footer matches LICENSE file
- [ ] Author/org matches manifest
- [ ] No references to removed or renamed components

## When to Use

- After adding or removing features, plugins, or components
- When stats or counts are likely stale
- After major restructuring
- Before a release or public announcement
- When the README feels outdated or cluttered
- Periodic maintenance (monthly for active projects)

## Related

- `readme-craft` skill -- the best practices and structure this command audits against
- `/maintain-claude-md` -- similar audit workflow for CLAUDE.md files
