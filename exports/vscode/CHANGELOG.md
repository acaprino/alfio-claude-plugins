# Changelog

## 19.5.0

- Mirrors the description trim that cut the plugin corpus by about 35%. 169 agent, skill and prompt descriptions across 35 bundles now carry the shortened text, adapted as usual: routing labels become `Use when` / `Not for` prose, namespaces are de-prefixed, and the `_pipelines` renames (`review-*`, `xray-*`) are applied. Only descriptions changed; no body, no `tools:` list, no contribution path, so `package.json`'s agent and prompt arrays are untouched.
- A description sits in context in every session while the body loads only on invocation, so anything a description restated from its own body was cost with no routing value. The cut removed enumerations the bodies already carry, sentences repeated inside a single description, and a contentless exclusion clause that a scaffolding template had propagated to 29 components. Every distinctive trigger term and every sibling cross-reference survives.
- Two same-name pairs that had been describing each other now divide by role: the `abstraction-architect` skill takes the phrases a user types while its agent takes its pipeline coordinates, and the same split applies to the GA4 knowledge base and its expert agent. The six `codebase-mapper` Phase-2 writers, previously near-identical boilerplate, collapse to one line each.

## 19.3.0

- New `peer-review` bundle, the 38th: the `/review` prompt, the export-only `peer-review-orchestrator` agent, and the `packet-builder` and `respondent` subagents it dispatches, plus the `cross-model-peer-review` skill. Cross-model peer review of plans and specs: a challenge packet with GIVEN-tagged context, challenger findings that each carry their own falsifier, evidence-backed responses at file:line, a verbatim ledger, a certification pass the challenger owns, and a verdict computed from the ledger.
- The bundle ships the same transport-only MCP server the upstream plugin ships (`.github/skills/cross-model-peer-review/mcp/server.py`, byte-identical to the Claude Code copy), because it names no Claude Code mechanism anywhere in its own source and runs unchanged under any MCP-compliant client. Wiring it into Copilot needs a hand-added `.vscode/mcp.json` entry, documented with a snippet in the bundle's own README, since VS Code has no plugin-root auto-discovery equivalent to the path-expanding `.mcp.json` Claude Code reads on install.
- `peer_profiles` and `peer_ask`, the two MCP tool calls the orchestrator makes, are referenced by bare name rather than Claude Code's `mcp__<server>__<tool>` convention, and the orchestrator ships with no `tools:` allowlist at all: an MCP server's tool ids depend on the name the user gave that server, the same reasoning that already left the catalog's five browser-driving agents without one.
- `respondent.agent.md` restates the `receiving-code-review` discipline inline instead of loading it: that skill belongs to the upstream Claude Code plugin `superpowers`, not ported to this catalog, matching how the `testing` bundle already treats `mattpocock/skills` and `wshobson/agents`.
- The protocol itself (`PROTOCOL.md`, `finding-lifecycle.md`, `packet-anatomy.md`, `round-prompts.md`) travels byte-identical to the plugin's copy: it is deliberately harness-independent and names no tool, vendor, model, or transport, so this is the one part of the mirror with nothing to adapt.

## 19.2.0

