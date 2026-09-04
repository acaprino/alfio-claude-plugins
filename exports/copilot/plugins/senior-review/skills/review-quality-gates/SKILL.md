---
name: review-quality-gates
description: >
  Verification panel, completeness critic, pipeline conventions, and the
  shared-context provenance rule.
  TRIGGER WHEN: running /senior-review:team-review quality gates; running
  /senior-review:code-review Steps 4b and 4c; consolidating or deduplicating
  findings from multiple parallel reviewers.
  DO NOT TRIGGER WHEN: single-reviewer style review with no consolidation phase,
  or generic team coordination (the host harness covers that).
---

# Review Quality Gates

Gates and consolidation rules shared by /senior-review:team-review and /senior-review:code-review.

## Shared-Context Provenance Rule

> **Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.**

This is the pipeline's first-level invariant, not quality advice. Three consequences bind every gate below:

1. A reviewer that consumed a claim from the X-ray output or the interconnect map has not verified that claim. It must re-derive the claim independently before standing a finding on it.
2. Concordance between reviewers who share a premise is an **echo**. It raises no confidence and no severity. Consolidation reports it as such.
3. No metric may reward agreement with a shared artifact. Utilization of the map is an operational number, never a quality signal.

The same rule applied across model families instead of across reviewers is implemented by the `peer-review` plugin (`/peer-review:review`), which sends a plan or spec to a challenger on a different model family and runs an evidence-backed multi-round deliberation over it. There the shared artifact is the challenge packet: facts supplied to the challenger are tagged `GIVEN`, repeating one back never counts as corroboration, and a participant that reaches the authoritative source itself records the promotion `GIVEN -> DERIVED`. That plugin bounds the claim further than this section does, because two frontier models still share a corpus: what earns the second opinion its cost is decorrelated errors, not clean-room independence.

## Context Sharing Pattern

When `/team-review` runs in pipeline mode (no `--no-context`), reviewers do not receive raw code only. They receive three context artifacts produced in Phase 1:

1. **X-ray output** (from `codebase-xray` plugin) at the path the orchestrating command recorded: `$XRAY_RUN_DIR` when that command started the X-ray run itself (`/team-review` Phase 1a), or the `.codebase-xray/` mirror when it is consuming an analysis that already existed (`/code-review` Step 2). A command that started a run never reads the mirror: the mirror means "latest published run", not "the run I just produced". Files: `01-structure.md`, `02-interfaces.md`, `05-risks.md`, and optionally `03-flows.md`, `04-semantics.md`, `06-documentation.md`, `07-final-report.md`.
2. **Interconnect map** at `.team-review/02-interconnect.md` (from `codebase-xray:semantic-interconnect-mapper`): contracts (formal / structural / implicit), invariants, domain rules, assumptions (verified / documented / unverified), integration hot-spots, change impact radius.
3. **Knowledge provenance** at `.team-review/01-knowledge-provenance.md` (from `/team-review` Phase 1d): which concepts each discovery branch found, which neither found, and which they disagree about. Reviewers derive candidate concerns from it, so it is distributed with the other two.

A fourth artifact is produced alongside them and is **not** shared context: `.team-review/01b-independent-claims.md`, derived in Phase 1c by `senior-review:premise-auditor` while blind to both of the above. Phase 1d joins it with X-ray's leads into `01-knowledge-provenance.md`, and every contradiction becomes a `disputed` row in the map.

### Why context sharing matters, and where it stops

Phase 1 surfaces concerns that are invisible from local inspection: broken implicit contracts, invariant drift, bypass paths, non-idempotent retries, terminal state mutations. Reviewers use the map as a **checklist of things to hunt**, which is where its value is.

The economy argument applies to re-reading the whole codebase. It never applies to re-deriving a premise a finding stands on. Controlled redundancy on load-bearing premises is deliberate: it is the only thing that makes agreement between reviewers mean anything. A pipeline that spends tokens re-verifying one premise and saves them everywhere else is spending them correctly.

### How reviewers should consume the context

Reviewers should **not** read the entire context file. They should Grep or read only the anchors relevant to their dimension, guided by the `## Reviewer Hints` section at the bottom of `.team-review/02-interconnect.md`.

Default anchor routing:

