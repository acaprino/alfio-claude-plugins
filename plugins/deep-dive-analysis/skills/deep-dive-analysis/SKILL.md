---
name: deep-dive-analysis
description: >
  AI-powered systematic codebase analysis. Combines structure extraction with semantic understanding to produce documentation capturing WHAT, WHY, HOW, and CONSEQUENCES. Multi-language: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust. Includes pattern recognition, red flag detection, flow tracing, and quality assessment.
  TRIGGER WHEN: encountering unfamiliar code, before major refactoring, or when documentation is stale or missing
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

# Deep Dive Analysis Skill

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

The scripts are designed to work **out of the box** with just the Python stdlib. Tree-sitter is optional and improves accuracy for Java / JavaScript / TypeScript:

```bash
# Optional: install for higher-fidelity parsing
pip install -r scripts/requirements.txt
# or
uv pip install -r scripts/requirements.txt
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
- Track analysis progress
- Classify files by criticality

**Semantic Analysis (Claude AI):**
- Recognize architectural and design patterns
- Identify red flags and anti-patterns
- Trace data and control flows
- Document contracts and invariants
- Assess quality and maintainability

**Documentation Maintenance:**
- Review and maintain documentation (Phase 8)
- Fix broken links and update navigation indexes
- Analyze and rewrite code comments (antirez standards)

**Use this skill when:**
- Analyzing a codebase you're unfamiliar with
- Generating documentation that explains WHY, not just WHAT
- Identifying architectural patterns and anti-patterns
- Performing code review with semantic understanding
- Onboarding to a new project

## Prerequisites

This skill is invoked by the `/deep-dive-analysis` command. The command creates and manages state automatically in `.deep-dive/` under the target directory:

1. **`.deep-dive/state.json`** -- phase tracking (auto-created by the command)
2. **`.deep-dive/<phase-number>-<name>.md`** -- per-phase output documents

The legacy standalone flow using `analysis_progress.json` and `DEEP_DIVE_PLAN.md` at project root is no longer the primary path -- prefer invoking `/deep-dive-analysis <target>`.

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

## Available Commands

### 1. Analyze Single File

```bash
# Python
python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --file src/utils/circuit_breaker.py \
  --output-format markdown

# Java
python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --file src/main/java/com/example/UserService.java

# TypeScript
python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --file src/services/auth.ts

# SQL / PL-SQL
python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --file migrations/0042_users.sql

python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --file packages/user_pkg.pkb
```

**Parameters:**
- `--file` / `-f`: Relative path to file - **REQUIRED**. Any supported extension (see Language Support table).
- `--output-format` / `-o`: Output format (json, markdown, summary) - default: summary
- `--find-usages` / `-u`: Find all usages of exported symbols - default: false
- `--update-progress` / `-p`: Update analysis_progress.json - default: false

### 2. Check Progress

```bash
python .claude/skills/deep-dive-analysis/scripts/check_progress.py \
  --phase 1 --status pending
```

### 3. Find Usages

```bash
python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --symbol CircuitBreaker --file src/utils/circuit_breaker.py
```

### 4. Generate Phase Report

```bash
python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --phase 1 --output-format markdown --output-file docs/01_domains/COMMON_LIBRARY.md
```

---

## Phase 8: Documentation Review Commands

### 5. Scan Documentation Health

```bash
python .claude/skills/deep-dive-analysis/scripts/doc_review.py scan \
  --path docs/ --output doc_health_report.json
```

### 6. Validate Links

```bash
python .claude/skills/deep-dive-analysis/scripts/doc_review.py validate-links \
  --path docs/ --fix
```

### 7. Verify Against Source Code

```bash
python .claude/skills/deep-dive-analysis/scripts/doc_review.py verify \
  --doc docs/agents/lifecycle.md --source src/agents/lifecycle.py
```

### 8. Update Navigation Indexes

```bash
python .claude/skills/deep-dive-analysis/scripts/doc_review.py update-indexes \
  --search-index docs/00_navigation/SEARCH_INDEX.md \
  --by-domain docs/00_navigation/BY_DOMAIN.md
```

### 9. Full Documentation Maintenance

```bash
python .claude/skills/deep-dive-analysis/scripts/doc_review.py full-maintenance \
  --path docs/ --auto-fix --output doc_health_report.json
```

Executes: scan health, validate/fix links, identify obsolete files, update indexes, generate report.

---

## Comment Quality Commands (Antirez Standards)

### 10. Analyze Comment Quality

```bash
python .claude/skills/deep-dive-analysis/scripts/rewrite_comments.py analyze \
  src/main.py --report
```

### 11. Scan Directory for Comment Issues

```bash
python .claude/skills/deep-dive-analysis/scripts/rewrite_comments.py scan \
  src/ --recursive --issues-only
```

### 12. Generate Comment Health Report

```bash
python .claude/skills/deep-dive-analysis/scripts/rewrite_comments.py report \
  src/ --output comment_health.md
```

### 13. Rewrite Comments

```bash
python .claude/skills/deep-dive-analysis/scripts/rewrite_comments.py rewrite \
  src/main.py --apply --backup
