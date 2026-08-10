# Review pipeline: epistemic independence

Date: 2026-08-10
Plugins: `codebase-xray`, `senior-review`
Status: approved, pending implementation plan

## The incident

A `/senior-review:team-review` run on the Jupiter codebase reported a Critical finding: heartbeat responses cannot refill strategy credentials. The finding was false at the system level. Two heartbeat paths exist, and the second one carries credentials on the probe response. The project documented this correctly and prominently: `docs/00_navigation/SEARCH_INDEX.md` carries a "Credential Refill" entry pointing at `docs/01_domains/agents/heartbeat.md`, which explains why two paths exist, and `auto_registration.md` describes the convergence.

Four review dimensions reported the problem independently. Their agreement was not corroboration. All four had been given the same premise by the orchestrator, derived from a true but partial X-ray observation: the periodic heartbeat metadata carries no strategy fields. True of one path, silent about the other.

## Root cause

The pipeline is `code -> X-ray -> interconnect map -> N reviewers -> verification`. It looks redundant and is not. X-ray and the map are a single epistemic point of failure: one observer forms a premise and N observers explore it. A wrong premise produces N concordant wrong findings, and the verification panel cannot catch it because each verifier confirms a locally true fact underneath a globally false conclusion.

Three properties of the current implementation made this reachable:

1. **The map is treated as authoritative.** `senior-review/agents/logic-integrity-auditor.md:56` says "Do not search where the map says nothing" and `:202` says "Do NOT read the full target codebase if the map did not flag an anchor". Both contradict the `[MAP-GAP]` mechanism at `:197`, which asks the same agent to report rules the map missed.
2. **The shared context has no declared epistemic status.** The reviewer prompt template (`senior-review/commands/team-review.md:276-296`) says "read these before analyzing code" and never says what the context is worth. `review-quality-gates/SKILL.md:27` supplies a rationale ("Without shared context, each reviewer re-reads the code from scratch. This is wasteful") that makes treating the context as settled fact feel sanctioned. The instruction "do not re-derive, build on top" that the orchestrating session injected into all eight reviewers does not exist anywhere in the plugins. It was improvised into the space the template leaves open.
3. **The one quality metric rewards the correlation.** `review-quality-gates/SKILL.md:75-83` scores the fraction of findings citing a map anchor, calls 30% or more "the pipeline is paying off", and asks logic-integrity for 70% or more. `team-review.md:414` prints it to the user labeled `<- quality metric`.

Documentation discovery is the fourth contributing factor and a separate defect. `--depth=lite` is the team-review default (`team-review.md:213`) and skips Phase 6 Documentation Health (`codebase-xray/commands/analyze.md:135`), so no agent ever opened the docs directory. Phase 6 is also the wrong instrument: it is an audit *of* documentation, not a use *of* documentation as a discovery lead.

## The invariant

This becomes a first-level section of `review-quality-gates/SKILL.md`, not a note inside general quality advice:

> **Shared-context provenance rule.** Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.

## Topology

```
Phase 0c   Review Evidence Discovery                    [senior-review]
           writes .team-review/01a-review-knowledge-leads.md   IMMUTABLE
                              |
              +---------------+---------------+
              |                               |
Phase 1a   X-RAY                         Phase 1c  PREMISE AUDITOR
           + Project Knowledge Discovery            blind independent derivation
           writes <run-dir>/knowledge/              reads ONLY 01a + repo
             navigation.md                          forbidden: .deep-dive/,
             documentation-leads.md                            02-interconnect.md
              |                               |
              |                               writes 01b-independent-claims.md
              +---------------+---------------+
                              |
                       RECONCILIATION
                       writes .team-review/01-knowledge-provenance.md
                              |
Phase 1b   INTERCONNECT MAP                              [codebase-xray]
           fallible hypothesis index, states include `disputed`
                              |
Phase 2    REVIEWERS
           every finding declares its load-bearing premise and provenance
                              |
Phase 4    CONSOLIDATION
           dependent agreement is not corroboration
                              |
Phase 4b   LENS 0 -> lenses 1-2 -> lens 3
           counterexample-backed premise attack, gated on provenance
```