- Tracks marketplace 19.2.0 (`senior-review` 9.0.0, `codebase-xray` 2.2.0). The `_pipelines` bundle now enforces one rule end to end: evidence derived from a shared artifact cannot corroborate the claims in that same artifact. N reviewers agreeing on a premise they were all handed is one observation, not N. The old pipeline derived context once and then explored it with fifteen agents, which produced confident agreement about whatever the first observer got wrong.
- Every reviewer finding now declares two fields: the **load-bearing premise** (the single proposition whose falsity collapses the finding, required to be minimal, falsifiable and scoped) and its **premise_provenance** (`independent`, `shared-context` or `mixed`, recording causal dependence rather than citation). Twelve reviewer agents carry the fields in their output formats, and the `/team-review` prompt template requires them.
- New agent `review-premise-auditor` runs in a new Phase 1c, in parallel with the X-ray pass and blind to it: no `.deep-dive/` in any form, no interconnect map. It derives claims from the diff, the code and the tests, hunting specifically for multiplicity (a probe path beside a periodic one, a bootstrap path beside a steady-state one). It never compares its own output, which is what makes the blindness verifiable instead of merely asserted. Phase 1d reconciles the two derivations into `01-knowledge-provenance.md` and turns every contradiction into a `disputed` row in the map.
- The verification panel goes from three lenses to four. **Lens 0** attacks the finding's premise rather than the finding, runs first, and is gated on provenance: `independent` findings skip it. It is a veto, not a vote, because local correctness cannot outvote a refuted premise; a verifier can be entirely right that the cited line does what the finding says while the inference to the conclusion is dead because another path exists. It may only refute on a `file:line` counterexample, and a refutation targeting the PREMISE kills the finding while one targeting shared SUPPORT strikes only that leg.
- The interconnect map is relabelled in its own header as a fallible hypothesis index rather than ground truth, and every row now carries a status. A fourth value, `disputed`, means two derivations reached incompatible conclusions with both sides cited and neither resolved. `Missing` and `Disputed` are kept as separate states throughout: absence of evidence is not contradictory evidence.
- `review-logic-integrity-auditor` is rewritten from map-first to map-first-never-map-authoritative. An empty map section is now a hypothesis that lowers a category's priority rather than a fact that removes it, and the targeted hunt gained an independent-discovery step and a contradiction hunt that are not optional when the mapped anchors produce nothing.
- Consolidation weighs agreement by provenance. Findings that agree from disjoint or independent premises are **corroborated**; findings that agree from the same shared premise are an **echo**, reported as such, raising neither confidence nor severity. The context utilization rate is demoted from a quality metric to an operational one, since a high value on a wrong map is the signature of the failure this work exists to prevent.
- X-ray gains an always-on Phase 0, Project Knowledge Discovery, which runs at every depth including lite and writes `knowledge/navigation.md` and `knowledge/documentation-leads.md`. It separates two roles a document plays: as evidence it stays an unverified claim, but as a **discovery lead** it is a first-class input to collect early. Refusing to read a project's own index does not make the analysis more rigorous, it makes it blind to intent.
- **Breaking:** `/team-review`'s `--skip-interconnect` is renamed `--no-context` with no alias. The X-ray pipeline keeps its own `--skip-interconnect`, which is a different flag with a different meaning: there it skips only the interconnect map. Raw mode also now skips the new Phase 0c, because knowledge leads distributed to N reviewers would themselves be shared context.
- Two deliberate divergences from the Claude Code source, both recorded in the files that carry them. Lens 0 runs on `review-verification-lens` rather than on `review-premise-auditor`, so that the blind deriver and the fully-primed challenger are different agents and the blindness is structural rather than instruction-dependent. And the Phase 1d reconciliation runs on the orchestrator rather than inside the mapper, because the map here is produced within the X-ray run, which `/team-review` dispatches as one unit.

## 19.1.3

- Security correctness fix in the `ai-tooling` bundle (plugin 5.0.1), found by running the eval harness against the plugin for the first time. The hook examples in `agent-sdk-builder` returned `{ behavior: "deny", message }`, which is `PermissionResult`, the shape belonging to the `canUseTool` callback. A hook returning it matches no variant of `HookJSONOutput` and is ignored at runtime, so a guard written from that documentation looks installed and allows everything. Hooks now return `hookSpecificOutput: { hookEventName, permissionDecision, permissionDecisionReason }`, and the return-values section leads with why this particular confusion is the dangerous one: it fails silently and in the safe-looking direction.
- The same pass fixes hook input fields to the declared snake_case (`tool_name`, `tool_input`, not `event.toolName`) and drops a wrong "(TypeScript only)" note on the `dontAsk` permission mode. All verified against `@anthropic-ai/claude-agent-sdk@0.3.226` type definitions.
- This defect was introduced by the 19.0.1 security fix itself, which moved validation into a `PreToolUse` hook and wrote that hook with the callback's return shape. The fix for the original defect shipped a subtler version of it.
- `prompt-engineer` gains two rules the same run earned. The semantic diff must now name what it compared on the Interface line, because "Interface: unchanged" is true of almost any rewrite once it is quietly scoped to key names while the schema literal has changed. And the rubric gains an explicit "when the prompt is already good" section: saying so and stopping is a real conclusion, and three specific ways a rewrite grows without improving (restructuring justified as clarity alone, examples added to an already unambiguous format, behaviors that reach the rewrite without appearing in the diagnosis) are named as defects.

## 19.1.2

- Export-only release. Defines `$SKILLS` in the 19 bundle files that used it without saying what it resolves to, so an agent loading any of them alone knows where the skills directory is instead of guessing. Eighteen of those were introduced by 19.1.1 itself, which rewrote paths to `$SKILLS/...` without carrying the definition along: six `_pipelines` review agents, ten `codebase-mapper` agents and two of its prompts, plus the pre-existing `marketplace-audit` skill.
- The `tauri-development` bundle's stale-builds reference drops a self-referential path inside an example error string, matching the wording the plugin already uses. 19.1.1 had rewritten it to a `$SKILLS` path, which meant nothing in that position and diverged the mirror from its source.
- A ninth structural check (`$SKILLS defined where used`) now enforces this, closing a blind spot the export checker had carried since the catalog build. It recognizes a definition by the candidate roots it enumerates rather than by a fixed sentence, because the wording legitimately varies across bundles.

## 19.1.1

