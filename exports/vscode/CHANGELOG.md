# Changelog

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
