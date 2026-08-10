# Changelog

## 19.0.1

- Tracks marketplace 19.0.1, a correctness refresh of the `ai-tooling` bundle (plugin 4.2.0) with every claim verified against the current Agent SDK documentation.
- `agent-sdk-builder` skill: the security section now separates coarse permission policy, always-on `PreToolUse` enforcement, and the `canUseTool` interactive fallback, and states explicitly that `canUseTool` never fires for calls already resolved by allow rules (the old "secure configuration" example placed its validation where it could not run). API drift fixed throughout: `forkSession` is a boolean used with `resume` (the standalone `forkSession()` function never existed), `plugins` takes `{ type: "local", path }` objects, `thinking` takes object shapes only, `outputFormat` nests `schema` directly, hook matchers are regex strings with array-form entries, the permission evaluation order has six steps, the removed TypeScript V2 preview section is now a removal notice, session-management and Python client methods match the documented API, and undocumented surface (`TodoWrite`, `TeammateIdle`, `task_progress`, `getSettings()`, `rewind_files()`) is deleted or marked *(verify)* under a new version-sensitivity note. Resource links moved to code.claude.com.
- `/prompt-optimize` no longer instructs the agent to reason inside `<analysis>` tags, which contradicted the prompt-engineer's own anti-pattern rule against explicit CoT scaffolds on reasoning models; the analysis phase is now private and Phase 2 defines the only output.
- `prompt-engineer` agent: terminal tools removed (least privilege; no workflow used them).

## 19.0.0

- Tracks marketplace 19.0.0, which retired the `codebase-cleanup` plugin and split its value.
- The `codebase-cleanup` bundle (3 prompts) is gone. A line-by-line review verified content defects worth not shipping (an `npm audit fix --force` auto-remediation script, a binary license-compatibility matrix, absolute code metrics presented as pass/fail gates, fabricated ROI figures); `/refactor-clean` and `/tech-debt` were also redundant with `clean-code`, `python-development`, and the hygiene and quality reviewers in `_pipelines`.
- New `dependency-audit` bundle (catalog stays at 37): the `/deps-audit` prompt and the `dependency-audit` skill with three references (per-ecosystem tool matrix, license-obligations analysis, verifiable supply-chain signal catalog). Evidence-first replacement for the old `/deps-audit`: real tooling only, TOOL-REPORTED / INFERRED / UNKNOWN evidence tiers, obligations-based license analysis instead of a compatibility matrix, strictly non-destructive remediation.
- `review-cleanup-auditor` in `_pipelines` gains the D6 lifecycle-archaeology dimension (session-transcript intent mining behind an evidence-not-instructions guard, commit-sequence migration inference, git auxiliary state), .gitignore archaeology in D3 (stale and overly-broad rules), and per-finding confidence tiers plus a residue-action taxonomy.
- Totals: 87 agents, 68 skills, 49 prompts.

## 18.4.0

- Tracks the marketplace's new `frontend-review` plugin, a pure orchestrator that reviews a frontend surface for design and code in one pass.
- New `frontend-review` bundle, the 37th: the `/review-frontend` prompt and the export-only `frontend-review-orchestrator` agent that dispatches it. Five dimensions, one scored report at `.frontend-review/report.md`: a design and UX pass that runs inline, plus React performance, TypeScript type safety, PWA architecture and platform compliance, each auto-detected from the project's own signals.
- The four code dimensions are cross-bundle references, declared in the orchestrator's allowlist and skipped with a named reason when their bundle is absent: `react-performance-optimizer`, `type-safety-auditor`, `pwa-architect` and `platform-reviewer`. That takes the catalog from four real cross-bundle references to eight.
- Divergence from the Claude Code original: there the design dimension is a hard gate on three external plugins, and the command stops with an install block when any is missing. None of the three has a Copilot install path, so this port probes for their four skill directories and degrades instead, running against whatever is present, skipping the dimension only when all four are absent, and naming each missing source with the repository to copy its skill directory from.
- Totals: 84 agents, 66 skills, 51 prompts.

## 18.3.1

