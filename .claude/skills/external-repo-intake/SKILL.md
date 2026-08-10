---
name: external-repo-intake
description: >
  Workflow for the FIRST vendoring of content from an external GitHub repository into this
  marketplace: classification, the four decision dimensions, the license compliance gate,
  fetch and inspect, convention adaptation, wiring the content into agents and commands,
  tracking, and the commit shape.
  TRIGGER WHEN: the user asks to "import", "pull", "vendor", "cherry-pick", or "borrow from"
  an external GitHub repository that is not already registered in the sync table of the
  `upstream-sync` skill.
  DO NOT TRIGGER WHEN: re-syncing a repository already registered in that sync table (use
  `upstream-sync`), refreshing a hand-authored plugin with no upstream (use
  `custom-plugin-refresh`), or mirroring our content outward to another host (use
  `downstream-exports`).
---

# External-repository intake

When the user asks to "import", "pull", "vendor", "cherry-pick", or "borrow from" an external GitHub repository (anything not already registered in the sync table of the `upstream-sync` skill), follow this workflow before touching any local file. This skill covers the *first* intake. Re-syncing repositories already registered uses the separate `upstream-sync` skill.

## 1. Classify the operation

We do not fork, submodule, or add runtime dependencies. The only intake mode for this marketplace is **vendoring**: a one-shot or tracked copy of upstream content into our tree, with attribution preserved and the content adapted to our conventions.

| Sub-mode | When to pick | Example |
|---|---|---|
| **Full vendoring** | Upstream is a complete drop-in (a single SKILL.md, a small set of references) and there is no local equivalent | `kotlin-development` |
| **Cherry-pick vendoring** | Upstream has many files but only a subset adds value, or the upstream commands collide with our existing namespace | `wshobson/agents` (3 codebase-cleanup commands imported, 2 agents skipped for overlap; the vendor was later retired in marketplace 19.0.0) |
| **Hybrid merge** | Upstream covers ground that overlaps with a local file; append upstream content as a delimited section instead of creating a duplicate | `wshobson/agents` e2e-testing-patterns `references/details.md` kept inline in the local SKILL.md sections (the vendor was later delegated upstream in marketplace 18.0.0) |
| **Inspiration only** | We adopt patterns or workflow ideas but write our own content from scratch; no upstream text copied | `codebase-xray` from `gsd-build/get-shit-done` |

Combinations are normal (the `wshobson/agents` intake used cherry-pick plus hybrid merge plus new files across codebase-cleanup and e2e-testing-patterns; its multi-agent generic core, the reverse-engineering vendor, and the e2e-testing-patterns vendor were all later delegated back upstream, and the codebase-cleanup vendor was retired outright in marketplace 19.0.0).

## 2. Decide the four dimensions

Before writing any file, lock down each dimension. State them back to the user via `AskUserQuestion` whenever a meaningful choice exists.

| Dimension | Question | Common answers |
|---|---|---|
| **Selection** | Full repo or cherry-pick? | Cherry-pick if upstream is large, has collisions, or carries unused infrastructure |
| **Merge** | Standalone new files or merged into existing local files? | Merge when overlap exists; standalone for orphan topics |
| **Sync strategy** | One-shot snapshot or ongoing sync? | Snapshot when upstream changes slowly or churn is unwanted; ongoing sync when upstream is actively maintained and aligned with our direction |
| **Tracking** | Register in the upstream-synced table or leave untracked? | Register only if "ongoing sync" was chosen; snapshots can still be registered for re-import convenience |

## 3. License compliance gate

Block before fetching:

1. Read the upstream `LICENSE` file. The four expected outcomes:
   - **MIT / BSD / ISC / Apache-2.0**: proceed; preserve attribution header in every derived file.
   - **MPL-2.0**: proceed for documentation-only content; flag to the user before importing source code.
   - **GPL-2.0 / GPL-3.0 / AGPL**: STOP. Ask the user explicitly; the marketplace is MIT and incompatible licensing must be a conscious decision.
   - **No license / proprietary**: STOP. Do not import.