| Reviewer dimension | Primary anchors in interconnect map |
|--------------------|-------------------------------------|
| security | `## Integration Hot-Spots` (inbound), `## Assumptions` (unverified), `## Contracts` (implicit, input validation) |
| architecture (code-auditor) | `## Invariants`, `## Contracts` (structural + implicit), `## Call Graph` |
| logic-integrity | `## Contracts` (implicit, unverified), `## Invariants`, `## Assumptions` (unverified), `## Domain Rules` |
| distributed-flows | `## Integration Hot-Spots` (HTTP / queue / IPC), `## Call Graph` (cross-service) |
| chicken-egg | `## Assumptions` (initialization order), `## Integration Hot-Spots` (Env / config), `## Invariants` (cross-component) |
| ui-races | `## Invariants` (temporal), `## Integration Hot-Spots` (UI state) |
| temporal-resilience | `## Invariants` (temporal, liveness), `## Assumptions` (unverified, timing/retry), `## Integration Hot-Spots` (queues, timers, network loops) |
| data-integrity | `## Invariants` (uniqueness, state exclusivity, balances), `## Contracts` (structural, persistence shapes), `## Assumptions` (unverified, isolation/consistency) |
| resource-lifecycle | `## Assumptions` (pool bounds, connection reuse), `## Integration Hot-Spots` (connections, subprocesses, long-lived handles) |
| api-contracts | `## Contracts` (formal). This is the only dimension whose primary anchor is the formal-contract section, which is why it resolves to `senior-review:api-contract-auditor` and not to a generic reviewer |
| structural entropy (diff mode) | none. This reviewer does not consume the interconnect map: it reads `$XRAY_RUN_DIR/01-structure.md` + `02-interfaces.md`, plus its own concept index when one exists, and hunts existing representations of the same concept across the codebase with Grep. Omit the anchors block from its prompt; `/team-review` passes it a named-inputs addendum instead |

### Prompt template for context-aware reviewers

```
You are reviewing for the {dimension} dimension.

## Target
[...]

## Diff
[...]

## Context files
- X-ray output: $XRAY_RUN_DIR
- Interconnect map: .team-review/02-interconnect.md
- Knowledge provenance: .team-review/01-knowledge-provenance.md

### Epistemic status of the shared context

The shared context is NOT ground truth. It is an index of hypotheses produced by
one upstream observer.

- Claims marked `verified` may be reused directly.
- Claims marked `documented`, `unverified` or `disputed` are hypotheses. You MUST
  independently re-derive any such claim before using it as the premise of a finding.
- Actively search for code paths, tests or documents that contradict the context.
  Finding one is a result, not a failure.
- Silence in the context is not evidence of absence. A concern the map does not
  mention may still be real; look anyway.

Per `## Reviewer Hints` in the interconnect map, focus your reading on these anchors:
{anchors-for-this-dimension}

## Instructions
Follow your agent definition's phases and output format. Cite file:line for every finding.
Every finding that relates to a contract/invariant/assumption in the interconnect map should
also cite the map anchor that surfaced the concern.

