---
description: Audit a codebase for missed unification opportunities and wrong abstractions. Auto-launches /deep-dive-analysis:deep-dive-analysis when .deep-dive/ is missing or incomplete. Report-only.
argument-hint: "[path] [--scope <subpath>] [--severity-floor low|medium|high] [--focus unification|wrong-abstraction|both]"
---

# /abstraction-architect:audit

Audit a codebase for the two failure modes of pure architecture: missed unification (cross-cutting concerns scattered across call sites that should be a single layer) and wrong abstractions (god services, flag-soup functions, premature interfaces, leaky abstractions). Report-only.

## Usage

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --severity-floor high              # only high-severity findings
/abstraction-architect:audit --focus wrong-abstraction          # restrict to one category
/abstraction-architect:audit --scope src/api --focus unification
```

## Arguments

- `[path]` (optional) — codebase root. Default: current working directory.
- `--scope <subpath>` (optional) — limit findings to a subtree. Deep-dive is still run on the full codebase; the agent filters findings by scope.
- `--severity-floor low|medium|high` (optional) — drop findings below this severity. Default: `medium`.
- `--focus unification|wrong-abstraction|both` (optional) — restrict to one finding category. Default: `both`.

## What this command does

1. **Resolves the target path.** Defaults to the current working directory if `[path]` is omitted.

2. **Checks for `.deep-dive/`.** Looks for the required files: `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`. The optional `08-interconnect-map.md` is also checked; if absent the audit proceeds without bounded-context fusion analysis.

3. **Auto-launches deep-dive if needed.** If `.deep-dive/` is missing or incomplete, prints the status message *"No deep-dive output found at `.deep-dive/`. Launching `/deep-dive-analysis:deep-dive-analysis` first. This may take several minutes on a large codebase."* then invokes `/deep-dive-analysis:deep-dive-analysis` automatically without a confirmation prompt. If deep-dive fails, aborts with the path of the deep-dive log.

4. **Spawns the `abstraction-architect` agent** via the `Agent` tool, passing the codebase path, the deep-dive path, and the parsed scope / severity-floor / focus flags.

5. **The agent writes the report** to `<path>/.abstraction-architect/findings.md`.

6. **Prints to the user:**
   - The absolute path of the report.
   - Summary counts: total findings, high / medium / low breakdown.
   - The top three high-severity findings as one-line previews.

The full report stays in the file so the user opens it deliberately.

## Output location

`<path>/.abstraction-architect/findings.md`

The directory is created automatically if missing. Re-running the command overwrites the previous report.

## Prerequisites

- The `deep-dive-analysis` plugin must be installed (declared as a dependency in `marketplace.json`).
- For monorepos large enough to benefit from partitioned analysis, run `/agent-teams:team-deep-dive` first to produce `08-interconnect-map.md`; the auditor will then include bounded-context fusion findings.

## Related commands

- `/deep-dive-analysis:deep-dive-analysis` — produces the `.deep-dive/` input this command consumes. Auto-launched by this command when missing.
- `/agent-teams:team-deep-dive` — partitioned deep-dive for monorepos; adds `08-interconnect-map.md` to the output.
- `/senior-review:code-review` — orthogonal: general code-quality review. Use that for style and pattern consistency; use this for pure-architecture audits.
- `/clean-code:clean-code` — style and readability cleanup. Different concern.

## Out of scope

This command does not produce a refactoring plan. The `suggested direction` field in each finding names the target layer or refactoring move in one sentence. A future `/abstraction-architect:plan-refactor <finding-id>` command will turn a finding into a step-by-step plan.
