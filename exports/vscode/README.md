# codebase-xray + team-review for VS Code Copilot

A VS Code Copilot port of two multi-agent pipelines from [acaprino/claude-code-daodan](https://github.com/acaprino/claude-code-daodan):

- **`/xray-team-analyze`**: systematic codebase analysis. Combines mechanical structure extraction with semantic understanding, producing ground-truth documentation of WHAT, WHY, HOW, and CONSEQUENCES, followed by a structured map of contracts, invariants, and integration hot-spots.
- **`/team-review`**: multi-dimensional adversarial code review. Builds context with an X-ray pass, auto-detects which review dimensions the target warrants, dispatches up to 11 specialized reviewers in parallel, then runs a 3-lens verification panel and a completeness critic before reporting.

The second builds on the first: `/team-review` Phase 1 runs the X-ray pipeline to produce the context its reviewers hunt violations against.

Multi-language: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust.

## Install

Copy the bundle into your project:

```bash
cp -r exports/vscode/.github /path/to/your/project/
```

If the project already has a `.github/` directory, copy the three subdirectories individually:

```bash
cp -r exports/vscode/.github/skills/*  /path/to/your/project/.github/skills/
cp    exports/vscode/.github/prompts/* /path/to/your/project/.github/prompts/
cp    exports/vscode/.github/agents/*  /path/to/your/project/.github/agents/
```

VS Code picks up new skills, prompts, and agents without a restart. Verify with **Chat: Configure Agents** and by typing `/` in the Chat view: `/xray-team-analyze` and `/team-review` should appear.

For a monorepo where the bundle lives at the repository root but you open a subfolder, enable `chat.useCustomizationsInParentRepositories`.

Add `.deep-dive/` and `.team-review/` to your `.gitignore`.

### Optional: higher-fidelity parsing

The X-ray scripts need Python >= 3.10 and work with the stdlib alone. Tree-sitter improves Java, JavaScript, TypeScript, and Rust accuracy:

```bash
pip install -r .github/skills/codebase-xray/scripts/requirements.txt
```

Without it, those four languages fall back to regex extraction. Python always uses the stdlib `ast` module; SQL and PL/SQL always use the regex DDL extractor. The active parser is reported in the CLI output as `parser=stdlib-ast`, `parser=tree-sitter`, or `parser=regex-fallback`.

### Optional: tool-layer guard

Every worker and reviewer agent declares a `PreToolUse` hook pointing at `codebase-xray/hooks/xray_guard.py`. It enforces two rules the prompts already state:

1. Deny any tool call targeting a forbidden file: `.env` and its variants, `credentials.*`, `secrets.*`, `*.pem` / `*.key` / `*.p12` / `*.pfx`, `id_rsa*` / `id_ed25519*`, `.npmrc` / `.pypirc` / `.netrc`, and anything inside a `secrets/` or `credentials/` directory. Applies to every agent that declares the hook. The broader heuristics in the prose list (`*secret*`, `*credential*`) are deliberately not enforced here: a module named `secrets_manager.py` is exactly the kind of file the analysis should read and document, so that judgment stays with the model.
2. Deny any file-creating or file-editing call whose target lies outside the agent's session directory. X-ray workers pass `--confine .deep-dive`, reviewers pass `--confine .team-review`. Neither orchestrator declares the hook, since publishing and the quick-fix menu need source-file access.

Hooks are a VS Code preview feature. Enable `chat.useCustomAgentHooks` to activate the guard. Without it the hook block is ignored and enforcement falls back to the prompt instructions plus each agent's `tools` allowlist, which is what the pipelines assume anyway. The script is fail-open: an unparseable payload, an unknown tool name, or an unexpected key layout all resolve to "allow", so a schema change in VS Code degrades enforcement instead of blocking the run.

The hook command path assumes the bundle sits at `.github/skills/` in the workspace root. If you relocate the skills, either drop the `hooks:` block or repoint the command at the absolute path.

The guard ships with its own test suite. Run it after changing the guard, the forbidden-files list, or any agent's `--confine` value:

```bash
python .github/skills/codebase-xray/hooks/test_xray_guard.py
```

36 cases covering both confine values, the secret patterns, path traversal and absolute paths, and the fail-open paths. Stdlib only, no test runner, works from any working directory.

## Contents

```
.github/
├── skills/
│   ├── codebase-xray/          # X-ray skill: workflow, methodology, templates, 16 Python files
│   │   ├── hooks/xray_guard.py # the optional PreToolUse guard, shared by both pipelines
│   │   └── ...
│   ├── review-quality-gates/   # verification panel, completeness critic, context-sharing pattern
│   │   └── references/pipeline.md   # the full 6-phase team-review workflow
│   ├── defect-taxonomy/        # 140+ defect subcategories with CWE/OWASP mappings, 9 references
│   └── abstraction-architect/  # unification vs wrong-abstraction theory, 5 references
├── prompts/
│   ├── xray-team-analyze.prompt.md
│   └── team-review.prompt.md
└── agents/
    ├── xray-orchestrator.agent.md          # 6 X-ray agents
    ├── xray-{structure,behavior,quality}-worker.agent.md
    ├── xray-synthesizer.agent.md
    ├── xray-interconnect-mapper.agent.md
    ├── review-orchestrator.agent.md        # 15 review agents
    ├── review-{security,code,logic-integrity,cleanup}-auditor.agent.md
    ├── review-{ui-race,distributed-flow,api-contract}-auditor.agent.md
    ├── review-chicken-egg-detector.agent.md
    ├── review-react-performance-optimizer.agent.md
    ├── review-platform-reviewer.agent.md
    ├── review-abstraction-architect.agent.md
    ├── review-generic-reviewer.agent.md    # testing / migrations / general performance
    ├── review-verification-lens.agent.md   # Phase 4b, 3 per finding
    └── review-completeness-critic.agent.md # Phase 4c
```

21 agents, 2 prompt files, 4 skills. Each worker's phase spec and output template live in its agent definition, not in the workflow references, so the orchestrators read only the role they need.

Only the two orchestrators are `user-invocable`. The other 19 agents stay out of the agents dropdown and declare `agents: []`, so none of them can spawn further subagents.

## Pipeline: `/xray-team-analyze`

| Stage | Agent | Output |
|---|---|---|
| Phase 0 | `xray-orchestrator` | partition detection + checkpoint |
| Phase 1 Wave 1 | `xray-structure-worker` per partition | `01-structure.md`, `02-interfaces.md` |
| Phase 1 Wave 2 | `xray-behavior-worker` + `xray-quality-worker` per partition | `03-flows.md`, `04-semantics.md`, `05-risks.md`, `06-documentation.md` |
| Phase 2 | `xray-synthesizer` | consolidated `01..07.md` |
| Phase 3 | `xray-interconnect-mapper` | `08-interconnect-map.md` |
| Phase 4 | `xray-orchestrator` | publish, action plan, next steps |

Wave 2 starts only once every partition has both Wave 1 files on disk.

```
/xray-team-analyze .                      # auto-detect partitions, full depth
/xray-team-analyze src/                   # scope to a subtree
/xray-team-analyze . --depth=lite         # skip flows, semantics, doc health
/xray-team-analyze . --critical           # prioritize auth, payment, persistence
/xray-team-analyze . --comments           # include the comment quality audit
/xray-team-analyze . --docs-only          # documentation health only
/xray-team-analyze . --skip-interconnect  # stop after synthesis
/xray-team-analyze . --skip-synthesis     # per-partition reports only
/xray-team-analyze . --partition packages/api --partition packages/web --yes
/xray-team-analyze apps/backend --run-name backend
```

Small single-package repos are handled by the single-partition fallback, which produces one partition named `root`; the pipeline shape does not change. `--phase N` is rejected: phases are split across waves and workers, so starting mid-pipeline is not coherent.

Output lands in `.deep-dive/runs/<run-id>/` and is published to the `.deep-dive/` root on success:

```
.deep-dive/
├── runs.json                    # registry: active runs + latest completed
├── runs/<run-id>/               # isolated per-run output
│   └── partitions/<name>/       # per-partition worker output
└── 01-structure.md .. 08-interconnect-map.md   # published mirror of the latest run
```

Concurrent runs are safe: a run writes only inside its own directory until the publish step.

## Pipeline: `/team-review`

| Phase | Agent | Output |
|---|---|---|
| 0 | `review-orchestrator` | target resolution, `00-scope.md` |
| 0b | `review-orchestrator` | dimension detection + plan shown to the user |
| 1 | X-ray pipeline at `--depth=lite` | context + `02-interconnect.md` |
| 2 | up to 11 reviewers in parallel | `findings-<dimension>.md` each |
| 3 | `review-orchestrator` | dedup, severity calibration, `99-consolidated.md` |
| 4b | `review-verification-lens` x3 per finding | `98-verification.md` |
| 4c | `review-completeness-critic` | `97-coverage-gaps.md` |
| 5 | `review-orchestrator` | report |

Four dimensions always run (security, architecture, logic integrity, codebase hygiene). The rest activate on signals in the changed files: UI races, React performance, general performance, platform compliance, distributed flows, circular dependencies, API contracts, testing quality, data migrations, abstraction.

```
/team-review main...HEAD                  # review the branch diff, auto-detect dimensions
/team-review #123                         # review a pull request
/team-review src/auth/ --all              # force every dimension on a directory
/team-review main...HEAD --deep           # full-depth X-ray context instead of lite
/team-review main...HEAD --fast           # skip the verification panel and the critic
/team-review main...HEAD --rigorous       # verify every finding above the confidence floor
/team-review src/api --reviewers security,api-contracts
/team-review src/utils/dates.ts --skip-interconnect   # quick scan, no context pass
```

Session output lands in `.team-review/` and stays there after the report. Nothing in this pipeline edits source code.

Two gates keep the findings honest. The **verification panel** judges each finding with three independent lenses (reachability, refutation, severity calibration) and needs 2 of the first 2 to vote REAL for a finding to survive; a tie keeps it alive, tagged `contested`. The **completeness critic** then asks what the review never examined, and may trigger exactly one bounded follow-up round.

## Differences from the Claude Code plugins

### Both pipelines

| Area | Claude Code | This port |
|---|---|---|
| Command surface | Plugin commands | `.github/prompts/*.prompt.md` bound to a custom agent via `agent:` |
| Orchestration | The command body runs on the main agent | A dedicated orchestrator agent per pipeline, required because VS Code gates subagent dispatch behind an `agents:` allowlist |
| Script paths | `${CLAUDE_PLUGIN_ROOT}` expansion | Resolved once per session by probing `.github/skills/`, `.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` |
| Barriers | `TaskList` polling on task status | File existence on disk, verified with `#search/fileSearch` |
| Ownership enforcement | Prompt instructions only | Prompt instructions, plus a per-agent `tools` allowlist, plus the optional `PreToolUse` guard confining writes to the session directory |
| Secret protection | Prompt instructions only | Prompt instructions plus the optional `PreToolUse` guard |
| Worker visibility | Agents are addressable by name | Workers are `user-invocable: false`; only the two orchestrators are selectable |
| Team infrastructure | Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and the upstream `agent-teams` plugin | Native `#agent/runSubagent`, no flag, no external plugin |

### `/xray-team-analyze`

| Area | Claude Code | This port |
|---|---|---|
| Entry points | `/codebase-xray:analyze` and `/codebase-xray:team-analyze` | One prompt file. The classic single-context path was dropped; the single-partition fallback covers it. |
| `--phase N` | Supported by the classic command | Rejected with an explicit error |
| Phase specs | Duplicated between command bodies and agent definitions | Live only in the agent definitions; the workflow reference points at them |
| Worker scoping | Separate code paths for single-target and partitioned modes | One set of workers parametrized by `output_dir` |
| Interconnect map | `senior-review:semantic-interconnect-mapper`, a separate plugin | Vendored as `xray-interconnect-mapper`, wired into Phase 3 |
| Reviewer hints | Named the `senior-review` reviewer agents | Rewritten as generic review-concern hints |
| Downstream handoff | Next-steps menu routes into `project-setup` and `codebase-mapper` | Generic guidance; those plugins have no VS Code equivalent |

### `/team-review`

| Area | Claude Code | This port |
|---|---|---|
| Context building | Phase 1a invokes the `codebase-xray:analyze` skill, Phase 1b spawns `semantic-interconnect-mapper` separately | One X-ray run at `--depth=lite`. The ported X-ray pipeline already emits `08-interconnect-map.md` as its own Phase 3, so the two phases collapse into one and the mapper is not run twice. |
| Interconnect map source | Written directly to `.team-review/02-interconnect.md` | Copied there from the X-ray **run directory**, not the `.deep-dive/` root mirror, which a concurrent X-ray run can republish mid-review |
| Dimension detection | A block of `grep`, `sed`, and `awk` piped in bash | Expressed on `#search/textSearch` and `#search/fileSearch`, so it behaves the same on Windows without a POSIX layer |
| API contracts dimension | Generic `agent-teams:team-reviewer` | The specialized `review-api-contract-auditor`, which the upstream plugin ships but the upstream command never wired in |
| Dead code dimension | The Phase 2 table says `general-purpose`, the Phase 0b table says `cleanup-auditor` | Resolved to `review-cleanup-auditor`. The upstream tables contradict each other; the specialized agent is clearly the intent. |
| Testing / migrations / performance | Generic `agent-teams:team-reviewer` | `review-generic-reviewer`, which carries an explicit checklist per dimension instead of a bare dimension name |
| Verification lens models | Lens 3 pinned to a cheaper model | Unpinned. VS Code accepts `model:`, but the correct id depends on which Copilot models the user has; pin it yourself on `review-verification-lens` if it pays off. |
| Cleanup fix command | Findings end with `Fix: /senior-review:cleanup-dead-code --phase=<phase>` | `Fix phase: <phase>`. The automated removal command is not part of this bundle; the auditor stays report-only. |
| Team teardown | `shutdown_request` to every reviewer, then implicit cleanup | Nothing to tear down; subagents end when they return |

The `.deep-dive/` layout, run registry, phase numbering, output file names, and `##` section anchors are unchanged, so anything that already consumes the Claude Code plugins' output reads this port's output without modification.

## Standards

The skills follow the [Agent Skills specification](https://agentskills.io/specification), which VS Code implements. The prompt files and custom agents are VS Code specific. Validate a skill with:

```bash
skills-ref validate .github/skills/codebase-xray
```

Because VS Code also reads `.claude/skills/` and `.agents/skills/`, the skill directories can be relocated to either path without edits. Only the hook command path in the agent files hardcodes `.github/skills/`.

## License

MIT. Derived from the `codebase-xray`, `senior-review`, `react-development`, `platform-engineering`, and `abstraction-architect` plugins in [acaprino/claude-code-daodan](https://github.com/acaprino/claude-code-daodan).
