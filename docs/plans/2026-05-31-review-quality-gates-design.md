# Design: Adversarial Verification Gates for Review Pipelines

**Date:** 2026-05-31
**Status:** Approved (brainstorming) — pending spec review before implementation plan
**Scope:** `agent-teams` (team-review command + multi-reviewer-patterns skill), `senior-review` (code-review command)
**Author:** Alfio Caprino (with Claude)

## Problem

The marketplace's review pipelines fan out across dimensions but do almost no adversarial verification of the findings they produce, and never ask what they failed to cover.

Grounded audit of the current state:

- **`/agent-teams:team-review`** Phase 4 does dedup + severity calibration only. There is no verification of findings and no completeness check. A plausible-but-wrong finding survives to the report unchallenged.
- **`/senior-review:code-review`** already has a partial gate (`Step 4b: Validate Critical & High Findings`): it spawns **one** validator per Critical/High finding returning `VALID | FALSE_POSITIVE`. It does not cover Medium/Low, uses a single judge (no majority), and there is no completeness critic.
- Neither pipeline asks "what did we not examine?" at the end. Gaps are passive side effects, never actively interrogated.

This is the highest-quality / lowest-blast-radius lever among the multi-agent opportunities identified: it raises finding precision (kills false positives) and recall awareness (surfaces blind spots) without migrating the orchestration substrate.

## Goals

1. Add a **3-lens adversarial verification panel** that judges each finding by majority vote.
2. Add a **completeness critic** that reports coverage gaps and, when it finds a high-risk uncovered area, triggers one bounded follow-up reviewer round.
3. **Centralize** the verification + critic logic in the `multi-reviewer-patterns` skill so the two commands stay thin and never diverge, and so future consumers (domain audits, a later Workflow rewire) inherit it.
4. Make the gate **default-on with a cost guard and an opt-out**, so the power is the default rather than hidden behind a flag.

## Non-goals (YAGNI)

- No Workflow-tool substrate. The gate runs in the existing prose/Agent-tool model (the deferred "direction 2" rewire to Workflow is a separate initiative).
- No loop-until-dry discovery (explicitly rejected — unbounded cost).
- No new reviewer agents. The panel and critic reuse existing specialized agents.
- No changes to domain-plugin audit commands (the "direction 3" fan-out is a later initiative).
- No real token-budget metering. The cost guard is a finding-count proxy (see Cost Guard).

## Key decisions (locked during brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Surfaces | Both commands + centralize logic in `multi-reviewer-patterns` skill |
| 2 | Verification form | Perspective-diverse panel (3 distinct lenses), majority confirms |
| 3 | What to verify | Everything above confidence floor (>=50%) by default |
| 4 | Default posture | Default-on + cost-guard + `--fast` opt-out + `--rigorous` force-full |
| 5 | Completeness critic | Critic + one bounded targeted round; degrades to report-only under guard |
| 6 | Substrate | A — prose/Agent tool, consistent with existing pipelines |

## Architecture

### Source of truth: the `multi-reviewer-patterns` skill

Two new canonical sections are added to `plugins/agent-teams/skills/multi-reviewer-patterns/SKILL.md`, alongside the existing dedup / severity-calibration sections:

- **`## Adversarial Verification Panel`** — the 3 lenses, the verifier verdict schema, the survival rule, severity recalibration, the selection logic (what enters the panel), and the cost guard.
- **`## Completeness Critic`** — the gap taxonomy, the bounded-round rule, and the degradation behavior.

