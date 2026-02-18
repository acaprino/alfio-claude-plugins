# Python Refactor Skill

A comprehensive Agent Skill for systematic code refactoring that prioritizes human readability and maintainability while preserving correctness.

## Purpose

Transform complex, hard-to-understand Python code into clear, well-documented, maintainable code through systematic application of proven refactoring patterns.

## When to Use

- User requests "readable", "maintainable", or "clean" code refactoring
- Code review flags comprehension or maintainability issues
- Legacy code modernization tasks
- Educational contexts or team onboarding scenarios
- Code complexity metrics exceed reasonable thresholds

## Core Capabilities

### 4-Phase Refactoring Workflow

1. **Analysis** - Scan code for readability issues and measure baseline metrics
2. **Planning** - Create risk-assessed refactoring plan with clear sequencing
3. **Execution** - Apply patterns incrementally with continuous test validation
4. **Validation** - Verify improvements and check for performance regression

### Refactoring Patterns

- **Complexity Reduction**: Guard clauses, method extraction, conditional simplification, dictionary dispatch
- **Naming Improvements**: Meaningful variables, boolean conventions, named constants
- **Documentation**: Comprehensive docstrings, module documentation, type hints
- **Structure**: Separation of concerns, consistent abstraction levels, layered architecture
- **OOP Transformation**: Global state encapsulation, dependency injection, domain models

### Anti-Pattern Detection

Automatically identifies 16+ common anti-patterns across three priority levels:
- **Critical**: Script-like procedural code, God Objects/Classes
- **High Priority**: Complex nesting, god functions, magic numbers, cryptic names
- **Medium Priority**: Code duplication, primitive obsession, long parameter lists

### Tooling

**Primary Stack (recommended):** Ruff + Complexipy (both Rust-based, very fast)
- Ruff: 800+ lint rules, replaces flake8 + plugins
- Complexipy: Dedicated cognitive complexity analysis

**Alternative:** Flake8 with curated plugin set (for projects already using it). See `references/flake8_plugins_guide.md`.

### Validation Scripts

- `measure_complexity.py` - AST-based cyclomatic complexity, function length, nesting depth
- `check_documentation.py` - Docstring and type hint coverage
- `compare_metrics.py` - Before/after metrics comparison
- `benchmark_changes.py` - Performance regression testing
- `analyze_with_flake8.py` - Comprehensive flake8 analysis with plugin support
- `compare_flake8_reports.py` - Flake8 before/after comparison
- `analyze_multi_metrics.py` - Combined cognitive + cyclomatic + maintainability report

## Skill Contents

```
python-refactor/
├── SKILL.md                              # Main skill instructions and workflow
├── README.md                             # This file
├── scripts/                              # Executable validation tools
│   ├── measure_complexity.py             # AST-based complexity analysis
│   ├── check_documentation.py            # Docstring and type hint coverage
│   ├── compare_metrics.py               # Before/after metrics comparison
│   ├── benchmark_changes.py             # Performance regression testing
│   ├── analyze_with_flake8.py           # Comprehensive flake8 analysis
│   ├── compare_flake8_reports.py        # Flake8 before/after comparison
│   └── analyze_multi_metrics.py         # Combined multi-metric analysis
├── references/                           # Reference documentation
│   ├── patterns.md                       # Refactoring patterns with examples
│   ├── anti-patterns.md                 # Anti-pattern catalog
│   ├── oop_principles.md               # SOLID principles and OOP guide
│   ├── cognitive_complexity_guide.md    # Cognitive complexity rules and tools
│   ├── REGRESSION_PREVENTION.md         # Mandatory regression prevention guide
│   ├── flake8_plugins_guide.md          # Flake8 plugin ecosystem
│   └── examples/                         # Complete before/after examples
│       ├── python_complexity_reduction.md
│       ├── typescript_naming_improvements.md
│       └── script_to_oop_transformation.md
└── assets/                               # Output templates and configurations
    ├── .flake8                           # Flake8 configuration template
    ├── pyproject.toml                    # Ruff + Complexipy configuration template
    └── templates/
        ├── analysis_template.md          # Pre-refactoring analysis format
        ├── summary_template.md           # Post-refactoring summary format
        └── flake8_report_template.md     # Flake8 analysis report format
```

## Cross-Language Patterns

While all tooling and scripts are Python-specific, the refactoring patterns (guard clauses, naming conventions, extract method, etc.) apply to any language. The `typescript_naming_improvements.md` example demonstrates naming patterns in a TypeScript context.

## Key Features

### Objective Metrics

All improvements measured with concrete metrics:
- Cyclomatic complexity targets (<10 per function)
- Cognitive complexity targets (<15 per function)
- Function length guidelines (<30 lines)
- Nesting depth limits (<=3 levels)
- Documentation coverage (>80% for public APIs)
- Type hint coverage (>90% for public functions)

### Risk Management

- Three-level risk assessment (Low/Medium/High)
- Performance regression thresholds (10% default)
- Safety-by-design migration protocol for destructive changes
- Test validation at each step
- Clear indication when human review is needed

### Composability

Integrates with other skills:
- **python-testing-patterns**: Ensure test coverage before/after
- **python-performance-optimization**: Deep profiling validation
- **async-python-patterns**: Async code restructuring
- **uv-package-manager**: Tool execution via `uv run`

## Success Criteria

Refactoring is successful when:
- All existing tests pass (zero regressions)
- Complexity metrics improved (documented)
- No performance regression >10%
- Documentation coverage improved
- Code is easier for humans to understand
- No new security vulnerabilities
- Changes are atomic and well-documented

## Limitations

- Cannot change algorithmic complexity (O(n^2) to O(n log n))
- Cannot add domain knowledge not in existing code
- Cannot guarantee correctness without comprehensive tests
- Performance-critical code should be profiled first

## Version

**Version:** 1.3.0
**Last Updated:** 2026
**Compatibility:** Claude Code, Claude.ai, Claude API

**Changelog:**
- **v1.3.0**: Major trim of SKILL.md (1440 -> ~330 lines), translated Italian to English, established ruff+complexipy as primary tooling, softened OOP mandate, added analyze_multi_metrics.py reference, updated file tree
- **v1.2.0**: Added OOP transformation patterns, regression prevention guide, cognitive complexity guide, complexipy integration, SOLID principles reference
- **v1.1.0**: Added comprehensive flake8 integration with plugin support, before/after comparison, and HTML/JSON reports
- **v1.0.0**: Initial release with complexity analysis, documentation checking, and refactoring patterns
