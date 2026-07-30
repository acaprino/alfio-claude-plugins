---
name: downstream-exports
description: >
  How to mirror our content OUT to hosts that are not Claude Code: the `exports/vscode/`
  catalog and its source map, the adaptations to re-apply on every mirror, the divergences
  that must survive a sync, the content that deliberately keeps Claude Code vocabulary, the
  method for a full re-audit, and the verification script plus its known false positives.
  TRIGGER WHEN: the user asks to update, mirror, regenerate, or audit anything under
  `exports/`, or a change lands in any plugin file, since as of the 2026-07-30 catalog
  build every plugin except `prompt-improver` feeds a bundle.
  DO NOT TRIGGER WHEN: pulling content IN from an external repo (use `external-repo-intake`
  or `upstream-sync`), or changing a file this skill's source map does not list.
---

# Downstream exports

The mirror image of the `external-repo-intake` skill. That skill covers content flowing *in* from other repos; this one covers our content flowing *out* to hosts that are not Claude Code. `exports/<host>/` holds those ports.

**Direction is one-way: `plugins/` is the source of truth, `exports/` is derived.** Never edit an export and back-port to the plugin. If a fix belongs in both, make it in `plugins/` first, then mirror. A defect found while auditing the export is often an upstream defect faithfully mirrored: check the source before assuming drift.

## Active exports

| Export | Host | Shape |
|---|---|---|
| `exports/vscode/` | VS Code Copilot (`.github/skills/`, `.github/prompts/`, `.github/agents/`) | A catalog of 36 independently installable bundles |

**The obligation is now global, not scoped.** Until the 2026-07-30 catalog build only five plugins fed the export. Now every plugin except `prompt-improver` has a bundle, so any plugin change is a candidate mirror. Do not go looking for the old five-row source map: it is gone.

## Source map

One bundle per plugin, at `exports/vscode/<plugin>/.github/`, with `skills/<name>/` mirroring `skills/`, `agents/<name>.agent.md` mirroring `agents/<name>.md`, and `prompts/<name>.prompt.md` mirroring `commands/<name>.md`. Three exceptions:

| Exception | Detail |
|---|---|
| `_pipelines` | Carries three plugins whole: `codebase-xray`, `senior-review`, `abstraction-architect`. It also vendors 14 superpowers skills plus their 6 agents, whose upstream is `obra/superpowers`, not `plugins/`. It has its own README and its own `metadata.version`. |
| `prompt-improver` | Not exported. It is a `UserPromptSubmit` hook; VS Code has no equivalent interception point. |
| Plugin-root content | `research/scripts/webfetch.py` and `ai-tooling/references/reasoning-patterns.md` live outside `skills/` upstream and are mirrored **into** the consuming skill's directory. A copy loop that only walks `skills/` silently misses them and leaves dangling references. |

Deliberately not exported, for reasons recorded in the catalog README: `/codebase-xray:analyze`, `/senior-review:code-review`, `/senior-review:pr-review`, `/abstraction-architect:audit`, and `/codebase-mapper:team-codebase-map`.

## Adaptations to re-apply on every mirror

A copied file is never correct as-is.

1. **Frontmatter conversion.** Claude Code `name` / `description` / `model: inherit` / `color` / `tools: Read, Write, ...` becomes VS Code `name` / `description` / `user-invocable` / `tools:` (YAML list of namespaced ids) / `agents:` / `hooks:`. Drop `model` and `color`. Skills add `license: MIT` and a `metadata` block (author, `source: acaprino/claude-code-daodan`, `upstream-plugin`). Prompts keep only `description`, optional `agent`, optional unquoted `argument-hint`.
2. **Routing labels become prose.** `TRIGGER WHEN: x` becomes `Use when x`; `DO NOT TRIGGER WHEN: y` becomes `Not for y`. The boilerplate "the task is outside the specific scope of this component" carries no information and is deleted outright. Watch the grammar: a naive rewrite produces `Not for the task is x`, which is wrong and appeared in nine files during the catalog build.
3. **Tool names.** `Read` -> `read/readFile`, `Grep` -> `search/textSearch`, `Glob` -> `search/fileSearch`, `Write` -> `edit/createFile`, `Edit` -> `edit/editFiles`, `Bash` -> `execute/runInTerminal`, `WebFetch` -> `web/fetch`, `WebSearch` -> `websearch`, `AskUserQuestion` -> `vscode/askQuestions`, Task-tool spawning -> `agent/runSubagent`. Applies to prose, not only frontmatter.
4. **Agent names.** Inside `_pipelines`: `senior-review:<x>` -> `review-<x>`, X-ray workers -> `xray-<x>`, `semantic-interconnect-mapper` -> `xray-interconnect-mapper`. In the catalog, agent names are kept as-is; they are already unique across all 36 bundles, and the checker enforces that.
5. **Plugin namespaces.** `plugin:thing` becomes a bare name inside its own bundle, and `` `thing` in the `plugin` bundle `` across bundles. `/plugin:command` becomes `/command`.
6. **`${CLAUDE_PLUGIN_ROOT}`** -> `$SKILLS`, defined once per file as the first of `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists. Any file that uses `$SKILLS` must define it.
7. **Task-status polling** (`TaskCreate` / `TaskList` / `TaskUpdate`) -> file-existence barriers verified with `#search/fileSearch`.
8. **Team infrastructure** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, `agent-teams` prerequisites, `shutdown_request`) -> delete.
9. **`agent-teams:team-reviewer` fallbacks** -> `review-generic-reviewer` with the dimension named in the dispatch prompt.
10. **The `PreToolUse` guard block** on every `_pipelines` worker and reviewer, with `--confine .deep-dive` or `--confine .team-review`. **Catalog bundles never declare hooks:** the guard script ships only in `_pipelines`, so a hook elsewhere would point at a path that does not exist.
11. **De-branding.** "Claude" as the actor becomes "the agent" or "the AI". See the exclusions below before running this over a whole bundle.
12. **Prose capitalization after the tool rename.** `Grep` mid-sentence becomes lowercase `search`, not `Search`.