Write your output to .team-review/findings-{dimension}.md.
```

**Path substitution.** This template is `/team-review`'s: the X-ray line resolves to `$XRAY_RUN_DIR`, the immutable directory of the run Phase 1a started. A command that started a run never reads the mirror, per the X-ray Concurrent Runs Model: the mirror means "latest published run", not "the run I just produced". `/code-review` does not use this template; it builds its own X-Ray Context Template and reads the `.codebase-xray/` mirror there, because it consumes an analysis it did not produce.

### Metrics

**Map utilization rate** (operational, not a quality signal): the fraction of findings citing an interconnect anchor. It says how much of the map was consumed. It says nothing about whether the review was good, and a high value on a wrong map is the signature of the failure this pipeline is built to avoid. Do not set a target for it.

Quality signals:

| Metric | Meaning |
|---|---|
| **Independent premise reconstruction rate** | fraction of findings whose load-bearing premise was obtained **without exposure to that premise**: derived by the Premise Auditor in Phase 1c, or genuinely re-derived by a reviewer. **Lens 0 does not count.** Mode 2 receives the finding, the declared premise, the map and the X-ray output, so it is deliberately primed. It falsifies well and derives nothing independently, and counting it here would let dependent observation masquerade as independent corroboration inside the very metrics built to stop that |
| **Premise challenge rate** | fraction of eligible premises actually attacked by Lens 0. Eligible means provenance `shared-context` or `mixed`, or a premise carrying a universal or negative quantifier at any provenance |
| **Map challenge rate** | fraction of consumed map rows explicitly tested rather than assumed |
| **Map gap rate** | rules, paths and invariants discovered independently that the map never carried, meaning `[MAP-GAP]` findings over total findings |
| **Cross-source corroboration rate** | findings corroborated across code, tests and documentation |

Cross-source corroboration is a diagnostic over findings for which multiple semantically relevant sources exist. It is not a number to maximize. Many findings are provable entirely from code, and a low rate on those is correct.

### Fallback: raw mode (`--no-context`)

When the pipeline is skipped, reviewers receive only target + diff. In this mode:
- `logic-integrity-auditor` is not spawned (no map to drive it).
- `premise-auditor` is not dispatched either, in either mode: there is no shared derivation for it to be independent of.
- Phase 0c does not run. The flag means "give me the raw mode", and a normally-on phase does not override it: `01a-review-knowledge-leads.md` distributed to N reviewers is itself shared context, so keeping the phase alive under the flag would make findings legitimately `shared-context`, let Lens 0 fire, and stop the mode reproducing the pre-pipeline behaviour it exists to provide.
- Every finding is `independent` by construction, so Lens 0 never fires and consolidation never reports an echo. The quantifier route in `### The four lenses` cannot rescue this: with no `premise-auditor` dispatched there is no Lens 0 to route to. Raw mode trades the premise gate away along with the shared context, which is what the flag is for.
- All other reviewers fall back to their pre-pipeline behavior.
- No `.codebase-xray/`, `$XRAY_RUN_DIR` or `.team-review/02-interconnect.md` references should appear in reviewer prompts.

## Reviewer Pipeline Conventions

Every reviewer agent that runs as part of `/team-review` Phase 2 carries a `## Pipeline Conventions` section in its system prompt with four cross-cutting rules. The orchestrator does not need to repeat them in the spawn prompt, but should be aware of what they mandate:

- **Scope budget**: each reviewer stops after ~15 file reads without a finding and returns a "scope-off-topic" report. The orchestrator should plan targets at a granularity that respects this budget.
- **No-findings protocol**: reviewers may legitimately return "examined X, Y, Z: no issues" instead of inventing findings. Treat such reports as valid Phase 3 input, not failure.
- **Cross-Reviewer Notes**: reviewers append observations that belong to other dimensions in a `## Cross-Reviewer Notes` section. Phase 3 consolidation must scan for this section and route the observations to the appropriate reviewer (or surface them in the consolidated report under the recipient dimension).
- **Interconnect anchor citation**: reviewers cite map anchors when applicable. This is the same signal the map utilization rate measures: an operational number, not a quality signal. See `### Metrics` for the quality signals that actually matter.

Background: the rationale for these conventions lives in `docs/references/agent-teams-best-practices.md` § Pipeline Conventions in the development repository. That file is not shipped with the installed plugin and is never needed at runtime: the four rules above are the complete, self-contained contract.

## Evidence Classes for Quantitative Claims

Any finding that quantifies damage (N times/day, GB transferred, $/month, requests/second) must label the number with one of two classes:

- **`measured`**: obtained by running a harness, simulation, or reproduction, or read from real logs/metrics. The finding states the method in one line (e.g., "24h simulated clock, 3 concordant runs"). Any harness is built outside the work tree and deleted afterwards; the Delivery Gate below checks for leftovers.
- **`derived`**: computed by reading the code. Permitted, but it is a hypothesis, not a fact: code-derived damage estimates have been wrong by two orders of magnitude in both directions (a "288 downloads/day" claim measured out at 2; a "bounded, negligible" claim can hide the real defect).

Consequences, enforced at consolidation and verification:

