---
name: defect-taxonomy
description: >
  16 macro-categories and 140+ subcategories of source-code failure modes, with CWE and OWASP
  mappings, fix patterns, and review frameworks.
  Use when an audit needs structured defect classification, a detection strategy, or severity
  calibration; loaded by `review-code-auditor`, `review-security-auditor`, and
  `review-ui-race-auditor`.
user-invocable: false
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: senior-review
---

# Defect Taxonomy Knowledge Base

Unified classification of source code defects synthesizing MITRE CWE, OWASP Top 10, NASA Power of 10, IBM ODC, IEEE 1044, and Beizer's taxonomy into actionable detection references.

## Reference Files

Load relevant references based on the code domain under review. Do NOT load all files -- select only what applies.

### Taxonomy References (defect patterns)

| Reference | When to load |
|-----------|-------------|
| `references/concurrency-state.md` | Concurrent/parallel code, shared state, async patterns, closures, variable scoping |
| `references/logic-types.md` | Comparisons, boolean logic, type conversions, generics, serialization |
| `references/memory-resources.md` | Memory management (C/C++/Rust), resource lifecycle, error handling, performance bottlenecks |
| `references/security.md` | Security review -- injection, auth, crypto, secrets, CORS, SSRF, input validation |
| `references/distributed-integration.md` | Microservices, APIs, distributed state, message queues, service mesh, migrations |
| `references/data-design-ops.md` | Database/ORM, design patterns, build/deploy, testing, observability |
| `references/detection-matrix.md` | Cross-cutting: detection channels per category, language-weighted focus, ROI prioritization |

### Review Frameworks (analysis methodology)

| Reference | When to load |
|-----------|-------------|
| `references/review-frameworks.md` | Always load for `review-code-auditor`. Contains cognitive models, failure flow methodology, anti-pattern checklist, mental models, severity/scoring system |

## Language-Weighted Category Focus

- **C/C++**: concurrency-state.md + memory-resources.md (categories 1, 5)
- **JVM (Java/Kotlin/Scala)**: concurrency-state.md + logic-types.md + memory-resources.md (categories 2, 7, 8)
- **JavaScript/TypeScript**: concurrency-state.md + logic-types.md + security.md (categories 2, 4, 6)
- **Python**: logic-types.md + security.md + memory-resources.md (categories 4, 6, 7)
- **Go/Rust**: concurrency-state.md + memory-resources.md (categories 1, 5, 7)
- **Microservices (any)**: distributed-integration.md + data-design-ops.md (categories 8-12)

## Usage Instructions

1. Identify the language(s) and domain of the code under review
2. Load the review-frameworks.md reference (for the `review-code-auditor` agent)
3. Load 1-3 taxonomy references matching the language/domain
4. Apply detection strategies from the loaded references during analysis
5. Map findings to CWE identifiers where applicable
6. Use the detection-matrix.md to prioritize detection approach