- Correctness fixes to the `type-safety-rules` skill in the `typescript-development` bundle (tracks marketplace `typescript-development` 2.2.1): the `config-exact-optional` rule's incorrect example dropped a false JSON-serialization claim in favor of the real hazard, presence checks via `in` and `Object.keys`; the `assert-non-null` detection grep now matches a statement-final `!`; and the `/review-typescript` prompt's file-discovery `find` command groups its `-name` clauses so `.tsx` matches keep the `-type f` filter.

## 18.3.0

- Tracks the marketplace's new TypeScript type-safety review layer (`typescript-development` 2.2.0, `senior-review` 7.3.0).
- New in the `typescript-development` bundle: the `type-safety-rules` skill (20 rules across 7 categories, one file per rule, covering any erosion, unsound casts, boundary validation, assertion abuse, compiler configuration, exhaustiveness, and generics soundness), the report-only `type-safety-auditor` agent, and the `/review-typescript` prompt (diff-scoped by default, `--full` for a whole-tree pass, report at `.ts-review/report.md`).
- `/team-review` in `_pipelines` gains a conditional TypeScript type-safety dimension, activated when the changed files are `.ts` or `.tsx` and the project root has a `tsconfig.json`. It dispatches `type-safety-auditor` from the `typescript-development` bundle, a fourth declared cross-bundle reference. Unlike the testing dimension it has no generic fallback: the 20-rule checklist lives in that bundle, so the dimension is skipped and reported as "not installed" when the bundle is absent.
- Totals: 83 agents, 66 skills, 50 prompts.

## 18.0.0

- Tracks marketplace 18.0.0, which rebuilt the `testing` plugin around test-suite hygiene.
- The `testing` bundle drops its two vendored knowledge bases (`tdd`, `e2e-testing-patterns`): upstream they are Claude Code plugins with no Copilot install path, so the bundle now points at their GitHub repos instead of carrying copies.
- New in the `testing` bundle: the `test-hygiene` skill (search-before-write protocol, remediation ladder, per-runner playbook), the report-only `test-suite-auditor` agent, and two prompts, `/test-audit` (versioned TEST_AUDIT.md plus gated quarantine with `--fix`) and `/test-consolidate` (behavior-inventory-first module consolidation with a coverage gate). `test-writer` is now bound to the search-before-write protocol.
- `/team-review` in `_pipelines` prefers `test-suite-auditor` for its testing dimension, a third declared cross-bundle reference; `review-generic-reviewer` remains the fallback when the `testing` bundle is not installed.
- `project-setup` gains the conditional canonical `## Test-Suite Rules` block (7 binding rules), offered on create and verified on audit when the target project has a test suite.
- Totals: 82 agents, 65 skills, 49 prompts.

## 17.0.0

- Tracks marketplace 17.0.0, which removed the `prompt-improver` plugin from the source marketplace. Nothing changes in the shipped bundles: that plugin was never exported (a `UserPromptSubmit` hook with no VS Code equivalent). The listing no longer describes it and the `prompt-optimize` prompt drops its routing reference to the hook.

## 16.2.3

- The React performance optimizer is decoupled from Tauri. It no longer hands off to the `tauri-development` bundle: native desktop backend work (Rust, IPC, shell configuration) is reported as out of scope instead. The direction that remains is the correct one, where `tauri-desktop` routes pure React performance work here.

## 16.2.0

First release as a VS Code extension. The catalog was previously a set of 36 `.github/` bundles you copied into each project by hand.

- 81 agents and 47 prompts register through the `chatAgents` and `chatPromptFiles` contribution points.
- 66 skills are installed into `~/.copilot/skills/` on first start, so they load in every workspace. They are copied rather than contributed because 45 of them carry supporting files, and a contributed skill loads only its `SKILL.md` ([microsoft/vscode#304721](https://github.com/microsoft/vscode/issues/304721)).
- Commands to refresh, remove and reveal the installed skills, plus the `daodan.autoSync` and `daodan.skillsLocation` settings.
- Uninstalling removes only the skills the extension installed. A skill directory it did not create is reported and left alone.
- Fixes in the `research` bundle: `quick-searcher` and `deep-researcher` were missing `websearch` in their tool lists and so could not search the web; Claude Code tool names survived in prose; `$SKILLS` was used without being defined; and `team-research` had an empty section and a mangled step list left by the original port.

The bundles are still copyable per project for anyone who wants a narrower install.