### Dispatch, which is where the real work is

VS Code gates subagent dispatch behind an `agents:` allowlist, and a **prompt file cannot declare one**. That single constraint drives four different adaptations, and picking the wrong one produces a bundle that looks right and cannot run.

| Upstream shape | Adaptation |
|---|---|
| Command dispatches **one** agent | Bind it: `agent: <name>` in the prompt frontmatter, and rewrite the `Task:` block into direct instructions. No orchestrator needed. |
| Command dispatches **several** agents, or one agent several times with genuinely independent contexts | Write an export-only orchestrator agent holding the `agents:` allowlist, and bind the prompt to it. |
| Command dispatches one agent several times as **lenses on a single target** | Collapse into sequential passes. Parallelism there is a speed optimization, not an independence guarantee, and an orchestrator would be maintenance for nothing. `/content-strategy` is the worked example. |
| An **agent** dispatches another agent | Add the callee to that agent's `agents:` list. Agents can hold an allowlist; prompts cannot. `deep-researcher` -> `quick-searcher` is the case. |

Unwrapping a `Task:` block is not just deleting the wrapper. Its `prompt: |` body is indented four spaces as a YAML scalar; left alone it renders as one code block. De-indent it, and demote any `##` headers inside it so they nest under the surrounding section instead of colliding with it.

### Plugin dependencies

In `_pipelines`, degradation notes are **deleted**: every agent ships in the bundle, so a dimension is skipped only when its activation rule did not fire.

In the catalog the opposite holds, because bundles genuinely install separately. Cross-bundle pointers are correct and must carry an explicit "skip it if that bundle is not installed" clause. Only two references are real dependencies rather than prose, both declared in an orchestrator allowlist and both with a written degraded path: `codebase-mapper` wants `xray-interconnect-mapper` from `_pipelines`, and `research` wants `codebase-explorer` from `codebase-mapper`.

## Content that keeps Claude Code vocabulary

Two bundles have Claude Code as their **subject matter**. Their tool names, `TRIGGER WHEN` labels and `CLAUDE_CODE_*` variables are the material being taught, and renaming them makes the content false:

- **`marketplace-ops`** (the whole bundle) authors Claude Code plugin marketplaces.
- **`ai-tooling/.github/skills/agent-sdk-builder`** documents the Claude Agent SDK.

The verification script excludes both. Any new grep you write must too. This is the single easiest way to silently corrupt the export.

## Divergences that must survive the mirror

These are decisions, not drift. A sync that "fixes" them is a regression.

**Catalog-wide:**

- **The catalog is not one bundle.** VS Code loads every present agent and skill description for routing, so a monolith taxes every project with every plugin it does not use.
- **`/team-codebase-map` is dropped.** Minus the agent-teams layer it is identical to `/map-codebase`, which already runs its six writers concurrently.
- **`/content-strategy` runs three sequential passes**, not three concurrent dispatches.
- **`project-setup` targets `AGENTS.md` / `.github/copilot-instructions.md`**, honoring an existing `CLAUDE.md`. A note at the top of each file states the mapping; the substance is unchanged.
- **Five browser-driving agents ship with no `tools:` field.** An MCP server's tool ids depend on the name the user gave that server, so they cannot be allowlisted; omitting the field grants the full set. Each says so in a comment. Do not "fix" this by inventing ids.
- **`websearch` is declared in `tools:`** on the three agents that need it. It resolves once the Web Search for Copilot extension is installed, and is inert otherwise.

