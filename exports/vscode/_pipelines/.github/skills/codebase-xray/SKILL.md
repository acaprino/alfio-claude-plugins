---
name: codebase-xray
description: >
  AI-powered systematic codebase analysis. Combines mechanical structure extraction with semantic understanding to produce ground-truth documentation capturing WHAT, WHY, HOW, and CONSEQUENCES. Multi-language: Python, Java, JavaScript, TypeScript, SQL, PL/SQL, Rust. Includes pattern recognition, red flag detection, flow tracing, quality assessment, and concurrent analysis runs. Use when encountering unfamiliar code, before major refactoring, when pre-review technical context is needed, or when documentation is stale or missing. Do not use for human-readable narrative docs, public-facing READMEs, or code review verdicts.
user-invocable: false
license: MIT
compatibility: Requires Python >= 3.10. Optional tree-sitter for higher-fidelity Java, JavaScript, TypeScript, and Rust parsing.
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: codebase-xray
  version: "3.1.0"
---

# Codebase X-Ray Analysis Skill

## Overview

This skill combines **mechanical structure extraction** with **semantic understanding** to produce comprehensive codebase documentation. Unlike simple AST parsing, this skill captures:

- **WHAT** the code does (structure, functions, classes)
- **WHY** it exists (business purpose, design decisions)
- **HOW** it integrates (dependencies, contracts, flows)
- **CONSEQUENCES** of changes (side effects, failure modes)

## Resolving the skill directory

Every script path below is written as `$XRAY/...`. `$XRAY` is the directory containing this `SKILL.md`. Resolve it **once** at the start of a session with `#execute/runInTerminal`, then substitute the literal path into every later command (terminal state does not persist between tool calls):

```bash
for d in .github/skills/codebase-xray .agents/skills/codebase-xray \
         .claude/skills/codebase-xray "$HOME/.copilot/skills/codebase-xray"; do
  [ -d "$d" ] && echo "XRAY=$d" && break
done
```

On a Windows shell without a POSIX layer, check the same four paths with `#search/listDirectory` and take the first that exists.

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
pip install -r "$XRAY/scripts/requirements.txt"
# or
uv pip install -r "$XRAY/scripts/requirements.txt"
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

**Semantic Analysis (the agent):**
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

One entry point: the `/xray-team-analyze <target> [flags]` prompt file, which runs on the `xray-orchestrator` custom agent. Selecting **xray-orchestrator** from the agents dropdown and describing the target reaches the same pipeline. The workflow itself is specified in `references/workflow.md`.

It partitions the target (workspaces, top-level dirs, or language clusters), dispatches workers per partition across two waves, consolidates the results, and maps the contract surface. Small single-package repos are covered by the single-partition fallback, so there is no separate lightweight command.

This skill is not exposed as its own slash command (`user-invocable: false`). It still loads automatically when a prompt matches the description above, which is how a plain request such as "analyze this codebase and tell me what it does" reaches the pipeline.

State is managed automatically under `.deep-dive/` using the concurrent runs model below. If the prompt file and agents are not installed, read `references/workflow.md` and execute it inline.

## Concurrent Runs Model

Multiple analyses can run at the same time (different targets, different sessions, or a re-analysis while an older one is still in flight). Every analysis is an isolated **run**:

```
.deep-dive/
├── runs.json                          # registry: active runs + latest completed
├── runs/
│   └── <run-id>/                      # one directory per analysis run
│       ├── state.json                 # per-run phase tracking
│       ├── 01-structure.md .. 07-final-report.md
│       ├── 08-interconnect-map.md     # contracts, invariants, integration hot-spots
│       └── partitions/<name>/...      # per-partition worker output
├── state.json                         # mirror of the latest published run
└── 01-structure.md .. 08-interconnect-map.md   # mirror of the latest published run
```

Rules:

1. **Run identity.** `run-id` = slug of the target path + `-YYYYMMDD-HHMMSS`, or the value of `--run-name <name>` (normalized to `[a-z0-9-]`; on collision append `-2`, `-3`, ...).
2. **Isolation.** A run writes ONLY inside `.deep-dive/runs/<run-id>/` while in progress. Concurrent runs never share files.
3. **Registry.** `runs.json` holds `{"schema": 2, "active": [{run_id, target, mode, started_at}], "latest_completed": "<run-id>"}`. The orchestrator registers its run at start and updates the registry at completion. Read-modify-write it; never blindly overwrite entries you did not create.
4. **Publish step.** On successful completion, the orchestrator copies the run's `01..0N.md` files and `state.json` to the `.deep-dive/` root and sets `latest_completed`. The root mirror is the **downstream contract**: any consumer keeps reading `.deep-dive/01-structure.md` etc. unchanged. If two runs finish concurrently, the last one to publish owns the root mirror; both remain intact under `runs/`.
5. **Resume.** On invocation, the orchestrator reads `runs.json`: active runs are offered for resume; completed runs can be archived or re-published. A root `state.json` containing `current_phase` with no `runs.json` present is a pre-runs legacy layout: offer to migrate it into `runs/legacy-<date>/` before starting.

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
9. **USE** qualified symbol names in markers (`file.py::Class.method`), never line numbers. Line numbers break on any edit.

See `references/analysis-templates.md` for the full verification trust model, temporal purity principle, and documentation status markers.

## Output Usage Guide

After analysis completes, consult the right file for your task:

| Your Task | Start With | Also Check |
|-----------|-----------|------------|
| Onboarding / understanding the project | 07-final-report, 01-structure | 04-semantics |
| Writing new feature | 01-structure (Where to Add), 02-interfaces | 04-semantics |
| Fixing a bug | 03-flows, 05-risks | 01-structure |
| Refactoring | 01-structure, 04-semantics, 05-risks | 03-flows |
| Code review | 08-interconnect-map, 02-interfaces, 05-risks | 06-documentation |
| Updating documentation | 06-documentation, 04-semantics | 02-interfaces |
| Assessing change blast radius | 08-interconnect-map | 03-flows, 02-interfaces |

## Forbidden Files

The analysis NEVER reads or includes contents from sensitive files: `.env`, `.env.*`, `credentials.*`, `secrets.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `.npmrc`, `.pypirc`, `.netrc`, or any file containing API keys, passwords, or tokens. If encountered, note file existence only. Never quote contents.

When agent hooks are enabled, `hooks/xray_guard.py` enforces the unambiguous entries of this list at the tool layer. The broader heuristics (`*secret*`, `*credential*`) stay your judgment call, because a module named `secrets_manager.py` is a legitimate analysis target. See "Optional: tool-layer guard" in the bundle README.

## Script Commands

All scripts live in `$XRAY/scripts/` (see "Resolving the skill directory" above). Run them with `#execute/runInTerminal`.

### 1. Analyze Single File

```bash
python "$XRAY/scripts/analyze_file.py" --file src/utils/circuit_breaker.py --output-format markdown
python "$XRAY/scripts/analyze_file.py" --file src/main/java/com/example/UserService.java
python "$XRAY/scripts/analyze_file.py" --file src/services/auth.ts
python "$XRAY/scripts/analyze_file.py" --file src/lib.rs
python "$XRAY/scripts/analyze_file.py" --file migrations/0042_users.sql
```

**Parameters:**
- `--file` / `-f`: Relative or absolute path to file. **REQUIRED**. Any supported extension (see Language Support table).
- `--output-format` / `-o`: Output format (json, markdown, summary). Default: summary
- `--find-usages` / `-u`: Find all usages of exported symbols. Default: false

### 2. Find Usages of One Symbol

```bash
python "$XRAY/scripts/analyze_file.py" \
  --file src/utils/circuit_breaker.py --find-usages --symbol CircuitBreaker
```

`--symbol` restricts the usage search to a single exported symbol; the script errors cleanly if the symbol is not exported by the file.

### 3. Structural Parse Only

```bash
python "$XRAY/scripts/ast_parser.py" src/services/auth.ts
```

Emits the raw structural extraction (classes, functions, imports, exports) as JSON. Reports the active parser in `notes`.

---

## Documentation Maintenance Commands (Phase 6)

```bash
# Scan documentation health
python "$XRAY/scripts/doc_review.py" scan --path docs/ --output doc_health_report.json

# Validate (and fix) links
python "$XRAY/scripts/doc_review.py" validate-links --path docs/ --fix

# Verify a doc against its source
python "$XRAY/scripts/doc_review.py" verify --doc docs/agents/lifecycle.md --source src/agents/lifecycle.py

# Update navigation indexes
python "$XRAY/scripts/doc_review.py" update-indexes \
  --search-index docs/00_navigation/SEARCH_INDEX.md \
  --by-domain docs/00_navigation/BY_DOMAIN.md

# Full maintenance: scan, fix links, flag obsolete files, update indexes, report
python "$XRAY/scripts/doc_review.py" full-maintenance --path docs/ --auto-fix --output doc_health_report.json
```

