---
name: dependency-audit
description: >
  Knowledge base for evidence-first dependency auditing: the per-ecosystem audit/outdated/license tool
  matrix, the license-obligations analysis model, and the verifiable supply-chain signal catalog.
  Tool-first and evidence-tiered; forbids destructive remediation. Use when auditing dependencies for
  vulnerabilities, license obligations, outdated packages, or supply-chain risk in any ecosystem, or
  when running /deps-audit. Not for dead-code or unused-dependency cleanup, which `/team-review` in the
  `_pipelines` bundle and the `knip` skill in the `typescript-development` bundle cover, Python-only
  lint and type audits, which `/python-audit` in the `python-development` bundle covers, or code-level
  security review, which the `review-security-auditor` agent in the `_pipelines` bundle covers.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: dependency-audit
---

# Dependency Audit Knowledge Base

Method for auditing third-party dependencies without inventing facts. The `/deps-audit` prompt orchestrates; this skill holds the depth, split into references loaded on demand.

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