**Inside `_pipelines`:**

- No classic single-context X-ray; the single-partition fallback covers it, and `--phase N` is rejected explicitly.
- `/team-review` Phase 1a and 1b collapse into one X-ray run at `--depth=lite`.
- Reviewers read the X-ray run directory, never the `.deep-dive/` root mirror, which a concurrent run can republish mid-review.
- No model pinning on the verification lenses.
- The guard hook enforces only the unambiguous secret patterns; `*secret*` and `*credential*` stay prompt-level, because `secrets_manager.py` is a legitimate analysis target.
- Phase 0b detection is expressed on search tools, not a bash pipeline, so it works on Windows.

## Verification

One entry point, run from the repository root:

```bash
python .claude/skills/downstream-exports/scripts/check_export.py
```

Eight passes: frontmatter schema, tool ids, name uniqueness across bundles, prompt `agent:` bindings, `agents:` allowlists, residual Claude Code coupling, malformed markdown code spans, and byte-copy drift against `plugins/`. It exits non-zero on any failure and needs no dependencies.

Also run the guard hook suite when the guard, the forbidden-files list, or any `--confine` value changes:

```bash
python exports/vscode/_pipelines/.github/skills/codebase-xray/hooks/test_xray_guard.py
```

### False positives that have already cost a pass

Do not act on any of these without reading the hit in context:

- **Most tool-name matches are English verbs.** Across the catalog build, roughly 300 grep hits on `Read|Write|Edit|Glob|Grep|Bash` yielded about a dozen real references. "Write ONE test", "Read the input text", and `Text("Edit Profile")` inside a Compose example are all prose or code.
- **`site:apps.apple.com` is a Google search operator**, not a plugin namespace. So are `line:`, `http:`, and every YAML key.
- **"Claude" is often legitimate**: attribution comments, `acaprino/claude-code-daodan` in metadata, upstream repo names such as `dchuk/claude-code-tauri-skills`, and Claude named as a long-context LLM in a RAG comparison.
- **`tools:` lists are longer than they look.** `review-orchestrator` declares 16 ids; `vscode/askQuestions` sits at 15 and `todos` at 16 carries no namespace prefix. Parse the block to its terminator, which is what the checker does.
- **Legitimate frontmatter a naive schema check rejects:** `argument-hint` on orchestrators, `user-invocable` on skills, `compatibility` on `codebase-xray/SKILL.md`.
- **`codebase-xray:` inside `xray_guard.py`** is an error-message prefix, not a namespace.

### Traps found during the catalog build

- A `__pycache__/` directory was copied into a bundle. Exclude build artifacts when copying, and re-check after any bulk copy.
- Bulk string substitution damaged markdown twice: nested backticks produced `` ``/team-review` in the `_pipelines` bundle` ``, and a path rewrite hit an **attribution line** naming an upstream file rather than a runtime path. The code-span pass catches the first; only reading the diff catches the second.
- Each batch's greps found defects the previous batch's greps had missed, because the patterns kept widening. Always re-run the full check over the whole catalog, never only over what you just touched.

## Full re-audit

When the ask is to regenerate rather than mirror one change, **diff every file against its source; do not rewrite the files.** Rewriting to reproduce identical output adds risk without changing the result. Sort into four families:

| Family | How to audit |
|---|---|
| **Byte-copies** (scripts, assets, references naming no tool or agent) | `diff -q` against the source. Pass 8 of the checker does this automatically. |
| **Adapted** (every agent, prompt, skill that names a tool or agent) | Compare section headers, not whole bodies: `diff <(grep -o '^#\+ .*' src) <(grep -o '^#\+ .*' exp)`. A header present in the source and absent in the export is real drift, and the only thing worth reading line by line. |
| **Export-only** (orchestrators, `review-{generic-reviewer,verification-lens,completeness-critic}`, `xray_guard.py`, the READMEs) | Check internal consistency: allowlists, dispatched agent names, phase names. Nothing upstream to compare to. |
| **Vendored upstream** (the 14 superpowers skills, `agents/sp-*`) | Diff against `obra/superpowers` at the pinned version, never against `plugins/`. Tracked by the `exports/vscode` row of the `upstream-sync` sync table. |

## Versioning

`_pipelines` carries its own `metadata.version` inside `skills/codebase-xray/SKILL.md`. Bump it when its content changes, independently of the marketplace version. `exports/` is not registered in `marketplace.json` and is not a plugin.