1. A `derived` number alone cannot justify **Critical** severity. Either measure it (simulated clocks make a 24-hour scenario cost seconds) or cap the finding at High and name the measurement as the follow-up.
2. A finding cannot be **closed as acceptable** ("bounded", "self-limiting", "low traffic") on a `derived` number alone -- and not even a `measured` one settles it by itself: closing also requires answering the user-visible-consequence question below. Correct arithmetic about the wrong question is how real defects get archived.
3. The verification panel treats unlabeled quantitative claims as `derived`. Lens 2 (refutation) should actively check whether a claimed rate or cost survives contact with the code's actual control flow (deduplication, caps, phase transitions the estimate ignored).

### The user-visible-consequence question

Every finding whose damage is behavioral over time (repetition, degradation, silence) must state **what the user or operator sees, and when**. "None (silent)" is a severity escalator, never a mitigation: the absence of a signal over active damage is typically the more severe finding hiding behind a byte count. Reviewers whose dimension thinks in resource terms (performance, cost) must answer this question before archiving anything as within budget.

## Adversarial Verification Panel

After findings are consolidated (deduplicated), each selected finding is judged by a **panel of up to 4 verifiers**, each with a distinct lens. This replaces single-judge validation: independent mandates catch more failure modes than identical refuters.

This section is the source of truth. `/senior-review:team-review` (Phase 4b) and `/senior-review:code-review` (Step 4b) both drive the panel from here.

### The four lenses

Spawn one `Agent` per lens per finding. Use `subagent_type: general-purpose` for lenses 1-3 and `subagent_type: senior-review:premise-auditor` for lens 0. Omit `model` for lenses 0, 1 and 2 so they inherit the session model (reasoning-heavy), `model: sonnet` for lens 3 (calibration).

**Lens 3 is gated.** Lenses 1 and 2 run first, in parallel across findings (`run_in_background: true`). Lens 3 (severity calibration) is spawned only for findings that survive them (REAL from both, or the tie that marks them `contested`). Calibrating the severity of a finding the panel is about to discard is spend for nothing; the gate cuts roughly a third of the verifier calls with no change to the survival semantics. Findings killed by lenses 1-2 never reach lens 3 and keep their original severity in the `filtered` record.

The panel has four lenses. **Lens 0 is gated on provenance and runs first**, before lenses 1 and 2, for the same reason lens 3 is gated last: a finding a veto will discard should not consume the other lenses. Lens 3 stays gated on survival.

Lens 0 runs for findings whose `premise_provenance` is `shared-context` or `mixed`, **and, regardless of provenance, for any finding whose declared premise carries a universal or negative quantifier** (`no`, `never`, `cannot`, `always`, `only`). A finding declared `independent` with no such quantifier skips it. A finding that declares nothing is treated as `shared-context` when the pipeline ran, and the report records the reviewer as format-non-compliant. A finding with no `Load-bearing premise` has one derived by Lens 0, with the same note. The pipeline never drops a finding over a missing field.

The quantifier route exists because sharing is how an over-scoped premise *spreads*, not how it is *born*. The incident this pipeline was built from was a true local observation ("no credential-bearing response path exists") generalized to all paths by a reviewer that had read only one of them. Declared honestly as `independent`, it would pass a provenance-only gate untouched. A universal claim is exactly the claim one counterexample kills, which is the thing Lens 0 is good at.

**Lens 0 prompt (Premise Challenge):** spawn with `subagent_type: senior-review:premise-auditor`, mode 2, inheriting the session model.

```
Mode 2: adversarial premise challenge.

## The Finding
[severity, file:line, description, suggested fix]

## The declared load-bearing premise
[the finding's Load-bearing premise field verbatim, or "none declared"]

## Context available
- Interconnect map: .team-review/02-interconnect.md
- Knowledge provenance: .team-review/01-knowledge-provenance.md
- X-ray: $XRAY_RUN_DIR

## Instructions
Follow mode 2 of your agent definition. Attack the premise, not the finding.
Return REFUTED only with a file:line counterexample; without one, return UNCERTAIN.
Decide and state whether the counterexample falsifies the PREMISE itself or only
a piece of shared SUPPORT.
```

**Path substitution differs by command.** In `/team-review` the X-ray line resolves to `$XRAY_RUN_DIR`, the immutable directory of the run that command started. In `/code-review` it resolves to the `.codebase-xray/` mirror, because that command consumes a pre-existing analysis it did not produce. The interconnect map and knowledge provenance lines exist only in the `/team-review` path; in `/code-review` they are omitted, and a finding there is `independent` unless the X-ray context supplied its premise.

