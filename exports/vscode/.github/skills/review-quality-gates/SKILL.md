---
name: review-quality-gates
description: >
  Quality gates for multi-reviewer code review pipelines: adversarial verification panel,
  completeness critic, reviewer pipeline conventions, and the context sharing pattern for parallel
  reviewers. Loaded by the /team-review orchestrator before consolidation, and by anyone
  deduplicating or severity-calibrating findings from multiple parallel reviewers.
user-invocable: false
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: senior-review
---

# Review Quality Gates

Gates and consolidation rules for the `/team-review` pipeline.

## Context Sharing Pattern

When `/team-review` runs in pipeline mode (no `--skip-interconnect`), reviewers do not receive raw code only. They receive two context artifacts produced in Phase 1:

1. **X-ray output** at `<xray_run_dir>/` (from the `codebase-xray` skill): `01-structure.md`, `02-interfaces.md`, `05-risks.md`, and at full depth also `03-flows.md`, `04-semantics.md`, `06-documentation.md`, `07-final-report.md`. Reviewers read the immutable run directory, never the `.deep-dive/` root mirror, which a concurrent X-ray run may republish mid-review.
2. **Interconnect map** at `.team-review/02-interconnect.md`, copied by Phase 1 from the X-ray run's `08-interconnect-map.md` (produced by `xray-interconnect-mapper`): contracts (formal / structural / implicit), invariants, domain rules, assumptions (verified / documented / unverified), integration hot-spots, change impact radius.

### Why context sharing matters

Without shared context, each reviewer re-reads the code from scratch. This is wasteful and, more importantly, blinds them to bugs that only manifest across components: broken implicit contracts, invariant drift, bypass paths, non-idempotent retries, terminal state mutations. Phase 1 surfaces those concerns in the interconnect map, and Phase 2 reviewers use the map as a checklist.

### How reviewers should consume the context

Reviewers should **not** read the entire context file. They should use `#search/textSearch` or read only the anchors relevant to their dimension, guided by the `## Review Focus Hints` section at the bottom of `.team-review/02-interconnect.md`.

Default anchor routing:

| Reviewer dimension | Primary anchors in interconnect map |
|--------------------|-------------------------------------|
| security | `## Integration Hot-Spots` (inbound), `## Assumptions` (unverified), `## Contracts` (implicit, input validation) |
| architecture (code-auditor) | `## Invariants`, `## Contracts` (structural + implicit), `## Call Graph` |
| logic-integrity | `## Contracts` (implicit, unverified), `## Invariants`, `## Assumptions` (unverified), `## Domain Rules` |
| distributed-flows | `## Integration Hot-Spots` (HTTP / queue / IPC), `## Call Graph` (cross-service) |
| chicken-egg | `## Assumptions` (initialization order), `## Integration Hot-Spots` (Env / config), `## Invariants` (cross-component) |
| ui-races | `## Invariants` (temporal), `## Integration Hot-Spots` (UI state) |
| api-contracts | `## Contracts` (formal) |
| abstraction (diff mode) | none. This reviewer does not consume the interconnect map: it reads the X-ray run's `01-structure.md` and `02-interfaces.md` and hunts prior art across the codebase with `#search/textSearch`. Omit the anchors block from its prompt; `/team-review` passes it a named-inputs addendum instead |

### Prompt template for context-aware reviewers

```
You are reviewing for the {dimension} dimension.

## Target
[...]

## Diff
[...]

## Context files
- X-ray output: <xray_run_dir>/
- Interconnect map: .team-review/02-interconnect.md

Per `## Review Focus Hints` in the interconnect map, focus your reading on these anchors:
{anchors-for-this-dimension}

## Instructions
Follow your agent definition's phases and output format. Cite file:line for every finding.
Every finding that relates to a contract/invariant/assumption in the interconnect map should
also cite the map anchor that surfaced the concern.

Write your output to .team-review/findings-{dimension}.md.
```

### Quality metric: context utilization rate

A useful quality signal at the end of a review: **what fraction of findings cite an interconnect-map anchor?**

- High (>= 30%): reviewers are leveraging the context effectively; the pipeline is paying off.
- Medium (10-30%): context used but inconsistently; consider refining prompts.
- Low (< 10%): either reviewers are ignoring the map or the map is too generic to be actionable.

The logic-integrity-auditor dimension should be at >= 70% (its findings are almost entirely driven by the map).

### Fallback: `--skip-interconnect` mode

When the pipeline is skipped, reviewers receive only target + diff. In this mode:
- `review-logic-integrity-auditor` is not spawned (no map to drive it).
- All other reviewers fall back to their pre-pipeline behavior.
- No X-ray run directory or `.team-review/02-interconnect.md` references should appear in reviewer prompts.

## Reviewer Pipeline Conventions

Every reviewer agent that runs as part of `/team-review` Phase 2 carries a `## Pipeline Conventions` section in its system prompt with four cross-cutting rules. The orchestrator does not need to repeat them in the spawn prompt, but should be aware of what they mandate:

- **Scope budget**: each reviewer stops after ~15 file reads without a finding and returns a "scope-off-topic" report. The orchestrator should plan targets at a granularity that respects this budget.
- **No-findings protocol**: reviewers may legitimately return "examined X, Y, Z: no issues" instead of inventing findings. Treat such reports as valid Phase 3 input, not failure.
- **Cross-Reviewer Notes**: reviewers append observations that belong to other dimensions in a `## Cross-Reviewer Notes` section. Phase 3 consolidation must scan for this section and route the observations to the appropriate reviewer (or surface them in the consolidated report under the recipient dimension).
- **Interconnect anchor citation**: reviewers cite map anchors when applicable. This is the same signal as the context utilization rate above; the section below quantifies the quality metric.

## Adversarial Verification Panel

After findings are consolidated (deduplicated), each selected finding is judged by a **panel of 3 verifiers run in parallel**, each with a distinct lens. This replaces single-judge validation: three independent mandates catch more failure modes than three identical refuters.

This section is the source of truth. `/team-review` Phase 4b drives the panel from here.

### The three lenses

Dispatch one `review-verification-lens` subagent per lens per finding with `#agent/runSubagent`, passing the lens number and prompt below. Issue all three (and the lenses across several findings) in a single assistant turn so they run concurrently.

All three lenses run on whatever model the session selected. The Claude Code original pinned a cheaper model on lens 3, since calibration is less reasoning-heavy than lenses 1 and 2. VS Code custom agents accept a `model:` field, so pin one on `review-verification-lens` if your setup benefits from it; the default is deliberately unpinned, because the correct model id depends on which Copilot models the user has available.

**Lens 1 prompt (Reachability / Correctness):**

```
You are verifier LENS 1 of 3 (Reachability / Correctness) for one code-review finding.
Your job: determine whether the described defect REALLY exists and is reachable.

## The Finding
[severity, file:line, description, suggested fix]

## The Diff
[diff for the relevant file]

## Full File Content
[full content of the file containing the finding]

## Instructions
1. Locate the exact file:line. Is the citation correct?
2. Trace the control/data flow: is the buggy path actually reachable in normal or error execution?
3. Does the code truly exhibit the described problem, or is the description a misread?
Return REAL only if you can point to the concrete lines and the path that triggers the defect.

Respond with EXACTLY:
- Verdict: REAL or FALSE_POSITIVE
- Confidence: 0-100
- Reason: 1-2 sentences citing file:line
```

**Lens 2 prompt (False-Positive Causes):**

```
You are verifier LENS 2 of 3 (False-Positive Causes) for one code-review finding.
Your job: actively try to REFUTE the finding. Default to FALSE_POSITIVE if uncertain.

## The Finding
[severity, file:line, description, suggested fix]

## The Diff
[diff for the relevant file]

## Full File Content
[full content of the file containing the finding]

## Instructions
Try to explain the flagged code away as one of:
1. Framework convention (Django/FastAPI/pytest/etc. idiom that is correct by design)
2. Intentional design choice consistent with surrounding code or CLAUDE.md
3. Pre-existing code not introduced or made newly relevant by the diff
4. A misunderstanding of the code's actual behavior or context
Return REAL only if the finding survives refutation on all four counts.

Respond with EXACTLY:
- Verdict: REAL or FALSE_POSITIVE
- Confidence: 0-100
- Reason: 1-2 sentences citing file:line; if FALSE_POSITIVE, name the refutation category
```

**Lens 3 prompt (Severity Calibration):**

```
You are verifier LENS 3 of 3 (Severity Calibration) for one code-review finding.
Assume the finding is REAL. Your only job is to vote the correct severity.

## The Finding
[severity, file:line, description, suggested fix]

## The Diff
[diff for the relevant file]

## Full File Content
[full content of the file containing the finding]

## Calibration criteria
- Critical: data loss, security breach, complete failure; certain or very likely
- High: significant functionality impact or degradation; likely
- Medium: partial impact, workaround exists; possible
- Low: minimal or cosmetic; unlikely

Respond with EXACTLY:
- Verdict: REAL
- Severity_vote: Critical or High or Medium or Low
- Confidence: 0-100
- Reason: 1-2 sentences citing file:line
```