Both commands reference these sections (the way they already reference the skill's deduplication and severity rules) instead of inlining the logic. The commands become thin on the gate; all substance lives in the skill.

### Integration in `/agent-teams:team-review`

team-review has no verification today. Insert two phases between consolidation and report:

```
Phase 4  Consolidation (existing)        -> deduplicated findings
Phase 4b Adversarial Verification (NEW)  -> panel per finding, majority vote, verdicts
Phase 4c Completeness Critic (NEW)       -> gaps + optional 1 targeted round
                                            (new findings re-enter Phase 4 -> 4b)
Phase 5  Report (existing, augmented)
```

Verification runs **after** dedup so panels are never spent on duplicate findings.

**Harmonization:** team-review does not currently apply a confidence floor (only code-review does, at its Step 4a). Phase 4b introduces the same `>= 50%` floor here, aligning the two pipelines. The underlying reviewer agents already emit confidence scores (code-review depends on this), so team-review reviewer output already carries the needed data; only the gating is new.

State tracking: add `phase_4b_verification` and `phase_4c_critic` to `.team-review/state.json`. Verification verdicts are written to a single `.team-review/98-verification.md` (one row per finding: verdict tally, final severity, `contested`/`filtered`/`unverified` flag); the critic writes `.team-review/97-coverage-gaps.md`.

### Evolution of `/senior-review:code-review`

code-review already has a single-judge gate at `Step 4b`. It is **replaced**, not duplicated:

```
Step 4   Consolidate (existing: 4a confidence-gate, 4b dedup, 4c pre-existing, 4d sort/score)
Step 4b  Validate -> REWRITTEN: shared 3-lens panel, scope widened to all-above-floor
Step 4c  Completeness Critic (NEW)
Step 5   Report (existing, augmented)
```

The change from today: single validator -> 3-lens panel; Critical/High only -> everything above the >=50% floor; plus the new critic step. The existing `Validation: X of Y ...` report line is extended (see Output Changes).

## Verification panel mechanics

For each finding selected for verification, spawn **3 verifiers in parallel**, each with a distinct mandate (not three clones):

1. **Reachability / Correctness lens** — Does the code actually have the described problem? Is the path reachable? Is `file:line` correct? Trace the flow and prove the defect manifests. Catches hallucinations and wrong citations.
2. **False-positive-causes lens** — Try to break it: is it a framework convention, an intentional design choice, pre-existing code untouched by the diff, or a misread of context? Starts biased toward false-positive. Catches plausible-but-wrong findings.
3. **Severity lens** — Assuming it is real, is the severity right against the skill's calibration criteria (impact x likelihood)? May *downgrade* (e.g. High -> Medium) without killing the finding.

### Verifier verdict schema

Each verifier returns:

```
verdict:        REAL | FALSE_POSITIVE      # lens 3 always REAL; it only votes severity
confidence:     0-100
severity_vote:  Critical | High | Medium | Low | n/a   # only lens 3 sets this
reason:         1-2 sentences with a file:line citation
```

### Survival rule

- A finding **survives** if **at least 2 of lenses 1-2 vote REAL**.
- If **>= 2 vote FALSE_POSITIVE** -> discarded, counted as `filtered` (never silently dropped).
- **Tie / inconclusive** (1 REAL / 1 FALSE, or fewer than 2 valid verdicts return) -> the finding **survives, marked `contested`**. Rationale: a flagged false positive is cheaper than a killed real bug. (Confirmed during brainstorming over the "tie kills" alternative.)
- **Final severity** = lens-3 `severity_vote` if the finding is confirmed real; otherwise the original severity.

### Selection: what enters the panel

- **Normal (default-on):** every finding with confidence `>= 50%` that survived dedup, regardless of severity.
- **Under cost guard** (more than ~25 findings AND not `--rigorous`): narrow to **stakes + uncertainty band** = all Critical/High + any Medium/Low in the 50-75% confidence band or with severity contested between reviewers. The rest pass through with their confidence score and a `unverified (cost-guard)` note. **The narrowing is declared in the report.**
- **`--rigorous`:** ignore the cap; verify everything-above-floor always.
- **`--fast`:** skip the entire gate (verification + critic).

## Completeness critic mechanics

Runs after verification (Phase 4c / Step 4c). Reads: verified findings, scope (`00-scope.md` for team-review; the gathered scope for code-review), context (deep-dive + interconnect map for team-review; `.deep-dive/` if present for code-review), and the list of dimensions that ran.

Evaluates gaps against a fixed taxonomy:

- Dimensions not run (e.g. security skipped; no distributed-flows despite messaging signals).
- Files in scope cited by no reviewer (cross-check changed files vs files referenced in findings).
- `unverified` assumptions in the interconnect map that no finding addressed.
- High-risk hot-spots (from `05-risks.md` / Integration Hot-Spots) with zero findings.

**Decision:** if it identifies a high-risk **uncovered** area, it spawns **one** targeted reviewer (the most specialized agent for that area) for a **single** round. Those new findings re-enter dedup (Phase 4) and verification (Phase 4b). Bounded to one round.

**Degradation:** under cost guard or budget pressure, the critic degrades to **report-only** (emits the gap list, no re-spawn) and declares it. `--fast` skips the critic entirely along with the rest of the gate.

## Output changes

### team-review Phase 5 report

- New line: `Verification: X verified, Z false positives, W contested`.
- New `## Coverage Gaps` section from the critic.
- When narrowed: `Cost-guard: verification narrowed to stakes+band (N findings unverified)`.
- When the critic ran a follow-up round: note the follow-up dimension and its findings.

### code-review Step 5 report

- The existing `Validation: X of Y Critical/High findings validated ...` line becomes `Verification: X of Y (3-lens panel), Z false positives, W contested`.
- New `## Coverage Gaps` section.
- Cost-guard line when applicable.

## Cross-cutting behavior

### Cost guard is a finding-count proxy, not token budget

In substrate A (prose/Agent) there is no `budget.remaining()` API (that is Workflow-tool only). The guard therefore triggers on **number of findings (~25)**, not real tokens. This is stated explicitly in the skill and commands so no false precision is implied. A future Workflow rewire (direction 2) replaces the proxy with a real budget.

### Fail-open on verifiers

If a verifier fails or returns a malformed verdict, it counts as an abstention. If fewer than 2 valid verdicts return for a finding, the finding survives marked `contested`. The gate never crashes the pipeline and never silently drops a finding.

### Validation of this change (no CI in this repo)

There is no test harness or build step. "Testing" means:

- Run `marketplace-ops:skills-validate` on the modified skill and `marketplace-ops:marketplace-health` on the marketplace.
- Grep the modified files for dash-aside constructs (CLAUDE.md style rule).
- Verify both commands actually reference the new skill sections (no orphan logic).
- A written dry-run trace in the implementation plan: walk one synthetic review through Phase 4 -> 4b -> 4c -> 5 for both the normal and cost-guard paths.

### Versioning / marketplace

- Bump `agent-teams` (skill + team-review changed) — minor (new sections + phases).
- Bump `senior-review` (code-review changed) — minor (gate rewritten + critic added).
- Bump `metadata.version`.
- Update `marketplace.json` and commit together.
- Add a short note on the verification-panel pattern to `docs/references/agent-teams-best-practices.md` (the source of truth for these pipelines).

## Files touched (anticipated)

| File | Change |
|------|--------|
| `plugins/agent-teams/skills/multi-reviewer-patterns/SKILL.md` | Add `## Adversarial Verification Panel` and `## Completeness Critic` canonical sections; bump skill `version` |
| `plugins/agent-teams/commands/team-review.md` | Insert Phase 4b + 4c; extend Phase 5 report; add state.json keys; reference skill sections; document `--fast` / `--rigorous` |
| `plugins/senior-review/commands/code-review.md` | Rewrite Step 4b to the shared panel; add Step 4c critic; extend Step 5 report; document `--fast` / `--rigorous` |
| `docs/references/agent-teams-best-practices.md` | Add verification-panel pattern note |
| `.claude-plugin/marketplace.json` | Bump `agent-teams`, `senior-review`, `metadata.version` |

## Open questions

None outstanding. All five design decisions plus the substrate choice were locked during brainstorming.
