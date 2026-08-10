---
name: dependency-audit
description: >
  Knowledge base for evidence-first dependency auditing: the per-ecosystem audit/outdated/license tool matrix, the license-obligations analysis model, and the verifiable supply-chain signal catalog. Tool-first and evidence-tiered; forbids destructive remediation.
  TRIGGER WHEN: auditing dependencies for vulnerabilities, license obligations, outdated packages, or supply-chain risk in any ecosystem; loaded by the /dependency-audit:deps-audit command.
  DO NOT TRIGGER WHEN: dead-code or unused-dependency cleanup (use senior-review:code-review or typescript-development:knip), Python-only lint/type audits (use python-development:python-audit), or code-level security review (use senior-review:security-auditor).
---

# Dependency Audit Knowledge Base

Method for auditing third-party dependencies without inventing facts. The `/dependency-audit:deps-audit` command orchestrates; this skill holds the depth, split into references loaded on demand.

## Core principles

1. **Tool-first.** The audit runs the ecosystem's own tooling and reads registries and advisory databases (OSV, GitHub Advisories, RustSec, PyPA). It never re-implements a scanner in pseudo-code and never guesses what a tool would have said.
2. **Evidence tiers.** Every reported fact is `TOOL-REPORTED`, `INFERRED` (with the derivation stated), or `UNKNOWN` (with what would resolve it). Fabricated quantities of any kind are forbidden: no estimated hours, no invented percentages, no dollar figures.
3. **Non-destructive remediation.** Never `--force`, never unapproved major-version upgrades, never lockfile regeneration, never dependency replacement without first presenting the proposed change, its compatibility risk, and a test/rollback plan.
4. **Licenses are obligations, not a matrix.** License analysis asks what obligations a dependency's license imposes given how the project combines and distributes it. Binary "X is incompatible with Y" tables are wrong often enough to be banned.
5. **Honest coverage.** Missing tools and unreachable registries are reported as gaps, with install commands, instead of being papered over.

## References

| File | Load when |
|---|---|
| `references/ecosystems.md` | Selecting or running audit / outdated / license tooling for any ecosystem, or parsing its output |
| `references/license-analysis.md` | Writing any license finding, classifying an SPDX identifier, or answering a copyleft question |
| `references/supply-chain.md` | Evaluating supply-chain risk signals or reviewing a dependency diff for tampering |
