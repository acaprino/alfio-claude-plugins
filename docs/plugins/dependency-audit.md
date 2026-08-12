# Dependency Audit Plugin

> Evidence-first dependency auditing: vulnerabilities, outdated packages, license obligations, and supply-chain signals, reported straight from each ecosystem's real tooling. Hand-authored replacement for the retired `codebase-cleanup` deps-audit command.

## Design principles

The plugin exists to audit dependencies without inventing facts. Five rules bind every run:

1. **Tools, not simulations.** Facts come from the ecosystem's own audit tooling, registries, and advisory databases (OSV, GitHub Advisories, RustSec, PyPA). No pseudo-code scanners.
2. **Evidence tiers.** Every claim is `TOOL-REPORTED`, `INFERRED` (derivation stated), or `UNKNOWN` (with what would resolve it). No invented hours, percentages, or dollar figures.
3. **Non-destructive.** Never `npm audit fix --force`, never unapproved major upgrades, never lockfile regeneration or dependency replacement without a presented plan (change, compatibility risk, test/rollback) and explicit approval.
4. **Licenses as obligations.** No binary compatibility matrix; findings state the obligation category, the trigger condition (distribution vs network use), and the question the owner must answer. Unknown licenses escalate to legal review.
5. **Honest coverage.** A missing tool or unreachable registry is a reported gap with an install command, never a silently skipped or simulated section.

## Commands

### `/dependency-audit:deps-audit`

```
/dependency-audit:deps-audit [path] [--ecosystem=npm|python|rust|go|ruby|php|java|dotnet|all] [--security-only] [--license-check] [--update-pr]
```

Seven-step workflow: discover ecosystems from manifests, load the per-ecosystem playbook, run vulnerability audits (native tool per ecosystem, `osv-scanner` as cross-check), measure outdated lag, run the license obligations analysis (`--license-check`), evaluate supply-chain signals, and produce a remediation plan. `--update-pr` applies an approved subset on a branch, runs the project's tests, and opens the PR via `gh`; a red branch is reverted, never pushed.

| Flag | Effect |
|---|---|
| `--ecosystem=` | Restrict to one ecosystem |
| `--security-only` | Vulnerabilities only; skip outdated, licenses, supply chain |
| `--license-check` | Include the license obligations analysis |
| `--update-pr` | After approval of the remediation table, apply and open a PR |

## Skills

### `dependency-audit`

Knowledge base loaded by the command (and usable standalone when auditing dependencies by hand).

| | |
|---|---|
| **Trigger** | Auditing dependencies for CVEs, license obligations, outdated packages, or supply-chain risk |
| **References** | `ecosystems.md` (per-ecosystem audit/outdated/license tool matrix with parse notes), `license-analysis.md` (obligations model, category table, finding wording rules), `supply-chain.md` (verifiable signal catalog: install scripts, registry metadata, lockfile integrity, dependency confusion, advisory databases) |

**Ecosystem coverage:** npm/pnpm/yarn/bun, Python (pip, uv, poetry), Rust (cargo), Go, Ruby (bundler), PHP (composer), Java (Maven/Gradle), .NET, plus `osv-scanner` as the cross-ecosystem fallback and second source.

---

**Related:** [senior-review](senior-review.md) (`cleanup-auditor` finds unused and phantom dependencies; `/code-review --commit` removes them at Step 7c), [typescript-development](typescript-development.md) (`knip` for TS/JS dead deps), [python-development](python-development.md) (`/python-audit` for Python lint/type/coverage).

**History:** replaces `/codebase-cleanup:deps-audit`, retired in marketplace 19.0.0. This plugin is local, hand-authored content with no upstream; it is maintained under the `custom-plugin-refresh` protocol.