Two rules make the isolation real:

- `01a-review-knowledge-leads.md` is written once, at Phase 0c, and never mutated. X-ray does not append to it. The Premise Auditor consumes an immutable snapshot of navigation pointers, so its blindness is demonstrable rather than assumed.
- The three-block provenance view is a derived artifact produced at the join, after both branches complete. It is not a bus shared between two concurrent branches.

## Intervention A: remove undue authority from the map

### A1. `senior-review/agents/logic-integrity-auditor.md`

Prime Directive 1 becomes `Map-first, never map-authoritative`. The map is a fallible hypothesis index.

Delete the second sentence of `:56` ("Do not search where the map says nothing") and the whole of `:202` ("Do NOT read the full target codebase if the map did not flag an anchor").

For every review category in scope, the agent performs, in order:

1. the mapped anchors first,
2. at least one independent discovery pass from the changed code, the knowledge leads, tests, callers and callees, and semantic siblings,
3. an active search for evidence that contradicts the map,
4. a `[MAP-GAP]` finding when independent evidence reveals an omitted contract, path, invariant or domain rule.

The scope budget at `:209` stays. Independent discovery is bounded, not unbounded.

### A2. The map declares its own status

`codebase-xray/agents/semantic-interconnect-mapper.md` gains a mandatory header line in its output format, stating that the map is an index of fallible hypotheses and not ground truth, and that every consumer must verify a row before using it as a premise for a finding.

### A3. Extend the existing status vocabulary

Today `verified | documented | unverified` exists only on `## Assumptions` (`semantic-interconnect-mapper.md:129-132`, `:212-214`) and half-exists on implicit contracts (`:197`). Extend the same column to all three contract layers, to `## Invariants` and to `## Domain Rules`, and add a fourth value:

- `disputed`: the Premise Auditor's independent derivation contradicts this row, or two sources within the repository disagree. Carries both citations.

No second taxonomy is introduced. Fewer concepts means a higher chance agents actually use the convention.

## Intervention B: provenance and adversarial independence

### B1. Declare the status of the shared context

The reviewer prompt template in `senior-review/commands/team-review.md` and the agent prompts in `senior-review/skills/review-quality-gates/references/code-review-agents.md` gain an explicit clause:

> The shared context is not ground truth. Claims marked `verified` may be reused. Claims marked `documented`, `unverified` or `disputed` are hypotheses: verify them independently before using them as the premise of a finding. Actively look for code paths that contradict them.

`review-quality-gates/SKILL.md:27` is rewritten. Controlled redundancy on load-bearing premises is deliberate, not waste. The economy argument applies to re-reading the whole codebase, never to re-deriving a premise a finding stands on.

### B2. Finding format

Two fields are added to the finding format of every reviewer agent that runs in the pipeline:

```
- Load-bearing premise: "No credential-bearing response path exists after registration"
- premise_provenance: independent | shared-context | mixed
```

Rules for the premise text, enforced by the format documentation and checked by Lens 0:

- **minimal**: the single proposition whose falsity collapses the whole finding,
- **falsifiable**: stated so that a concrete counterexample would settle it,
- **scoped**: naming the path, component or condition it ranges over.

```
Bad:  "The implementation is broken."
Bad:  "Heartbeat handling is incorrect."          (paraphrase of the finding)
Good: "No credential-bearing response path exists after registration."
```

`premise_provenance` records causal dependence, not formal citation. A reviewer that absorbed an invariant from the map and then produced an apparently autonomous finding declares `shared-context`, not `independent`.

Degradation: a finding with no `premise_provenance` is treated as `shared-context` when the pipeline ran, and the report records the reviewer as format-non-compliant. A finding with no `Load-bearing premise` has one derived by Lens 0, with the same non-compliance note. The pipeline never drops a finding over a missing field.

