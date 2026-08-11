---
name: analyze
description: >
  AI-powered systematic codebase analysis. Combines structure extraction with semantic understanding to produce ground-truth documentation capturing WHAT, WHY, HOW, and CONSEQUENCES. Multi-language: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust. Includes pattern recognition, red flag detection, flow tracing, quality assessment, and concurrent analysis runs.
  TRIGGER WHEN: encountering unfamiliar code, before major refactoring, when pre-review technical context is needed, or when documentation is stale or missing.
  DO NOT TRIGGER WHEN: the user wants human-readable narrative docs (use codebase-mapper:map-codebase), a public-facing README (use docs plugins), or a code review verdict (use senior-review skills; they consume this skill's output instead).
---

# Codebase X-Ray Analysis Skill

## Overview

This skill combines **mechanical structure extraction** with **Claude's semantic understanding** to produce comprehensive codebase documentation. Unlike simple AST parsing, this skill captures:

- **WHAT** the code does (structure, functions, classes)
- **WHY** it exists (business purpose, design decisions)
- **HOW** it integrates (dependencies, contracts, flows)
- **CONSEQUENCES** of changes (side effects, failure modes)

## Language Support

| Language | Extensions | Structural extraction | Comment rewriting |
|---|---|---|---|
| Python | `.py`, `.pyi` | stdlib `ast` (always available) | `#` line + docstrings |
| Java | `.java` | tree-sitter (preferred) or regex | `//`, `/* */`, Javadoc `/** */` |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` | tree-sitter (preferred) or regex | `//`, `/* */`, JSDoc `/** */` |
| TypeScript | `.ts`, `.tsx`, `.mts`, `.cts` | tree-sitter (preferred) or regex; adds interfaces, enums, type aliases | `//`, `/* */`, JSDoc `/** */` |
| SQL | `.sql`, `.ddl`, `.dml` | regex DDL (tables, views, indexes, sequences, types, functions, procedures, triggers) | `--`, `/* */` |
| PL/SQL (Oracle) | `.pks`, `.pkb`, `.plsql`, `.pls`, `.pck`, `.prc`, `.fnc`, `.trg` | regex (packages, package bodies, type bodies, cursors, exceptions, %TYPE/%ROWTYPE references) | `--`, `/* */` |
| Rust | `.rs` | tree-sitter (preferred) or regex; structs, enums, traits, impls (with `Trait for Type` naming), mods, unions, type aliases | `//`, `/* */`, rustdoc `///` / `//!` / `/** */` / `/*! */` |

`.sql` files are disambiguated against PL/SQL by inspecting content for Oracle-specific markers (`CREATE OR REPLACE PACKAGE`, `DBMS_OUTPUT`, `%TYPE`, `%ROWTYPE`, `UTL_FILE`, `PRAGMA AUTONOMOUS`, etc.). PostgreSQL `plpgsql` is correctly classified as SQL.

## Prerequisites

The scripts require Python >= 3.10 and work **out of the box** with just the stdlib. Tree-sitter is optional and improves accuracy for Java / JavaScript / TypeScript / Rust:

```bash
# Optional: install for higher-fidelity parsing
pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/requirements.txt"
# or
uv pip install -r "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/requirements.txt"
```

What changes when tree-sitter is installed:

- **Java**: nested classes, generic type parameters, annotations, multi-line declarations parsed correctly. Without it, the regex fallback still finds top-level classes, methods, imports, and constants.
- **JavaScript / TypeScript**: arrow functions in object/class properties, decorators, template literals, JSX elements parsed correctly. Without it, the regex fallback handles top-level declarations, ES6 `import`/`export`, and CommonJS `require`.
- **Rust**: lifetimes, generic bounds (`where` clauses), impl blocks with trait bounds, attribute macros parsed correctly. Without it, the regex fallback still finds top-level fns, structs/enums/traits/impls/mods, use declarations, and UPPER_CASE constants.
- **Python / SQL / PL-SQL**: no change. Python always uses stdlib `ast`; SQL/PL-SQL always use the regex DDL extractor.

The active parser is reported in `ParseResult.notes` and in the CLI output: `parser=stdlib-ast`, `parser=tree-sitter`, or `parser=regex-fallback`.

### Capabilities

**Mechanical Analysis (Scripts):**
- Extract code structure (classes, functions, imports)
- Map dependencies (internal/external)
- Find symbol usages across the codebase
- Classify files by criticality

**Semantic Analysis (Claude AI):**
- Recognize architectural and design patterns
- Identify red flags and anti-patterns
- Trace data and control flows
- Document contracts and invariants
- Assess quality and maintainability

**Documentation Maintenance:**
- Review and maintain documentation (Phase 6)
- Fix broken links and update navigation indexes
- Analyze and rewrite code comments (antirez standards)

**Use this skill when:**
- Analyzing a codebase you're unfamiliar with
- Generating documentation that explains WHY, not just WHAT
- Identifying architectural patterns and anti-patterns
- Building technical ground truth before a code review
- Onboarding to a new project

## How This Skill Is Invoked

This skill is driven by the `/codebase-xray:analyze` command (single context) and `/codebase-xray:team-analyze` (multi-agent, partitioned). Both manage their state automatically under `.deep-dive/` using the concurrent runs model below.

## Concurrent Runs Model

Multiple analyses can run at the same time (different targets, different sessions, or a re-analysis while an older one is still in flight). Every analysis is an isolated **run**:

```
.deep-dive/
├── runs.json                          # registry: active runs + latest completed
├── runs/
│   └── <run-id>/                      # one directory per analysis run
│       ├── state.json                 # per-run phase tracking
│       ├── knowledge/                   # Phase 0: navigation.md, documentation-leads.md
│       ├── 01-structure.md .. 07-final-report.md
│       ├── partitions/<name>/...      # team mode only
│       └── 08-interconnect-map.md     # team mode only
├── state.json                         # mirror of the latest published run
└── 01-structure.md .. 08-*.md         # mirror of the latest published run
```

Rules:

1. **Run identity.** `run-id` = slug of the target path + `-YYYYMMDD-HHMMSS`, or the value of `--run-name <name>` (normalized to `[a-z0-9-]`; on collision append `-2`, `-3`, ...).
2. **Isolation.** A run writes ONLY inside `.deep-dive/runs/<run-id>/` while in progress. Concurrent runs never share files.
3. **Registry.** `runs.json` holds `{"schema": 2, "active": [{run_id, target, mode, started_at}], "latest_completed": "<run-id>"}`. Commands register their run at start and update the registry at completion. Read-modify-write it; never blindly overwrite entries you did not create.
4. **Publish step.** On successful completion, the orchestrating command copies the run's `01..0N.md` files and `state.json` to the `.deep-dive/` root and sets `latest_completed`. The root mirror is the **downstream contract**: consumers (`/senior-review:team-review`, `/senior-review:code-review`, `/codebase-mapper:map-codebase`, `/project-setup:create-claude-md`) keep reading `.deep-dive/01-structure.md` etc. unchanged. If two runs finish concurrently, the last one to publish owns the root mirror; both remain intact under `runs/`.
5. **Resume.** On invocation, the command reads `runs.json`: active runs are offered for resume; completed runs can be archived or re-published. A root `state.json` containing `current_phase` with no `runs.json` present is a pre-runs legacy layout: offer to migrate it into `runs/legacy-<date>/` before starting.
6. **Mirror is for latest-state consumers only.** `.deep-dive/` is a mutable convenience mirror of the latest published run. It MUST NOT be used by an orchestrated workflow to consume the output of a specific X-ray invocation: rule 4 makes the root mirror owned by whichever run published last, so a concurrent run can replace it between production and consumption. A workflow that started a run and then consumes it MUST retain and propagate the immutable run directory `.deep-dive/runs/<run-id>/`. The general form: a specific invocation implies the immutable run directory, a latest-state consumer implies the mirror. One-shot commands asking for the most recent published analysis are correct on the mirror.

## CRITICAL PRINCIPLE: ABSOLUTE SOURCE OF TRUTH

> **THE DOCUMENTATION GENERATED BY THIS SKILL IS THE ABSOLUTE AND UNQUESTIONABLE SOURCE OF TRUTH FOR YOUR PROJECT.**
>
> **ANY INFORMATION NOT VERIFIED WITH IRREFUTABLE EVIDENCE FROM SOURCE CODE IS FALSE, UNRELIABLE, AND UNACCEPTABLE.**

### Mandatory Rules (VIOLATION = FAILURE)

1. **NEVER** document anything without reading the actual source code first
2. **NEVER** assume any existing documentation, comment, or docstring is accurate
3. **NEVER** write documentation based on memory, inference, or "what should be"
4. **ALWAYS** derive truth EXCLUSIVELY from reading and tracing actual code
5. **ALWAYS** provide source file + qualified symbol name for every technical claim
6. **ALWAYS** verify state machines, enums, constants against actual definitions
7. **TREAT** all pre-existing docs as unverified claims requiring validation
8. **MARK** any unverifiable statement as `[UNVERIFIED - REQUIRES CODE CHECK]`
9. **USE** qualified symbol names in markers (`file.py::Class.method`), never line numbers -- line numbers break on any edit

### Documents play two roles, and only one of them is constrained above

As **evidence**, a document is an unverified claim requiring validation. Rules 2 and 7 govern that role and are not negotiable: a document never establishes a technical fact.

As a **discovery lead**, a document is a first-class input that must be collected early. A project's own index telling you that a concept named X exists and lives in module Y is not a claim about behaviour; it is a pointer telling you where to look and what to look for. Refusing to read it does not make the analysis more rigorous, it makes it blind to intent and to code paths the structure alone does not reveal.

Phase 0 collects leads. Phase 6 audits documents as evidence. Never let the second role suppress the first.

See `references/analysis-templates.md` for the full verification trust model, temporal purity principle, and documentation status markers.

## Output Usage Guide

After analysis completes, consult the right file for your task:

| Your Task | Start With | Also Check |
|-----------|-----------|------------|
| Onboarding / understanding the project | 07-final-report, 01-structure | 04-semantics |
| Writing new feature | 01-structure (Where to Add), 02-interfaces | 04-semantics |
| Fixing a bug | 03-flows, 05-risks | 01-structure |
| Refactoring | 01-structure, 04-semantics, 05-risks | 03-flows |
| Code review | 02-interfaces, 05-risks | 06-documentation |
| Updating documentation | 06-documentation, 04-semantics | 02-interfaces |

## Forbidden Files

The analysis NEVER reads or includes contents from sensitive files: `.env`, `.env.*`, `credentials.*`, `secrets.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `.npmrc`, `.pypirc`, `.netrc`, or any file containing API keys, passwords, or tokens. If encountered, note file existence only - never quote contents.

## Script Commands

All scripts live in `${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/`.

### 1. Analyze Single File

```bash
# Python
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_file.py" \
  --file src/utils/circuit_breaker.py \
  --output-format markdown

# Java
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_file.py" \
  --file src/main/java/com/example/UserService.java

# TypeScript
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_file.py" \
  --file src/services/auth.ts

# Rust
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_file.py" \
  --file src/lib.rs

# SQL / PL-SQL
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_file.py" \
  --file migrations/0042_users.sql
```

**Parameters:**
- `--file` / `-f`: Relative or absolute path to file - **REQUIRED**. Any supported extension (see Language Support table).
- `--output-format` / `-o`: Output format (json, markdown, summary) - default: summary
- `--find-usages` / `-u`: Find all usages of exported symbols - default: false

### 2. Find Usages of One Symbol

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/analyze_file.py" \
  --file src/utils/circuit_breaker.py --find-usages --symbol CircuitBreaker
```

`--symbol` restricts the usage search to a single exported symbol; the script errors cleanly if the symbol is not exported by the file.

### 3. Structural Parse Only

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/ast_parser.py" src/services/auth.ts
```

Emits the raw structural extraction (classes, functions, imports, exports) as JSON. Reports the active parser in `notes`.

---

## Documentation Maintenance Commands (Phase 6)

### 4. Scan Documentation Health

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/doc_review.py" scan \
  --path docs/ --output doc_health_report.json
```

### 5. Validate Links

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/doc_review.py" validate-links \
  --path docs/ --fix
```

### 6. Verify Against Source Code

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/doc_review.py" verify \
  --doc docs/agents/lifecycle.md --source src/agents/lifecycle.py
```

### 7. Update Navigation Indexes

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/doc_review.py" update-indexes \
  --search-index docs/00_navigation/SEARCH_INDEX.md \
  --by-domain docs/00_navigation/BY_DOMAIN.md
```

### 8. Full Documentation Maintenance

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/doc_review.py" full-maintenance \
  --path docs/ --auto-fix --output doc_health_report.json
```

Executes: scan health, validate/fix links, identify obsolete files, update indexes, generate report.

---

## Comment Quality Commands (Antirez Standards)

### 9. Analyze Comment Quality

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/rewrite_comments.py" analyze \
  src/main.py --report
```

### 10. Scan Directory for Comment Issues

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/rewrite_comments.py" scan \
  src/ --recursive --issues-only
```

### 11. Generate Comment Health Report

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/rewrite_comments.py" report \
  src/ --output comment_health.md
```

### 12. Rewrite Comments

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/rewrite_comments.py" rewrite \
  src/main.py --apply --backup
```

### 13. View Standards Reference

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/analyze/scripts/rewrite_comments.py" standards
```

---

## File Classification Criteria

| Classification | Criteria | Verification |
|---------------|----------|--------------|
| **Critical** | Handles authentication, security, encryption, sensitive data | Mandatory |
| **High-Complexity** | >300 LOC, >5 dependencies, state machines, async patterns | Mandatory |
| **Standard** | Normal business logic, data models, utilities | Recommended |
| **Utility** | Pure functions, helpers, constants | Optional |

The classifier matches patterns against raw file content (including comments and string literals), so treat its verdict as a triage signal to be confirmed by reading the file, not as ground truth.

---

## AI-Powered Semantic Analysis

### Five Layers of Understanding

| Layer | What | Who Does It |
|-------|------|-------------|
| **1. WHAT** | Classes, functions, imports | Scripts (AST) |
| **2. HOW** | Algorithm details, data flow | Claude's first pass |
| **3. WHY** | Business purpose, design decisions | Claude's deep analysis |
| **4. WHEN** | Triggers, lifecycle, concurrency | Claude's behavioral analysis |
| **5. CONSEQUENCES** | Side effects, failure modes | Claude's systems thinking |

### Pattern Recognition

| Pattern Type | Examples | Documentation Focus |
|-------------|----------|---------------------|
| **Architectural** | Repository, Service, CQRS, Event-Driven | Responsibilities, boundaries |
| **Behavioral** | State Machine, Strategy, Observer, Chain | Transitions, variations |
| **Resilience** | Circuit Breaker, Retry, Bulkhead, Timeout | Thresholds, fallbacks |
| **Data** | DTO, Value Object, Aggregate | Invariants, relationships |
| **Concurrency** | Producer-Consumer, Worker Pool | Thread safety, backpressure |

### Red Flags to Identify

```
ARCHITECTURE:
- GOD CLASS: >10 public methods or >500 LOC
- CIRCULAR DEPENDENCY: A -> B -> C -> A
- LEAKY ABSTRACTION: Implementation details in interface

RELIABILITY:
- SWALLOWED EXCEPTION: Empty catch blocks
- MISSING TIMEOUT: Network calls without timeout
- RACE CONDITION: Shared mutable state without sync

SECURITY:
- HARDCODED SECRET: Passwords, API keys in code
- SQL INJECTION: String concatenation in queries
- MISSING VALIDATION: Unsanitized user input
```

### AI Analysis Workflow

```
1. SCRIPTS RUN FIRST -> classifier.py, ast_parser.py, usage_finder.py
2. CLAUDE ANALYZES -> Read source, apply semantic questions, recognize patterns, identify red flags
3. CLAUDE DOCUMENTS -> Use template, explain WHY not just WHAT, document contracts
4. VERIFY -> Check against runtime behavior, validate with code traces
```

## Analysis Loop Workflow

```
1. CLASSIFY -> LOC, dependencies, critical patterns, assign classification
2. READ & MAP -> AST structure, classes, functions, constants, state mutations
3. DEPENDENCY CHECK -> Internal imports, external imports, external calls
4. CONTEXT ANALYSIS -> Symbol usages, importing modules, message flows
5. RUNTIME VERIFICATION (Critical/High-Complexity) -> Log analysis, flow verification
6. DOCUMENTATION -> Write the phase output file into the active run directory
```

## Best Practices

### Source Code Analysis (Phases 1-5)
1. Start with Phase 1 - foundation modules inform everything else
2. Never skip runtime verification for critical/high-complexity files
3. Keep all writes inside the active run directory until the publish step

### Documentation Maintenance (Phase 6)
1. Run scan first to understand current state
2. Fix links before content - broken links indicate structural issues
3. Verify against code before updating documentation
4. Update indexes last to reflect final state

## Team Mode Integration

The classic `/codebase-xray:analyze` command runs three subagents in two waves on a single target. For monorepos, multi-language repos, or large codebases where a single analysis context grows uncomfortable, switch to the team variant:

```
/codebase-xray:team-analyze <target>
```

The team command:
1. Auto-detects partitions (workspaces, top-level dirs, or language clusters) and asks you to confirm at a checkpoint.
2. Spawns three workers per partition in two waves (Wave 1 = Structure; Wave 2 = Behavior + Quality). Wave 2 workers read every partition's Wave 1 output, so cross-partition contracts and flows can be cited directly.
3. Synthesizes a backward-compatible `01..07.md` set inside the run directory; the publish step mirrors it to the `.deep-dive/` root, so any downstream consumer (`/senior-review:team-review`, `/codebase-mapper:map-codebase`, `/project-setup:create-claude-md`) picks it up without changes.
4. Adds `08-interconnect-map.md` produced by `codebase-xray:semantic-interconnect-mapper` on top of the consolidated set, giving a global Call Graph, Contracts, Invariants, and Integration Hot-Spots view.

### Choosing between classic and team

| Repo profile                                        | Use classic | Use team |
|-----------------------------------------------------|-------------|----------|
| Single package, < 200 files, one language           | ✓           |          |
| Monorepo (pnpm/npm/yarn/lerna/nx/turbo workspaces)  |             | ✓        |
| Multi-language (Python + TS, etc.) at top level     |             | ✓        |
| You want a global interconnection map produced in the same run |  | ✓        |
| You want `--phase N` or `--docs-only` control       | ✓           |          |

## References

- `references/analysis-templates.md` - Verification trust model, temporal purity principle, documentation status markers, comment classification, maintenance workflows
- `references/AI_ANALYSIS_METHODOLOGY.md` - Complete analysis methodology
- `references/SEMANTIC_PATTERNS.md` - Pattern recognition guide
- `references/ANTIREZ_COMMENTING_STANDARDS.md` - Comment taxonomy
- `templates/semantic_analysis.md` - AI-powered per-file analysis template
- `templates/analysis_report.md` - Module-level report template

## Resources

- **Scripts**: `scripts/` - analysis tools (Python >= 3.10 runtime, multi-language targets)
  - `ast_parser.py` - structural extraction dispatcher
  - `analyze_file.py` - per-file CLI (classification + structure + usages)
  - `classifier.py` - language-aware criticality classifier
  - `usage_finder.py` - cross-file symbol usage finder (multi-language extensions)
  - `comment_rewriter.py` - multi-language comment analysis engine
  - `rewrite_comments.py` - comment quality CLI (scan / analyze / rewrite / report)
  - `doc_review.py` - documentation maintenance (Phase 6)
  - `languages/` - per-language adapters (Python `ast`, Java/JS/TS/Rust via tree-sitter or regex, SQL/PL-SQL regex)
    - `base.py` - shared dataclasses + `LanguageAdapter` Protocol
    - `__init__.py` - extension dispatch (`detect_language`, `get_adapter`)
    - `comments.py` - per-language comment lexer (includes rustdoc post-processor)
    - `_treesitter.py` - optional tree-sitter loader with fallbacks
    - `python.py`, `java.py`, `javascript.py`, `typescript.py`, `sql.py`, `plsql.py`, `rust.py`
  - `requirements.txt` - optional dependencies (tree-sitter + tree-sitter-language-pack)