**Lens 1 prompt (Reachability / Correctness):**

```
You are verifier LENS 1 of 4 (Reachability / Correctness) for one code-review finding.
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
You are verifier LENS 2 of 4 (False-Positive Causes) for one code-review finding.
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
You are verifier LENS 3 of 4 (Severity Calibration) for one code-review finding.
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

Lens 0 does not use this schema. Per its agent definition it returns `premise_verdict` (`HOLDS`, `REFUTED`, or `UNCERTAIN`), `refutation_target` (`PREMISE` or `SUPPORT`, present only when `REFUTED`), `counterexample` (a `file:line`, required when `REFUTED`), and `premise_form` (`compliant` or `non-compliant`).

### Lens 0 resolution

Refutation type is resolved first, provenance second. Provenance decides only what can survive after a source is invalidated.

| Lens 0 result | Effect |
|---|---|
| `REFUTED`, target `PREMISE` | Finding discarded, counted `filtered: premise-refuted`. Regardless of provenance, and regardless of lenses 1-2, which are not spawned. |
| `REFUTED`, target `SUPPORT`, provenance `mixed` | Strike the shared leg. Restate the finding from the surviving independent evidence and run lenses 1-2 on the reduced finding. |
| `REFUTED`, target `SUPPORT`, provenance `shared-context` | Nothing survives the strike. Discarded, counted `filtered: premise-refuted`. |
| `UNCERTAIN` | Finding proceeds to lenses 1-2, tagged `premise-contested`. |
| `HOLDS` | Finding proceeds to lenses 1-2 unchanged. |

Local correctness cannot outvote a refuted premise. A verifier can be entirely right that the code at the cited line does what the finding says, while the inference from that fact to the finding's conclusion is dead because another path exists. That is why Lens 0 is a veto and not a fourth vote.

A `premise_form: non-compliant` return is recorded in the verification file and reported, whatever the verdict. It means a reviewer declared a paraphrase instead of a premise, and it is a defect in the review, not in the code.

### Survival rule

- Lens 0 is evaluated **before** the rule below. A finding discarded by Lens 0 never reaches lenses 1-2. A finding whose Lens 0 returned `UNCERTAIN` or `HOLDS` is judged by the rule below exactly as before.
- A finding **survives** if **at least 2 of lenses 1-2 vote REAL**.
- If **>= 2 of lenses 1-2 vote FALSE_POSITIVE**, the finding is **discarded** and counted as `filtered` (never silently dropped: the count appears in the report).
- **Tie or inconclusive** (1 REAL / 1 FALSE on lenses 1-2, or fewer than 2 valid verdicts returned) means the finding **survives, marked `contested`**. A flagged false positive is cheaper than a killed real bug.
- **Final severity** = lens-3 `severity_vote` when the finding is confirmed real; otherwise the original reviewer severity.

### Fail-open

If a verifier errors or returns a malformed verdict, treat it as an abstention. If fewer than 2 valid verdicts return for a finding, apply the tie rule (survives, `contested`). A surviving finding whose lens 3 errored keeps the original reviewer severity. The panel never crashes the pipeline and never silently drops a finding.

A Lens 0 that errors, returns malformed output, or returns `REFUTED` without a `file:line` counterexample is treated as `UNCERTAIN`. Lens 0 never kills a finding by failing.

### Selection: what enters the panel

- **Normal (default-on):** every finding with confidence `>= 50%` that survived deduplication, regardless of severity.
- **Under cost guard** (more than 25 surviving findings AND `--rigorous` not set): narrow to **stakes + uncertainty band**, which is all Critical/High findings plus any Medium/Low in the 50-75% confidence band or with a severity that conflicted between reviewers. The remaining findings pass through unverified, tagged `unverified (cost-guard)`. **Declare the narrowing in the report.**
- **`--rigorous`:** ignore the cap; verify everything above the floor.
- **`--fast`:** skip the entire gate (panel + critic).

### Cost guard is a finding-count proxy

In the prose/Agent substrate there is no token-budget API. The guard triggers on the **number of surviving findings (threshold 25)**, not on real token consumption. State this wherever the guard is documented so no false precision is implied.

## Completeness Critic

After verification, one critic agent asks what the review failed to cover. It turns blind spots from passive side effects into active output and, when warranted, into one more round of work.

This section is the source of truth. `/senior-review:team-review` (Phase 4c) and `/senior-review:code-review` (Step 4c) both drive the critic from here.

### Inputs

The critic reads: the verified findings, the review scope, the list of dimensions that ran, and whatever context exists (X-ray output and the interconnect map for team-review; `.codebase-xray/` if present for code-review).

### Gap taxonomy

The critic evaluates coverage against a fixed taxonomy and writes a `## Coverage Gaps` block:

