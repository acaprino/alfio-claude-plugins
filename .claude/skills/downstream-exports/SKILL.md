---
name: downstream-exports
description: >
  How our content reaches hosts that are not Claude Code: the three adapters, what each
  host expects a package to look like, how the compiler renders harnesses from templates,
  how a neutral policy gets a host implementation, when a fingerprinted semantic override is
  the right answer, and the content that deliberately keeps host-as-subject vocabulary.
  TRIGGER WHEN: changing an adapter layout, capability binding, coordination strategy,
  harness template, policy implementation or override, or diagnosing why one host's package
  came out differently from another's.
  DO NOT TRIGGER WHEN: pulling content IN from an external repo (use `external-repo-intake`
  or `upstream-sync`), or editing plugin behaviour, which lives in the kernel under
  `plugins/` and is host-neutral by rule.
---

# Downstream exports

The mirror image of the `external-repo-intake` skill. That skill covers content flowing *in* from other repos; this one covers our content flowing *out* to the three hosts.

**Nothing under `exports/` is edited by hand, ever.** Every file there is compiler output from `plugins/` plus `adapters/`, and `python scripts/daodan_build.py --check` fails the build the moment a committed package stops reproducing from its source. If an export looks wrong, the bug is in the kernel, the adapter, or the compiler. Fixing the export directly produces a change that the next build silently deletes.

## The split that decides where a change goes

The core owns roles, workflow dependencies, required context isolation, joins and observable contracts. A harness owns host APIs, dispatch, scheduling, retries and result collection.

| The change is about | It belongs in |
|---|---|
| what a reviewer looks for, what a workflow means, what a report must contain | `plugins/<name>/` (Markdown for behaviour, TOML for structure) |
| which host tool satisfies a neutral capability | `adapters/<host>/capabilities.toml` |
| which coordination strategies a host supports, and in what order | `adapters/<host>/coordination.toml` |
| where a component lands in a host's package | `adapters/<host>/layout.toml` |
| the wrapper text that tells a host harness how to dispatch | `adapters/<host>/templates/` |
| how one host enforces a neutral policy | `adapters/<host>/policies/<name>/` with `policy.toml` naming what it `implements` |
| a meaning that genuinely cannot be rendered from the generic templates | `adapters/<host>/overrides/<plugin>/<workflow>/` |

**Never name a host tool, team API or dispatch primitive in neutral content.** That is the rule the whole split rests on: the moment a kernel says `Agent` or `runCommands`, one host's vocabulary has become everyone's contract.

## What each host expects

| | claude | copilot | codex |
|---|---|---|---|
| catalog | `.claude-plugin/marketplace.json` | `.github/plugin/marketplace.json` | `.agents/plugins/marketplace.json` |
| plugin manifest | `.claude-plugin/plugin.json` | `plugin.json` | `.codex-plugin/plugin.json` |
| roles | `agents/<role>.md` | `agents/<role>.agent.md` | `roles/<role>.md` |
| workflows | `commands/<workflow>.md` | `prompts/<workflow>.prompt.md` | `skills/<workflow>-workflow/SKILL.md` |
| skills | `skills/<skill>/SKILL.md` | same | same |
| source reference | `./exports/claude/plugins/<name>` | `./exports/copilot/plugins/<name>` | `source = "local"` plus `path` |

Codex suffixes workflow directories with `-workflow` on purpose: it is the one host that renders both skills and workflows as skills, and without the suffix a plugin that has a skill and a workflow of the same name (`codebase-xray:analyze` does) would collide on disk. That suffix is why component names may repeat across kinds; within a kind they may not.

## Harness rendering

A workflow whose phases fan out is not copied, it is rendered through that host's harness template, which wraps the neutral body with the dispatch obligations the contract requires: isolated worker contexts, the delivery barrier, the single-writer rule for the report, and a **dispatch plan**. The templates are `claude/templates/team-workflow.md.tmpl`, `copilot/templates/coordinator.agent.md.tmpl` (plus `worker.agent.md.tmpl` for the roles) and `codex/templates/subagent-workflow.SKILL.md.tmpl`.

The dispatch plan (`${dispatch_plan}`) is one numbered line per phase of the sidecar, in order: how many workers (once each for a static `fanout`, one per item for a `fanout_from` selection, one for a single `role`, none for a shared phase), in what context, at what concurrency, behind which barrier, and what the phase needs, consumes and produces. It replaced a header that said "dispatch the selected roles, once each", which was right for one wave of reviewers and wrong for `codebase-xray:team-analyze`, which fans out one worker per partition across three waves: on Codex and Copilot that header was the only dispatch guidance, and read literally it produced one structure worker for the whole codebase.

The Copilot coordinator's `tools` line is derived, not fixed: every capability the plugin requires whose binding carries a `value` contributes that tool, and `repository.read` and `roles.dispatch` are always included. That is why `roles.dispatch` carries `value = "agent"` in the Copilot bindings. A coordinator that writes run state, runs a detection script and publishes a mirror gets `edit` and `runCommands` because its kernel declared `repository.write` and `shell.execute`, and a hand-written `['agent', 'search']` would have left it unable to do any of that.

Copilot is the only host that rewrites role frontmatter: the compiler maps Claude-shaped tool names onto Copilot's (`Read`/`Glob`/`Grep` to `search`, `Write`/`Edit` to `edit`, `Bash` to `runCommands`, `WebFetch`/`WebSearch` to `fetch`, `Agent`/`Task` to `agent`) and flattens the description to a quoted one-liner. Frontmatter scalars are rendered inline, so a description carrying a colon or a stray quote is what breaks a whole block: that failure mode is the reason `_one_line` exists.

