# Scope Boundaries and Non-Goals

This file exists so that exclusions are written down rather than merely omitted. An omitted exclusion gets re-added by a well-meaning future pass; a written one has to be argued with.

## The goal is not a finding category

> **Structural simplification is the desired outcome of the audit, not a finding category.**

Without this rule, every D1 to D7 finding can be restated as a "structural simplification opportunity" that carries no new information, and the report doubles in length while saying the same things twice.

## Excluded dimensions and their owners

Five structural concerns are deliberately outside this plugin. Each has an owner that already covers it, and each has a permitted role here as supporting evidence.

| Excluded | Owner | Permitted role here |
|---|---|---|
| Dependency structure: cycles, missed inversions, depth | `senior-review:code-auditor` for coupling, `senior-review:chicken-egg-detector` for initialization cycles | A dependency may be cited as supporting evidence for D1 to D7. "This dependency is wrong" is never an autonomous finding here. |
| Responsibility cohesion inside a module | `senior-review:code-auditor` | Two modules owning the same policy is evidence of D2. "This class has too many responsibilities" is not ours. |
| API surface size and contract drift | `senior-review:api-contract-auditor`, `senior-review:cleanup-auditor` D4 for barrel and unused-export bloat | May appear incidentally inside a D7 remediation. Never a category. |
| Indirection cost | absorbed as lens L2 | Contributes to D7. "Too much indirection" never opens a finding alone. |
| Structural simplification | none, it is the goal | See the rule above. |

## Dedup with `senior-review:code-auditor`

Both agents run as dimensions of the same review, so the boundary is load-bearing rather than theoretical.

- **Inside one file** belongs to `code-auditor`: god functions, stringly-typed code, a leaky signature, an interface with one implementation, all judged on what the file under review shows on its own.
- **Across files** belongs here: this already exists elsewhere, this is the occurrence that justifies unifying, this fact has two owners, this layer is bypassed by callers that live somewhere else.

Do not re-flag a smell that is fully visible inside one file without reference to another site.

## Other neighbours

- **Dead code, unused exports, orphan assets, VCS hygiene**: `senior-review:cleanup-auditor`. A duplicated representation that is simply unused is a cleanup finding, not a D3.
- **Style and readability**: `clean-code:clean-code`. Renaming for clarity is not a structural finding.
- **Contract violations against a documented invariant**: `senior-review:logic-integrity-auditor`. That agent hunts code that *breaks* a documented rule. This one hunts a rule that has *two authoritative statements*. The two are complementary and neither subsumes the other.
- **Persistence semantics**: `senior-review:data-integrity-auditor`. A derivable column with no constraint backing it is theirs. The same column with four repair functions around it is D4 here. When both apply, report D4 and note the overlap in Cross-Reviewer Notes.

## This plugin does not

- Produce a refactoring plan. `Suggested direction` names the target layer or the move in one sentence.
- Edit any file other than its own report and, in global mode, its own concept index.
- Score the codebase. `senior-review:code-auditor` owns the Code Quality Score.