### B3. Premise Auditor

New agent: `senior-review/agents/premise-auditor.md`. One agent, two modes.

**Independent mode (Phase 1c).**

```
inputs:      diff and scope, .team-review/01a-review-knowledge-leads.md,
             the repository, tests and docs it reaches on its own
forbidden:   .deep-dive/ in any form, .team-review/02-interconnect.md,
             any X-ray conclusion
output:      .team-review/01b-independent-claims.md
mandate:     derive only. Do not compare, do not review, do not propose fixes.
```

It receives pointers to where the project keeps its knowledge, never X-ray's conclusions about the code. The claims it produces carry the same status vocabulary as A3, including `documented` for anything it read but did not verify against code.

**Adversarial mode (Phase 4b, Lens 0).** Full context allowed: the finding, its declared premise, the map, the deep-dive output, the knowledge provenance file.

Comparison between the two derivations belongs to the reconciliation step and the mapper, never to the auditor itself. Independent derivation, centralized comparison.

Architecture note: the mapper lives in `codebase-xray` and will receive the path of `01b-independent-claims.md` as a prompt input. A path is not a reference to a `senior-review` agent, skill or command, so the forbidden `codebase-xray -> senior-review` edge stays closed.

### B4. Lens 0

Runs before lenses 1-2, gated on `premise_provenance` in `{shared-context, mixed}`. Findings marked `independent` skip it. Running it first mirrors the existing gated-lens rationale: it avoids spending lenses 1-2 on findings a veto would discard anyway.

Return schema:

```
premise_verdict:    HOLDS | REFUTED | UNCERTAIN
refutation_target:  PREMISE | SUPPORT        (required when REFUTED)
counterexample:     file:line                (required when REFUTED)
reason:             1-2 sentences with citation
```

`REFUTED` without a counterexample citation degrades to `UNCERTAIN`. This is the whole of the veto-only-with-evidence rule.

Resolution, refutation type first and provenance second:

| Lens 0 result | Effect |
|---|---|
| `REFUTED`, target `PREMISE` | Finding discarded, `filtered: premise-refuted`. Regardless of provenance and regardless of lenses 1-2. |
| `REFUTED`, target `SUPPORT`, provenance `mixed` | Strike the shared leg, restate the finding from the surviving independent evidence, run lenses 1-2 on the reduced finding. |
| `REFUTED`, target `SUPPORT`, provenance `shared-context` | Nothing survives the strike. Discarded, `filtered: premise-refuted`. |
| `UNCERTAIN` or `HOLDS` | Finding proceeds to lenses 1-2 as today. `UNCERTAIN` adds the tag `premise-contested`. |

The distinction matters because local correctness cannot outvote a refuted premise. In the incident, lenses 1 and 2 were right: the periodic heartbeat metadata really does lack strategy fields. The inference from that fact to "no heartbeat path can refill credentials" is what the probe response path kills, and it stays dead even for a reviewer that verified the periodic path independently.

Lens 0 also checks the premise against the B2 rules. A premise that is a paraphrase of the finding rather than a minimal falsifiable proposition is returned as non-compliant and the finding is tagged, never silently accepted.

### B5. Consolidation

`team-review.md:349-360` point 4 currently reads: findings appearing in multiple dimensions are "a sign of a likely-real root cause". It becomes conditional on provenance:

- Agreement between findings with `independent` provenance, or with disjoint premises, remains a corroboration signal.
- Agreement between findings sharing the same `shared-context` premise is reported as **echo**, with the shared premise named. It raises no confidence and no severity.

The report distinguishes the two explicitly. Agreement and independent corroboration become different words for different things.

## Intervention C: discovery and plumbing

### C1. `codebase-xray`: Project Knowledge Discovery

New always-on phase, running in every depth including `--depth=lite`. It is numbered **Phase 0** and runs first, before structure extraction. Phases 1 through 7 keep their current numbers, because `--phase N` is a user-facing flag and renumbering would break every invocation that names a phase. It executes **inline in the orchestrating context**, not as a spawned agent: reading the project instructions and globbing for index files is cheap, and Phase 7 already sets the precedent for inline work.

