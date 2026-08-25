# Analysis Templates and Verification Model

## Verification Trust Model

```
Layer 1: TOOL-VALIDATED
  - Automated checks: file exists, AST symbol exists, signature matches
  - Marker: [VALIDATED: file.py::ClassName.method_name @ 2025-12-20]

Layer 2: HUMAN-VERIFIED
  - Manual review: semantic correctness, behavior match
  - Marker: [VERIFIED: file.py::ClassName.method_name by @reviewer @ 2025-12-20]

Layer 3: RUNTIME-CONFIRMED
  - Log/trace evidence of actual behavior
  - Marker: [CONFIRMED: trace_id=abc123 @ 2025-12-20]

Tool validation catches STRUCTURAL issues (file moved, symbol renamed, signature changed).
Human verification ensures SEMANTIC correctness (code does what doc says).
Runtime confirmation proves BEHAVIORAL truth (system actually works this way).

ALL THREE LAYERS are required for critical documentation.

NOTE: Markers use qualified symbol names (Module::Class.method, file::function)
instead of line numbers. Line numbers shift on any edit; symbol names are stable
and survive refactoring as long as the symbol itself is not renamed.
```

## The Iron Law of Documentation

```
DOCUMENTATION = f(SOURCE_CODE) + VERIFICATION

If NOT verified_against_code(statement) -> statement is FALSE
If NOT exists_in_codebase(reference)    -> reference is FABRICATED
If NOT traceable_to_source(claim)       -> claim is SPECULATION
```

## The Temporal Purity Principle

```
Documentation = PRESENT_TENSE(current_implementation)

FORBIDDEN:
- "was/were/previously/formerly/used to"
- "deprecated since version X" -> just REMOVE it
- "changed from X to Y" -> only describe Y
- "in the old system..." -> irrelevant, delete
- inline changelogs -> use CHANGELOG.md or git

REQUIRED:
- Present tense: "The system uses..." not "The system used..."
- Current state only: Document what IS, not what WAS
- Git for archaeology: History lives in version control, not docs
```

**The Rule:**
> When you find documentation containing historical language, **DELETE IT**.
> Git blame exists for archaeology. Documentation exists for the present.

## Verification Requirements

| Documentation Type | Required Evidence |
|-------------------|-------------------|
| **Enum/State values** | Exact match with source code enum definition |
| **Function behavior** | Code path tracing, actual implementation reading |
| **Constants/Timeouts** | Variable definition in source with file:line |
| **Message formats** | Message class definition, field validation |
| **Architecture claims** | Import graph analysis, actual class relationships |
| **Flow diagrams** | Verified against runtime logs OR code path analysis |

## Documentation Verification Status

Every section of documentation MUST have one of these status markers:

- `[VERIFIED: file.py::ClassName.method_name]` - Confirmed against source code symbol
- `[VERIFIED: trace_id=xyz]` - Confirmed against runtime logs
- `[UNVERIFIED]` - Requires verification before trusting
- `[DEPRECATED]` - Code has changed, documentation outdated

Symbol reference format: `file.py::symbol` for top-level, `file.py::Class.method` for members.
Never use line numbers in markers -- they break on any file edit.

**UNVERIFIED documentation is UNTRUSTED documentation.**

## The Semantic Analysis Mandate

```
Scripts extract STRUCTURE:  "class Foo with method bar()"
Claude extracts MEANING:    "Foo implements Repository pattern for
                             caching user sessions with TTL expiration"

NEVER stop at structure. ALWAYS pursue understanding.
```

## Semantic Analysis Template

Use `templates/semantic_analysis.md` for comprehensive per-file analysis that includes:

- Executive summary (purpose, responsibility, patterns)
- Behavioral analysis (triggers, processing, side effects)
- Dependency analysis (why each dependency exists)
- Quality assessment (strengths, concerns, red flags)
- Contract documentation (full interface semantics)
- Flow tracing (primary and error paths)
- Testing implications (what must be tested)

## JSON Output Structure

```json
{
  "file": "src/utils/circuit_breaker.py",
  "classification": "critical",
  "metrics": {
    "lines_of_code": 245,
    "num_classes": 2,
    "num_functions": 8,
    "num_dependencies": 12
  },
  "structure": {
    "classes": [],
    "functions": [],
    "constants": []
  },
  "dependencies": {
    "internal": [],
    "external": [],
    "external_calls": []
  },
  "usages": [],
  "verification_required": true
}
```

## Markdown Output Format

The markdown output follows the template in `templates/analysis_report.md` and produces sections suitable for inclusion in phase deliverable documents.

## Comment Type Classification

| Type | Category | Description | Action |
|------|----------|-------------|--------|
| **function** | GOOD | API docs at function/class top | Keep/Enhance |
| **design** | GOOD | File-level algorithm explanations | Keep |
| **why** | GOOD | Explains reasoning behind code | Keep |
| **teacher** | GOOD | Educates about domain concepts | Keep |
| **checklist** | GOOD | Reminds of coordinated changes | Keep |
| **guide** | GOOD | Section dividers, structure | Keep sparingly |
| **trivial** | BAD | Restates what code says | Delete |
| **debt** | BAD | TODO/FIXME without plan | Rewrite/Resolve |
| **backup** | BAD | Commented-out code | Delete |

## Comment Quality Workflow

```
1. SCAN
   - Run: rewrite_comments.py scan <dir> --recursive
   - Review files with most issues
   - Generate: rewrite_comments.py report <dir> --output report.md

2. TRIAGE
   - Identify high-priority files (critical modules)
   - Focus on DEBT comments (convert to issues or design docs)
   - Plan bulk TRIVIAL/BACKUP deletions

3. REWRITE
   - Run: rewrite_comments.py rewrite <file> --apply --backup
   - Review changes in diff
   - Verify no functional changes

4. VERIFY
   - Run tests to confirm no breakage
   - Re-scan to confirm improvements
   - Update comment_health.md report
```

## Documentation Maintenance Workflow

When invoking Phase 6 documentation maintenance, follow this sequence:

```
1. PLANNING
   - Run: doc_review.py scan --path docs/
   - Review health report
   - Identify priority fixes (broken links, obsolete files)
   - Create todo list with specific actions

2. EXECUTION (in batches)
   - Batch 1: Fix broken links
     - Run: doc_review.py validate-links --fix
   - Batch 2: Verify critical docs against source
     - Run: doc_review.py verify --doc <file> --source <code>
   - Batch 3: Delete obsolete files
     - Manual review + deletion
   - Batch 4: Update navigation indexes
     - Run: doc_review.py update-indexes
   - Batch 5: Update timestamps
     - Set last_updated on verified files

3. VERIFICATION
   - Run: doc_review.py scan (confirm improvements)
   - Run: doc_review.py validate-links (confirm zero broken)
   - Generate final doc_health_report.json
```