2. For Apache-2.0 specifically, check whether upstream has a `NOTICE` file. If it does, preserve its contents alongside the derived files.
3. Attribution header on every derived file (new or merged section):
   ```
   <!--
   Portions of this file are derived from <owner>/<repo>
   (https://github.com/<owner>/<repo>), <SPDX-license> License.
   Snapshot YYYY-MM-DD.
   -->
   ```

## 4. Fetch and inspect (read-only)

Use `gh api repos/<owner>/<repo>/contents/<path>` with `--jq '.content' | base64 -d`. Save everything to `.upstream-scratch/<repo>/` (excluded from commits). Read every fetched file before writing local files. Count and assess size before proposing the merge plan.

## 5. Adapt to local conventions

Before saving any derived file, scan for and rewrite:

- **Dash-aside construct** ("X — Y — Z" / "X -- Y -- Z" / "X - Y - Z" bracketing a clause): replace with sentences, parentheses, or colons. Never substitute one dash form for another.
- **Emoji**: remove if the destination plugin's existing files have none.
- **Upstream-specific cross-references**: rewrite `[reference/foo.md](foo.md)` style links to point at the local destination path (or remove if the target was not imported). Rewrite `{{template_vars}}` and references to upstream-only commands.
- **Namespace prefixes**: rewrite upstream `<their-plugin>:X` skill references to the local `<our-plugin>:X` equivalent, or drop them when we vendor no equivalent.
- **Stale tool names** in team-related imports: `Teammate` / `Task tool to spawn` -> `Agent tool`; explicit `TeamCreate` / `TeamDelete` steps -> rewrite to implicit team formation (the team forms when the first teammate is spawned) and automatic cleanup at session end (both tools were removed in Claude Code 2.1.178).

## 6. Wire the new content into existing agents and commands

Importing content that no agent reads is wasted work. After saving derived files:

1. Add a `## References Library` (or equivalent) entry in the host plugin's `SKILL.md` that indexes every new/extended reference with a one-line topic description.
2. Update any command or agent that should now consult the new references. Add explicit `Read plugins/<plugin>/skills/.../<file>.md` instructions in the relevant prompt sections.
3. Avoid preloading discipline: the consumers must read references on-demand, not all upfront. State this in the wiring text.

## 7. Decide on tracking and re-sync

If the sub-mode is "ongoing sync" (or "snapshot but worth tracking for re-import"), append a row to the sync table in `.claude/skills/upstream-sync/SKILL.md`, with:
- Plugin (and sub-skill, if applicable) plus license tag for non-MIT sources
- Upstream repo plus the specific subpath
- Full list of derived local files and any merged sections

Then append the matching `gh api` fetch loop to that skill's "How to sync a plugin" code block. Do this even for snapshots; it makes a future re-import a one-command operation rather than archaeology.

If the sub-mode is "inspiration only", do NOT add a sync-table row. Add an inline note in the affected file describing what was adopted from where, but no sync entry.

Never add a sync-table row for anything listed under "Deliberately not vendored" in `CLAUDE.md`. Those areas were handed back to their upstreams on purpose.

## 8. Version bump and commit

- Bump every plugin whose `version` in `marketplace.json` had content added.
- Bump `metadata.version` (minor bump for first-time intake of a new upstream; patch bump for follow-up reworks of an existing intake).
- Single commit with the imported files, the local edits, the SKILL.md wiring, the sync-table update in `.claude/skills/upstream-sync/SKILL.md`, and the version bumps together.
- Commit message: `Cherry-pick / Vendor / Import <subject> from <owner>/<repo> (v<new>)` with a short description block listing new files, merged sections, license, and attribution date.

## 9. Verification before push

- `grep` derived files for any leftover upstream-only references, stale tool names, or dash-aside constructs.
- Validate `marketplace.json` JSON syntax.
- `git status` shows nothing in `.upstream-scratch/` staged.
- `git diff --stat` to sanity-check scope.