It owns discovery of **how the repository documents itself**:

- read `CLAUDE.md` and equivalent project instruction files,
- locate the canonical indexes the project actually uses: search indexes, README, ADR indexes, architecture and domain indexes, doc entry points,
- record the navigation conventions themselves, meaning which file the project treats as its semantic index,
- search for documents attached to the concepts, symbols and subsystems in scope.

Output, inside the run directory:

```
<run-dir>/knowledge/navigation.md            how this repo organizes its knowledge
<run-dir>/knowledge/documentation-leads.md   concept -> document, every row `documented`/`unverified`
```

Everything it produces is a **lead**, never a truth. Phase 6 Documentation Health stays full-only and keeps its current meaning as an audit of documentation quality and drift.

The `## CRITICAL PRINCIPLE: ABSOLUTE SOURCE OF TRUTH` block at `skills/analyze/SKILL.md:110-128` is **not weakened**. Rule 2 and rule 7 are epistemically correct and are the reason stale documentation does not poison the analysis. One line is added distinguishing the two roles a document can play: as evidence it remains an unverified claim requiring validation, as a discovery lead it is a first-class input that must be collected early.

### C2. `senior-review`: Review Evidence Discovery

New Phase 0c, owning discovery of **what evidence is relevant to this review**:

- start from the diff, the scope and the concepts it touches,
- use the navigation conventions when X-ray has already published them for this repository, and discover them independently when it has not,
- find documents, tests and alternate paths pertinent to the change,
- write `.team-review/01a-review-knowledge-leads.md`, immutable once written.

The duty of autonomous rediscovery is written as an obligation, not a permission:

> X-ray's documentation leads are an input, never a completeness guarantee. When no lead exists for a concept the diff touches, search the available indexes yourself and record what you find under `Independently discovered by Senior Review`.

Without this clause the completeness of X-ray's discovery would become the next shared premise, which is the failure mode this design exists to remove.

### C3. Knowledge reconciliation

After Phase 1a and Phase 1c both complete, the orchestrator produces the derived view:

```markdown
# Knowledge provenance

## Independently discovered by Senior Review
[rows from 01a]

## Inherited from X-Ray
[rows from <run-dir>/knowledge/documentation-leads.md]

## Missing / Disputed
[concepts in scope with no lead from either source]
[claims where 01b-independent-claims.md contradicts an X-ray conclusion]
```

Written to `.team-review/01-knowledge-provenance.md`. This is the canonical artifact consumed downstream. `01a` and `01b` are the two sources that feed it. Rows in `Missing / Disputed` become `disputed` states in the interconnect map.

### Behaviour under `--skip-interconnect`

Phase 0c still runs. Knowledge leads help reviewers whether or not a map exists, and the phase is cheap.

Phase 1a, 1c, the reconciliation and Phase 1b are all skipped, as today. With no shared context, every finding is `independent` by construction, so Lens 0 never fires and the consolidation echo rule never triggers. The mode degrades to itself without special cases.

### C4. Run directory provenance

Rule added to the `codebase-xray` contract, next to the concurrent runs model at `skills/analyze/SKILL.md:102-108`:

> `.deep-dive/` is a mutable convenience mirror of the latest published run. It MUST NOT be used by an orchestrated workflow to consume the output of a specific X-ray invocation. Such workflows MUST retain and propagate the immutable run directory `.deep-dive/runs/<run-id>/`.

The general form: a specific invocation implies the immutable run directory, a latest-state consumer implies the mirror. The race exists only where causality exists between "this pipeline produced run X" and "this pipeline must now consume X". One-shot commands asking for the most recent published analysis are correct on the mirror, and are left alone.

`.team-review/state.json` gains an official provenance block instead of a free-form string in prompts:

```json
"xray": {
  "run_id": "...",
  "run_dir": ".deep-dive/runs/...",
  "target": "...",
  "depth": "lite"
}
```