Substitution is `string.Template` with an allowlisted context (`scripts/daodan/templates.py`). An unknown placeholder is an error, never an empty string, and a layout path that escapes its package is refused.

## The two Claude placeholders a kernel may write

A kernel body says `${CLAUDE_PLUGIN_ROOT}/skills/x/scripts/y.py` because the bundled-path linter requires that form: it is what survives installation on Claude. It says `$ARGUMENTS` because that is what a Claude command expands. Neither is defined on Copilot or Codex, so the renderer rewrites both per host from four layout keys, and inserts the host's explanation once, after the frontmatter, in every Markdown file that uses the reference:

| key | claude | copilot | codex |
|---|---|---|---|
| `plugin_root_reference` | `${CLAUDE_PLUGIN_ROOT}` (itself) | `${PLUGIN_ROOT}`, which Copilot CLI documents for paths inside the plugin directory | `<plugin-root>`, a marker the agent resolves once: Codex hands `PLUGIN_ROOT` to hook commands only |
| `plugin_root_note` | none | names `plugin.json` as the directory to find | names `.codex-plugin/plugin.json` |
| `arguments_reference` | `$ARGUMENTS` (itself) | `<arguments>` | `<arguments>` |
| `arguments_note` | none | "substitute what the user typed after the prompt name" | "... after the skill name" |

Claude's keys map each placeholder onto itself and carry no note, so its packages are unchanged by this pass. Only the `${CLAUDE_PLUGIN_ROOT}` form is rewritten; a bare `$CLAUDE_PLUGIN_ROOT` would pass through and fail `tests/test_daodan_host_rendering.py`.

A workflow that does not fan out is rendered under host frontmatter from the `workflow_frontmatter` layout key, which lists the keys the host reads in order: Claude has none and gets the kernel file verbatim, Codex gets `name` and `description` with the argument hint moved into the body as an `Arguments:` line, Copilot gets `name`, `description` and `argument-hint`, which its prompt files support.

Which strategy each host selected is recorded per package in `.daodan-provenance.json`, together with the kernel digest and any overrides applied. Topology names may differ between hosts; contract assertions may not.

## Overrides are a last resort, and they expire

An override replaces one rendered file for one host, and it carries the digest of the neutral source it was reviewed against. When that source moves, the override is reported `stale-override` and the build fails until a human re-reads it. An override may select a different declared mechanism; it may never add a tool, MCP server, LSP server, hook or capability the kernel did not declare (`override-capability-escalation`), and it may not quietly drop a contract the workflow declares (`override-drops-contract`).

There are currently no overrides at all. Every host divergence so far was expressible through the generic templates, which is the outcome the gate exists to make visible rather than to encourage. Reach for one only after establishing that a *behavioural contract* cannot be rendered generically. A different topology is not a reason; a different meaning is.

## Policies: what is enforced where

A neutral policy under `plugins/<name>/policies/` says what must hold. An adapter's `policies/<name>/policy.toml` says how one host makes it hold, and the compiler ships that implementation inside the package. Only one such implementation exists, `copilot/policies/xray-guard` for `codebase-xray`'s `write-confinement`, and it is shipped but not wired, for reasons that bind any future policy:

- **A plugin-level hook is session-global.** `hooks/hooks.json`, which Claude Code and Codex both read, fires for every tool call of every agent while the plugin is enabled. A confinement rule there would refuse every write outside `.codebase-xray/` in every session. A confinement policy can never ship as a plugin hook, on any host.
- **Per-agent hooks are the right mechanism and are not yet safe to generate.** Claude agent frontmatter and VS Code custom agents accept a `hooks:` block scoped to that agent. A hook command that fails to find its script does not fail open: a non-zero exit blocks that worker's every tool call, and `${CLAUDE_PLUGIN_ROOT}` is not reliably expanded in agent-frontmatter hook commands. Copilot CLI does not run plugin hooks at all (github/copilot-cli#2540).
- **So the policy is prompt-level everywhere**, carried by the worker prompts and the ownership contracts in the roles, and the kernel's `write-confinement.toml` says so in its `[enforcement]` table. Wire a mechanism only after a host probe shows a per-agent hook running from an installed plugin, and wrap the command so a missing script allows rather than blocks.

## Content that deliberately keeps host-as-subject vocabulary

`marketplace-ops` and `ai-tooling`'s `agent-sdk-builder` are *about* the agent tooling, so their tool names and trigger labels are content rather than accidental host coupling. Never de-brand or tool-rename them.

## Verification

```bash
python scripts/daodan_build.py                 # publish all three hosts
python scripts/daodan_build.py --check --support   # drift gate plus the per-host support table
python -m unittest discover -s tests           # compiler, port and parity contracts
python adapters/copilot/policies/xray-guard/test_xray_guard.py
```

A plugin reported `unsupported` on any host blocks the release: it means a required capability has no binding, or no coordination strategy satisfies its workflow. Fix the binding or the workflow. Never soften the contract to make a host pass.

## What this skill used to cover, and why it no longer does

Until the universal cutover this repository hand-mirrored a per-plugin VS Code bundle catalog, generated an extension manifest, packaged a `.vsix` and released it on a tag. All of it is gone: the bundles, `mirror_export.py`, the export structural checker, the manifest generator, and both workflows that served them. The compiler replaced the obligation with a gate, which is the point. Do not rebuild any of it, and do not reintroduce a second hand-maintained copy of a plugin for any host.