1. **Dimensions not run** that the scope warranted (e.g. security skipped on auth code; no distributed-flows despite messaging signals; no temporal-resilience despite timers/retry/scheduler code in the diff).
2. **Files in scope cited by no reviewer** (cross-check the changed-file list against files referenced in findings).
3. **Unverified assumptions** in the interconnect map that no finding addressed.
4. **High-risk hot-spots** (from X-ray `05-risks.md` or the map's Integration Hot-Spots) with zero findings.
5. **Findings closed on metrics alone**: any finding archived as acceptable ("bounded", "low traffic", "within budget") that does not state the user-visible consequence, or whose quantitative basis is `derived` and unmeasured (see `## Evidence Classes`). These are re-opened as gaps, not silently accepted.

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
[X-ray paths and interconnect map path, or "none"]

## Instructions
Produce a "## Coverage Gaps" list across these categories, each item actionable and specific:
1. Dimensions warranted by the scope but not run
2. In-scope files cited by no finding
3. Interconnect-map assumptions marked unverified that no finding addressed
4. High-risk hot-spots (05-risks.md / Integration Hot-Spots) with zero findings
5. Findings closed as acceptable on a metric alone: for each, ask "what does the
   user see when this happens?" -- if the answer is missing or is "nothing, silently",
   re-open it as a gap; also flag any quantitative closure whose number is derived
   from reading the code rather than measured

Then, if and ONLY if one gap is a high-risk uncovered area, name the single most valuable
follow-up: which dimension/agent should review which files. Output it under
"## Recommended follow-up" with one entry, or "## Recommended follow-up: none".
```

### Bounded follow-up round

If the critic names a high-risk uncovered area, spawn **one** targeted reviewer (the most specialized agent for that area) for a **single** round. Its findings re-enter deduplication and then the verification panel. One round only: the critic does not run again on the follow-up output.

### Degradation

Under the cost guard or budget pressure, the critic degrades to **report-only**: it emits the `## Coverage Gaps` list with no follow-up spawn, and the report states that the follow-up was skipped. `--fast` skips the critic entirely.

## Delivery Gate

Value that never gets delivered, and debris that gets left behind, both degrade a review as surely as a missed bug. Two mechanical checks, driven by the orchestrator, close the loop:

### Every reviewer delivers or declares

Consolidation (team-review Phase 3 / code-review Step 4) does not start until every spawned reviewer has produced one of exactly two artifacts: its findings file, or an explicit no-findings report ("examined X, Y, Z -- no issues"). Neither silence nor an idle agent counts as either one.

- A reviewer idle past a reasonable deadline gets **one** direct nudge (`SendMessage` in team mode; reading the task output in background-agent mode).
- If it stays silent, the orchestrator salvages whatever task output exists, saves it to the findings path marked `[undelivered -- collected by orchestrator]`, and the final report lists the dimension as **degraded**, never as clean.
- A dimension with no artifact at all is reported as **not delivered**: the review has a known blind spot and says so. This is the only way a matched dimension can go missing, since every reviewer this pipeline spawns comes from a hard dependency and is always installed.

### The work tree is left as found

The pre-review `git status --porcelain` snapshot (recorded at scope time) is diffed against the post-review state before the report is finalized. Anything created by the review outside its session directory (`.team-review/` or the command's equivalent) -- probe scripts, measurement harnesses, scratch fixtures -- is removed, and the removal is noted in the report. Measurement evidence belongs in the finding (numbers, method, `measured` label), never as a file in the repository. This is the enforcement arm of the `measured` evidence class above: measure freely, keep the numbers, leave no trace.