Every later step derives its paths from that block. A review becomes reproducible, and each artifact traceable to exactly the X-ray run that fed it.

Perimeter: `team-review`, `code-review`, `review-quality-gates` and the mapper prompt. `project-setup`, `abstraction-architect` invoked directly, and `codebase-mapper` keep reading the mirror.

### C5. Metrics

Remove the quality framing of context utilization: the thresholds at `review-quality-gates/SKILL.md:79-83` and the `<- quality metric` label at `team-review.md:414`. Map utilization survives as an operational number only.

New metrics:

| Metric | Meaning |
|---|---|
| Independent verification rate | fraction of findings whose load-bearing premise was independently reconstructed by a reviewer or by Lens 0 |
| Map challenge rate | fraction of consumed map rows explicitly tested rather than assumed |
| Map gap rate | rules, paths and invariants discovered independently that the map never carried |
| Cross-source corroboration rate | findings corroborated across code, tests and documentation |

Caveat carried in the text for the last one: it is a diagnostic over findings for which multiple semantically relevant sources exist, never a number to maximize. Many findings are provable entirely from code, and a low rate on those is correct.

### C6. Eval case

New case `evals/senior-review/cases/jupiter-credential-refill`. The harness already counts FP rate (`evals/senior-review/README.md:24-27`), so no new structure is required. The case format gains one field:

```yaml
must_not_report:
  - claim: "heartbeat responses cannot refill strategy credentials"
    why_false: "probe response path carries credentials"
    evidence: "docs/01_domains/agents/heartbeat.md, auto_registration.md, probe handler"
```

Scoring: reporting a `must_not_report` claim that survives the pipeline's own verification is a scored failure, not merely a counted false positive. This is the regression test for the whole change.

## Deliberately not done

- The source-of-truth doctrine is not weakened. The defect was that documents were never collected as leads, not that they were distrusted as evidence.
- No second epistemic taxonomy. The existing status column is extended and gains one value.
- The run-id is not propagated to standalone consumers. 104 occurrences across 19 files would turn a precise correction into an infrastructure refactor for no additional safety.
- The Premise Auditor is not a second code review. It derives premises and attacks them, nothing else.
- No new agent in `codebase-xray`. Project Knowledge Discovery is a phase of the analyze skill.
- `/senior-review:cleanup-dead-code` stays retired and no command is recreated.

## Blast radius

| Plugin | Files |
|---|---|
| `codebase-xray` | `skills/analyze/SKILL.md`, `commands/analyze.md`, `commands/team-analyze.md`, `agents/semantic-interconnect-mapper.md`, the partition workers that mirror the phase list |
| `senior-review` | `commands/team-review.md`, `commands/code-review.md`, `skills/review-quality-gates/SKILL.md`, `skills/review-quality-gates/references/code-review-agents.md`, `agents/premise-auditor.md` (new), `agents/logic-integrity-auditor.md`, plus the finding-format section of every pipeline reviewer agent |
| repo | `evals/senior-review/` case and README, `exports/vscode/` bundles for both plugins |

Marketplace mechanics: bump both plugin versions and `metadata.version`, mirror into `exports/`, regenerate the extension manifest if the new agent changes the contribution lists, bump `exports/vscode/package.json`, and pass the five consistency checks. Stage explicit paths, never `git add -A`, because other sessions run this repository concurrently.

## Verification

1. `python scripts/lint_dependency_graph.py`: the new agent adds no cross-plugin runtime reference, and the `codebase-xray -> senior-review` edge must stay absent.
2. `python scripts/lint_bundled_paths.py`: all new reference paths use `${CLAUDE_PLUGIN_ROOT}` or skill-relative form.
3. `python .claude/skills/downstream-exports/scripts/check_export.py`.
4. `python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check`.
5. `python scripts/check_version_bumps.py <base-rev>`.
6. The `jupiter-credential-refill` case runs and the false finding is not reported.