---

## Comment Quality Commands (Antirez Standards)

```bash
python "$XRAY/scripts/rewrite_comments.py" analyze src/main.py --report
python "$XRAY/scripts/rewrite_comments.py" scan src/ --recursive --issues-only
python "$XRAY/scripts/rewrite_comments.py" report src/ --output comment_health.md
python "$XRAY/scripts/rewrite_comments.py" rewrite src/main.py --apply --backup
python "$XRAY/scripts/rewrite_comments.py" standards
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

## Semantic Analysis

### Five Layers of Understanding

| Layer | What | Who Does It |
|-------|------|-------------|
| **1. WHAT** | Classes, functions, imports | Scripts (AST) |
| **2. HOW** | Algorithm details, data flow | Agent's first pass |
| **3. WHY** | Business purpose, design decisions | Agent's deep analysis |
| **4. WHEN** | Triggers, lifecycle, concurrency | Agent's behavioral analysis |
| **5. CONSEQUENCES** | Side effects, failure modes | Agent's systems thinking |

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

### Analysis Workflow

```
1. SCRIPTS RUN FIRST -> classifier.py, ast_parser.py, usage_finder.py
2. AGENT ANALYZES   -> Read source, apply semantic questions, recognize patterns, identify red flags
3. AGENT DOCUMENTS  -> Use template, explain WHY not just WHAT, document contracts
4. VERIFY           -> Check against runtime behavior, validate with code traces
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
1. Start with Phase 1: foundation modules inform everything else
2. Never skip runtime verification for critical/high-complexity files
3. Keep all writes inside the active run directory until the publish step

### Documentation Maintenance (Phase 6)
1. Run scan first to understand current state
2. Fix links before content: broken links indicate structural issues
3. Verify against code before updating documentation
4. Update indexes last to reflect final state

## Pipeline shape

| Stage | Agent | Output |
|---|---|---|
| Phase 0 | `xray-orchestrator` | partition detection + checkpoint |
| Phase 1 Wave 1 | `xray-structure-worker` (one per partition) | `01-structure.md`, `02-interfaces.md` |
| Phase 1 Wave 2 | `xray-behavior-worker` + `xray-quality-worker` (one pair per partition) | `03-flows.md`, `04-semantics.md`, `05-risks.md`, `06-documentation.md` |
| Phase 2 | `xray-synthesizer` | consolidated `01..07.md` |
| Phase 3 | `xray-interconnect-mapper` | `08-interconnect-map.md` |
| Phase 4 | `xray-orchestrator` | publish to `.deep-dive/` root, action plan, next steps |

Each worker's phase spec and output template live in its agent definition under `.github/agents/`. Read the agent file when you need a template, including when executing a role inline because subagent dispatch is unavailable.

## References Library

Read these on demand. Do not preload them all.

- `references/workflow.md`: the complete pipeline. Flags, partition detection, wave barriers, dispatch prompts, synthesis, interconnect map, publish step, resume logic, next-steps menu
- `references/analysis-templates.md`: verification trust model, temporal purity principle, documentation status markers, comment classification, maintenance workflows
- `references/AI_ANALYSIS_METHODOLOGY.md`: complete analysis methodology
- `references/SEMANTIC_PATTERNS.md`: pattern recognition guide
- `references/ANTIREZ_COMMENTING_STANDARDS.md`: comment taxonomy
- `assets/semantic_analysis.md`: per-file analysis template
- `assets/analysis_report.md`: module-level report template

## Resources

`scripts/` holds the analysis tools (Python >= 3.10 runtime, multi-language targets):

- `ast_parser.py`: structural extraction dispatcher
- `analyze_file.py`: per-file CLI (classification + structure + usages)
- `classifier.py`: language-aware criticality classifier
- `usage_finder.py`: cross-file symbol usage finder (multi-language extensions)
- `comment_rewriter.py`: multi-language comment analysis engine
- `rewrite_comments.py`: comment quality CLI (scan / analyze / rewrite / report)
- `doc_review.py`: documentation maintenance (Phase 6)
- `languages/`: per-language adapters (Python `ast`, Java/JS/TS/Rust via tree-sitter or regex, SQL/PL-SQL regex)
- `requirements.txt`: optional dependencies (tree-sitter + tree-sitter-language-pack)

`hooks/xray_guard.py` is the optional `PreToolUse` guard described in the bundle README.