- Fixes 40 references that named a path only resolvable in a checkout of the source repository, across `business`, `codebase-mapper`, `python-development`, `senior-review`, `stripe` and `tauri-development`. The bundles were mostly already correct, since the port rewrites paths to `$SKILLS/...`; this release repairs the 22 that had been mirrored verbatim, and the upstream plugins that were broken for every installed user.
- What was failing in the bundles: `defect-taxonomy` reference loads in six `_pipelines` review agents (chicken-egg, code-auditor, distributed-flow, logic-integrity, security, ui-race), and `audience-adaptation.md` register calibration in ten `codebase-mapper` agents plus the `/docs-create` and `/humanize-docs` prompts. Those reads silently resolved to nothing, so the agents ran without the knowledge base they were written around.
- `/audit-webhooks` in the `stripe` bundle drops a parenthetical that pointed at an agent file by source path; the agent is spawned by name and always was.
- Backed by a new consistency check (`scripts/lint_bundled_paths.py`) so the class cannot return. Its grandfathered-debt list is deliberately empty: everything it found on its first run was fixed rather than baselined.

## 19.1.0

- Tracks marketplace 19.1.0, which restructures the `ai-tooling` bundle (plugin 5.0.0) around the distinction between knowledge that ages and knowledge that does not. Follows the 19.0.1 correctness refresh of the same bundle; this release changes its shape rather than its facts.
- `agent-sdk-builder` goes from one 1068-line file to a 153-line decision core plus five on-demand references (`sdk-api`, `sessions-subagents`, `permissions-hooks-security`, `mcp-plugins-skills`, `deployment`). The core now carries a three-tier source-of-truth policy: the project's installed SDK first, then current official documentation, then these bundled files, which are explicitly never the last word on a signature, an option shape, a default, or whether a feature still exists. A claim-classification table (STABLE / API-SENSITIVE / MODEL-SENSITIVE) says which of its own statements the agent must re-verify, and environment detection now records the installed version so every answer is relative to it. The 19.0.1 refresh fixed the facts that had drifted; this one is meant to stop the drift from mattering.
- `prompt-engineer` extracts a behavioral contract before rewriting anything (goal, hard constraints, behavioral invariants, interface, intentional freedoms, trust boundaries, known failure modes) and reports a semantic diff afterwards, so a rewrite that quietly stopped doing its job is a reportable defect rather than a silent one.
- Its rubric became archetype-aware: eight archetypes, eleven dimensions, five of them conditional, with everything else marked N/A. The old universal rubric rewarded the wrong shape, scoring a creative prompt on output determinism or an exploratory one on maximum specificity. The weighted average is gone; the target is the right profile, not 5/5 everywhere.
- Mandatory self-evaluation is replaced by audit depth proportional to consequence, split on one question: if this prompt regresses, who finds out?
- Quality claims are now labeled predicted, measured, or verified, and never interchangeably. `/prompt-optimize` follows: the scorecard is renamed diagnostic and marked predicted, the comparison column reads "predicted effect (unmeasured)", a behavioral-changes section reports what each variant changed in behavior, and Phase 1 classifies the archetype instead of scoring six fixed dimensions.

## 19.0.3

- Tracks marketplace 19.0.3, which de-dogmatizes four rules of the `testing` bundle (plugin 2.2.0) after an external review found them stated as universal invariants where they hold only under conditions.
- Test oracles: the "Hardcoded Golden Values" anti-pattern in `test-writer` became "The Mirrored Oracle". The old rule flagged `assert total == 660` and prescribed deriving the expected value from the inputs, which is the recipe for a test that reimplements the production algorithm and passes when both share a bug. The rule now targets that tautology directly: an explicit, independently derived expected value is the strongest oracle, and invariants or tolerances are for when the complete value is impractical or the property itself is the contract.
- Test ownership is now scoped per layer in `test-hygiene` (rules 2 and 3) and in `test-suite-auditor` D1. One file per source file still binds unit tests; integration, contract, and e2e tests are behavior-owned and legitimately span several source modules. The violation above the unit layer is an unexplained second file for the same behavioral scope, not multi-module reach. `/test-consolidate` Step 5 rewrites one file per owner accordingly.
- Cross-layer overlap is no longer duplication by definition. `test-suite-auditor` D5 flags it only when two tests protect substantially the same failure mode through the same observable contract without adding independent risk coverage; a business invariant defended at several layers against different failure modes is defense in depth, and a new anti-pattern entry says not to flag it.
- Quarantine age became a signal rather than a verdict: an entry older than 3 months is a deletion candidate needing corroborating evidence (feature removed, replacement coverage, temporary origin, no bug-fix provenance) through the consolidation approval gate, instead of being deleted without discussion.

## 19.0.2

- Repair release with no new content. The 19.0.0 restructure (codebase-cleanup retired, dependency-audit added) had been prepared in the working tree but not committed when the 19.0.1 refresh was cut; that commit swept in the registry, changelog and manifest halves without the files. This release lands the remaining files (the dependency-audit bundle, the codebase-cleanup removals, the `review-cleanup-auditor` D6 update) so the shipped tree matches the manifest again.

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