```

### 14. View Standards Reference

```bash
python .claude/skills/deep-dive-analysis/scripts/rewrite_comments.py standards
```

---

## File Classification Criteria

| Classification | Criteria | Verification |
|---------------|----------|--------------|
| **Critical** | Handles authentication, security, encryption, sensitive data | Mandatory |
| **High-Complexity** | >300 LOC, >5 dependencies, state machines, async patterns | Mandatory |
| **Standard** | Normal business logic, data models, utilities | Recommended |
| **Utility** | Pure functions, helpers, constants | Optional |

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
6. DOCUMENTATION -> Update progress, generate report, cross-reference
```

## Best Practices

### Source Code Analysis (Phases 1-7)
1. Start with Phase 1 - foundation modules inform everything else
2. Track progress with `--update-progress`
3. Never skip runtime verification for critical/high-complexity files
4. Cross-reference with CONTEXT.md after analysis

### Documentation Maintenance (Phase 8)
1. Run scan first to understand current state
2. Fix links before content - broken links indicate structural issues
3. Verify against code before updating documentation
4. Update indexes last to reflect final state

## Team Mode Integration

The classic `/deep-dive-analysis` command runs three subagents in two waves on a single target. For monorepos, multi-language repos, or large codebases where a single deep-dive's context window grows uncomfortable, switch to the team variant:

```
/deep-dive-analysis:team-deep-dive <target>
```

The team command:
1. Auto-detects partitions (workspaces, top-level dirs, or language clusters) and asks you to confirm at a checkpoint.
2. Spawns three deep-dive workers per partition in two waves (Wave 1 = Structure; Wave 2 = Behavior + Quality). Wave 2 workers read every partition's Wave 1 output, so cross-partition contracts and flows can be cited directly.
3. Synthesizes a backward-compatible `.deep-dive/01..07.md` set that any downstream consumer (`/senior-review:team-review`, `/codebase-mapper:map-codebase`, `/project-setup:create-claude-md`) can pick up without changes.
4. Adds `.deep-dive/08-interconnect-map.md` produced by `senior-review:semantic-interconnect-mapper` on top of the consolidated set, giving a global Call Graph, Contracts, Invariants, and Integration Hot-Spots view.

### Choosing between classic and team

| Repo profile                                        | Use classic | Use team |
|-----------------------------------------------------|-------------|----------|
| Single package, < 200 files, one language           | ✓           |          |
| Monorepo (pnpm/npm/yarn/lerna/nx/turbo workspaces)  |             | ✓        |
| Multi-language (Python + TS, etc.) at top level     |             | ✓        |
| You want a global interconnection map produced in the same run |  | ✓        |
| You want `--phase N` or `--docs-only` control       | ✓           |          |

### Output layout (team mode)

```
.deep-dive/
├── state.json
├── partitions/
│   └── <name>/{01..06}.md          ← per-partition reports
├── 01-structure.md .. 07-final-report.md   ← consolidated (compat with classic)
└── 08-interconnect-map.md          ← new, global cross-partition map
```

See `docs/plans/2026-05-20-deep-dive-team-mode-design.md` for the full architecture.

## References

- `references/analysis-templates.md` - Verification trust model, temporal purity principle, documentation status markers, comment classification, maintenance workflows
- `references/AI_ANALYSIS_METHODOLOGY.md` - Complete analysis methodology
- `references/SEMANTIC_PATTERNS.md` - Pattern recognition guide
- `references/ANTIREZ_COMMENTING_STANDARDS.md` - Comment taxonomy
- `references/DEEP_DIVE_PLAN.md` - Master analysis plan with all phase definitions
- `templates/semantic_analysis.md` - AI-powered per-file analysis template
- `templates/analysis_report.md` - Module-level report template

## Resources

- **Scripts**: `scripts/` - analysis tools (Python runtime, multi-language targets)
  - `ast_parser.py` - structural extraction dispatcher (Phases 1-7)
  - `analyze_file.py` - per-file CLI (classification + structure + usages)
  - `classifier.py` - language-aware criticality classifier
  - `usage_finder.py` - cross-file symbol usage finder (multi-language extensions)
  - `comment_rewriter.py` - multi-language comment analysis engine
  - `rewrite_comments.py` - comment quality CLI (scan / analyze / rewrite / report)
  - `doc_review.py` - documentation maintenance (Phase 8)
  - `check_progress.py` / `progress_tracker.py` - phase progress tracking
  - `languages/` - per-language adapters (Python `ast`, Java/JS/TS/Rust via tree-sitter or regex, SQL/PL-SQL regex)
    - `base.py` - shared dataclasses + `LanguageAdapter` Protocol
    - `__init__.py` - extension dispatch (`detect_language`, `get_adapter`)
    - `comments.py` - per-language comment lexer (includes rustdoc post-processor)
    - `_treesitter.py` - optional tree-sitter loader with fallbacks
    - `python.py`, `java.py`, `javascript.py`, `typescript.py`, `sql.py`, `plsql.py`, `rust.py`
  - `requirements.txt` - optional dependencies (tree-sitter + language-pack, click)