### Verdict schema

Each verifier returns: `verdict` (REAL or FALSE_POSITIVE; lens 3 always REAL), `confidence` (0-100), `severity_vote` (lens 3 only), `reason` (with a file:line citation).

### Survival rule

- A finding **survives** if **at least 2 of lenses 1-2 vote REAL**.
- If **>= 2 of lenses 1-2 vote FALSE_POSITIVE**, the finding is **discarded** and counted as `filtered` (never silently dropped: the count appears in the report).
- **Tie or inconclusive** (1 REAL / 1 FALSE on lenses 1-2, or fewer than 2 valid verdicts returned) means the finding **survives, marked `contested`**. A flagged false positive is cheaper than a killed real bug.
- **Final severity** = lens-3 `severity_vote` when the finding is confirmed real; otherwise the original reviewer severity.

### Fail-open

If a verifier errors or returns a malformed verdict, treat it as an abstention. If fewer than 2 valid verdicts return for a finding, apply the tie rule (survives, `contested`). The panel never crashes the pipeline and never silently drops a finding.

### Selection: what enters the panel

- **Normal (default-on):** every finding with confidence `>= 50%` that survived deduplication, regardless of severity.
- **Under cost guard** (more than 25 surviving findings AND `--rigorous` not set): narrow to **stakes + uncertainty band**, which is all Critical/High findings plus any Medium/Low in the 50-75% confidence band or with a severity that conflicted between reviewers. The remaining findings pass through unverified, tagged `unverified (cost-guard)`. **Declare the narrowing in the report.**
- **`--rigorous`:** ignore the cap; verify everything above the floor.
- **`--fast`:** skip the entire gate (panel + critic).

### Cost guard is a finding-count proxy

There is no token-budget API available to a custom agent. The guard triggers on the **number of surviving findings (threshold 25)**, not on real token consumption. State this wherever the guard is documented so no false precision is implied.

## Completeness Critic

After verification, one critic agent asks what the review failed to cover. It turns blind spots from passive side effects into active output and, when warranted, into one more round of work.

This section is the source of truth. `/team-review` Phase 4c drives the critic from here, dispatching one `review-completeness-critic` subagent.

### Inputs

The critic reads: the verified findings, the review scope, the list of dimensions that ran, and whatever context exists (the X-ray run directory and the interconnect map, or "none" under `--skip-interconnect`).

### Gap taxonomy

The critic evaluates coverage against a fixed taxonomy and writes a `## Coverage Gaps` block:

1. **Dimensions not run** that the scope warranted (e.g. security skipped on auth code; no distributed-flows despite messaging signals).
2. **Files in scope cited by no reviewer** (cross-check the changed-file list against files referenced in findings).
3. **Unverified assumptions** in the interconnect map that no finding addressed.
4. **High-risk hot-spots** (from the X-ray run's `05-risks.md` or the map's Integration Hot-Spots) with zero findings.

### Critic prompt

```
You are the completeness critic for a multi-dimensional code review. Your job is NOT
to find new bugs directly. It is to find what the review did not examine.

## Verified findings
[the consolidated, verified findings]

## Scope
[changed files / target]

## Dimensions that ran
[list]

## Context available
[X-ray run directory and interconnect map path, or "none"]

## Instructions
Produce a "## Coverage Gaps" list across these categories, each item actionable and specific:
1. Dimensions warranted by the scope but not run
2. In-scope files cited by no finding
3. Interconnect-map assumptions marked unverified that no finding addressed
4. High-risk hot-spots (the X-ray run's 05-risks.md, or Integration Hot-Spots) with zero findings

Then, if and ONLY if one gap is a high-risk uncovered area, name the single most valuable
follow-up: which dimension/agent should review which files. Output it under
"## Recommended follow-up" with one entry, or "## Recommended follow-up: none".
```

### Bounded follow-up round

If the critic names a high-risk uncovered area, spawn **one** targeted reviewer (the most specialized agent for that area) for a **single** round. Its findings re-enter deduplication and then the verification panel. One round only: the critic does not run again on the follow-up output.

### Degradation

Under the cost guard or budget pressure, the critic degrades to **report-only**: it emits the `## Coverage Gaps` list with no follow-up spawn, and the report states that the follow-up was skipped. `--fast` skips the critic entirely.
