---
name: custom-plugin-refresh
description: >
  Maintenance protocol for hand-authored plugins that have no upstream to diff against:
  the four freshness risk classes and their cadences, where hard-coded versions hide, the
  re-research and surgical-edit update protocol, the refresh commit tag, and triage for
  picking what to refresh next.
  TRIGGER WHEN: the user asks to refresh, re-research, or fact-check a plugin that is not in
  the sync table of the `upstream-sync` skill; asks which plugins are stale or overdue; or
  asks about version drift in plugin knowledge bases.
  DO NOT TRIGGER WHEN: the plugin IS upstream-synced (use `upstream-sync`), the task is a
  first-time vendor of external content (use `external-repo-intake`), or the task is
  mirroring our content outward (use `downstream-exports`).
---

# Custom plugin maintenance

A "custom plugin" is any plugin NOT listed in the sync table of the `upstream-sync` skill. Its content is hand-authored or research-grounded and has no upstream source to re-pull. If a plugin is not in that sync table, it falls under this skill.

Custom plugins decay differently than vendored ones. There is no upstream commit to diff against. Versions, framework recommendations, breaking-change notes, and "current as of 2026" claims become stale silently. The maintenance protocol below is the antidote.

## Freshness risk classes

Classify each plugin into one of four classes. The class determines refresh cadence and triage priority.

| Class | What it tracks | Typical cadence | Examples |
|---|---|---|---|
| **Very fast** | Versions bump every few months; breaking changes are common; ecosystem reshuffles | Every 3 months | rag-development (embedding models, rerankers, vector DBs), digital-marketing/ga4-implementation (Consent Mode, GA4 events), react-development (React 19, Vercel guidance) |
| **Fast** | Framework releases 2-3x per year; APIs evolve | Every 6 months | libgdx-development, opentelemetry, tauri-development, stripe (API additions, webhook event types), grabber-development (anti-bot vendor moves), browser-extensions, pwa-expert (browser version churn, WebKit feature rollout, framework PWA library churn) |
| **Moderate** | Major releases ~yearly; breaking changes rare | Every 12 months | trading-broker-integration, csp (OR-Tools), python-development, typescript-development, messaging (RabbitMQ majors), obsidian-development, abstraction-architect (theory is stable; URL list in further-reading.md decays on a yearly cadence) |
| **Slow** | Workflow knowledge that ages by behavior change, not version bumps | Opportunistic; review only when symptoms appear | senior-review, codebase-mapper, team pipeline workflows, project-setup, marketplace-ops, system-utils, learning, docs, research, business, clean-code, codebase-xray, platform-engineering, testing methodology, xterm, app-analyzer, text-humanizer |

If unsure, default to "Fast" (6 months). Reclassify after the first refresh based on how much actually changed.

**`ai-tooling` is the exception to its own class.** Its workflow content is Slow, but `agent-sdk-builder` documents an SDK that ships breaking changes between minor releases, which puts that skill in **Very fast** (every 3 months). A 2026-08-10 fact-check found five drifted API claims at once: `fork_session` had changed type, `plugins` had changed from paths to config objects, `thinking` had moved to object-only shapes, the TypeScript V2 preview had been removed outright, and the migration guide's settings-source default had been superseded. Refresh the SDK skill on the fast cadence even when nothing else in the plugin has moved.

## Version-sensitive content: refresh the policy, not only the fact

A refresh that corrects today's facts leaves the same trap set for the next reader. Where a plugin documents a fast-moving external API, the durable fix is a source-of-truth policy plus a classification of its own claims, so the content tells the agent which of its statements not to trust. `ai-tooling` 5.0.0 is the worked example: a decision core carrying the tiers (the project's installed SDK, then current official documentation, then the bundled references) with the volatile detail moved into on-demand reference files, and a STABLE / API-SENSITIVE / MODEL-SENSITIVE table.

Two mechanics from that pass are reusable:

- **Mark what you could not confirm.** A claim that fails documentation resolution during a refresh is unconfirmed, not confirmed-absent. Tag it `*(verify)*` in place instead of deleting it or leaving it to read as verified. The tag is also the next refresh's work queue.
- **Prefer relative and substituted paths over repo paths.** `${CLAUDE_PLUGIN_ROOT}/...` and skill-relative `references/...` survive installation; `plugins/<name>/...` resolves only in a checkout of this repo. `python scripts/lint_bundled_paths.py` enforces this and carries the pre-existing debt as a baseline.

Where a refresh produces a behavioral invariant worth keeping (the frontier is never auto-picked; the installed SDK outranks the bundled reference), add a case to that plugin's harness under `evals/` rather than trusting the next reader to notice. `evals/ai-tooling/` is the pattern.

## Where hard-coded versions hide

Predictable hot spots, in priority order:

1. **Agent body** -- "Core Knowledge" / "Library Landscape" sections list package names and versions
2. **SKILL.md** -- "Quick Start" steps name install commands with versions
3. **References** -- changelog / breaking-changes sections; benchmark numbers; "as of YYYY" lines
4. **Audit command** -- checklists referencing specific version-gated features
5. **Marketplace.json description** -- if the description name-drops versions (e.g. "RabbitMQ 4.x coverage")

The agent and SKILL.md are the highest-value targets per minute of refresh effort. Reference files matter less for typical users (progressively disclosed) but matter most for power users.

## Update protocol

Steps to refresh a custom plugin. Same protocol regardless of risk class; only the cadence differs.

1. **Re-research the domain** with `research:deep-researcher`. Prioritize primary and recency sources in `Source families` at minimum. Prompt template (the spawn-block fields the agent's INPUT section expects, filled):
   ```
   Role: researcher
   Objective: <framework> current version, breaking changes since <version-in-plugin>, recommended
   baseline versions of dependencies, deprecations, ecosystem changes. Focus on facts that would
   change recommendations in an existing knowledge base.
   Boundaries: none
   Source families: official/primary docs and changelogs, recency (release notes, migration guides)
   Domain hint: <framework/domain>
   Backend: auto
   Budget: 15 searches / 12 pages / 4 rounds
   Return format: the researcher report
   ```
   Optional: add community sources to `Source families` if real-world usage patterns are part of what you cover.

2. **Diff the findings against the plugin**. Spawn Explore agents to grep the plugin for the specific version strings and section titles that came up in research. For each, decide:
   - **Clear win**: outdated fact with a confirmed replacement, apply Edit
   - **Subtle shift**: framework changed defaults but old approach still works, mention both
   - **No change**: research confirmed our content is still accurate
   - **Open question**: research was inconclusive, leave a comment and revisit next cycle

3. **Surgical Edits only**. Do not rewrite whole files. Replace specific lines and sentences. Preserve structure so future refreshes have stable anchors.

4. **Bump versions**. Patch bump for fact updates (`1.2.3 -> 1.2.4`). Minor bump if a new section, file, or reference was added (`1.2.3 -> 1.3.0`). Always bump `metadata.version` too (patch is fine unless the marketplace shape itself changed).

5. **Commit with a refresh tag**. Format:
   ```
   Refresh <plugin-name> for <framework> v<new-version> (v<plugin-version>)
   ```
   This makes the git log a searchable record of which plugins got attention when. Use this to decide what to refresh next: anything not touched in a full risk-class cadence is overdue.

## Triage on demand

When you sit down to do a refresh pass and don't know where to start:

```bash
# Plugins not refreshed in the last 6 months
git log --since="6 months ago" --name-only --pretty=format: -- plugins/ \
  | grep -v "^$" | awk -F/ '{print $2}' | sort -u > /tmp/recently-touched.txt

# Compare against the full plugin list in marketplace.json. The difference is your work queue.
```

Refresh the "Very fast" and "Fast" classes first if any are on the work queue; defer "Moderate" and "Slow" classes unless something specific prompted the review.

## When to upgrade a custom plugin to upstream-synced

If during a refresh you discover that someone else's open-source repo now publishes content that overlaps significantly with one of our custom plugins, evaluate vendoring it instead of maintaining from scratch. Follow the `external-repo-intake` skill, then add the plugin's row to the sync table in the `upstream-sync` skill.
