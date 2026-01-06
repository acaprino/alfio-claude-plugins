# Python Refactor Skill

A comprehensive Agent Skill for systematic code refactoring that prioritizes human readability and maintainability while preserving correctness.

## Purpose

Transform complex, hard-to-understand code into clear, well-documented, maintainable code through systematic application of proven refactoring patterns.

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

- **Complexity Reduction**: Guard clauses, method extraction, conditional simplification
- **Naming Improvements**: Meaningful variables, boolean conventions, named constants
- **Documentation**: Comprehensive docstrings, module documentation, type hints
- **Structure**: Separation of concerns, consistent abstraction levels, layered architecture

### Anti-Pattern Detection

Automatically identifies 16 common anti-patterns across three priority levels:
- **High Priority**: Complex nesting, god functions, magic numbers, cryptic names
- **Medium Priority**: Code duplication, god classes, primitive obsession
- **Low Priority**: Inconsistent naming, redundant comments, unused code

### Validation Framework

Includes executable Python scripts for objective metrics:
- `measure_complexity.py` - Cyclomatic complexity, function length, nesting depth
- `check_documentation.py` - Docstring and type hint coverage
- `compare_metrics.py` - Before/after comparison with percentage improvements
- `benchmark_changes.py` - Performance regression detection
- **`analyze_with_flake8.py`** - Comprehensive code quality analysis with plugin support
- **`compare_flake8_reports.py`** - Before/after flake8 comparison with detailed improvements

### Flake8 Integration

Three-tier system with **16 curated plugins** optimized for human-readable code:

**ESSENTIAL (5 plugins - Highest Impact):**
- **flake8-bugbear** - Finds likely bugs and design problems
- **flake8-simplify** - Suggests simpler, clearer code
- **flake8-cognitive-complexity** - Measures true cognitive load
- **pep8-naming** - Enforces clear naming conventions
- **flake8-docstrings** - Ensures documentation

**RECOMMENDED (5 plugins - Strong Impact):**
- **flake8-comprehensions** - Cleaner comprehensions
- **flake8-expression-complexity** - Prevents complex expressions
- **flake8-functions** - Simpler function signatures
- **flake8-variables-names** - Better variable naming
- **tryceratops** - Clean exception handling

**OPTIONAL (6 plugins - Nice to Have):**
- **flake8-builtins** - Prevents shadowing built-ins
- **flake8-eradicate** - Finds commented-out code
- **flake8-unused-arguments** - Flags unused parameters
- **flake8-annotations** - Validates type hints
- **pydoclint** - Complete docstrings
- **flake8-spellcheck** - Catches typos

**Features:**
- Generates HTML/JSON reports for tracking progress
- Compares before/after to quantify improvements
- Categorizes issues by severity (high/medium/low)
- Provides installation guidance by priority

## Skill Contents

```
python-refactor/
├── SKILL.md                     # Main skill instructions and workflow
├── README.md                    # This file
├── scripts/                     # Executable validation tools
│   ├── measure_complexity.py          # AST-based complexity analysis
│   ├── check_documentation.py         # Docstring and type hint coverage
│   ├── compare_metrics.py             # Before/after metrics comparison
│   ├── benchmark_changes.py           # Performance regression testing
│   ├── analyze_with_flake8.py         # Comprehensive flake8 analysis
│   └── compare_flake8_reports.py      # Flake8 before/after comparison
├── references/                  # Reference documentation
│   ├── patterns.md              # Detailed refactoring patterns with examples
│   ├── anti-patterns.md         # Anti-pattern catalog with detection criteria
│   └── examples/                # Complete before/after examples
│       ├── python_complexity_reduction.md
│       └── typescript_naming_improvements.md
└── assets/                      # Output templates and configurations
    ├── .flake8                  # Flake8 configuration template
    └── templates/
        ├── analysis_template.md      # Pre-refactoring analysis format
        ├── summary_template.md       # Post-refactoring summary format
        └── flake8_report_template.md # Flake8 analysis report format
```

## Language Support

### Primary Support
- **Python**: Full support with complexity analysis, type hints, docstrings
- **TypeScript/JavaScript**: Full support with type safety, modern patterns

### Guidelines Included
- **Java**: Interfaces, streams, optional handling
- **Go**: Error handling, defer patterns, naming conventions

## Key Features

### Objective Metrics

All improvements measured with concrete metrics:
- Cyclomatic complexity targets (<10 per function)
- Function length guidelines (<30 lines)
- Nesting depth limits (≤3 levels)
- Documentation coverage (>80% for public APIs)
- Type hint coverage (>90% for public functions)

### Risk Management

- Three-level risk assessment (Low/Medium/High)
- Performance regression thresholds (10% default)
- Test validation at each step
- Clear indication when human review is needed

### Composability

Integrates with other skills:
- **Testing skills**: Ensure test coverage before/after
- **Performance profiling**: Validate no degradation
- **Security auditing**: Check for new vulnerabilities

## Example Usage

### Basic Refactoring

```python
# User request: "Refactor this function for readability"
# Skill applies:
# 1. Analyzes current complexity (e.g., complexity: 18, nesting: 5)
# 2. Plans incremental improvements (guard clauses, method extraction)
# 3. Executes changes with test validation
# 4. Produces summary showing 78% complexity reduction
```

### Metrics-Driven Refactoring

```bash
# Analyze before refactoring
python scripts/measure_complexity.py legacy_code.py

# Skill performs refactoring following patterns.md

# Compare improvements
python scripts/compare_metrics.py legacy_code.py refactored_code.py

# Verify no performance regression
python scripts/benchmark_changes.py legacy_code.py refactored_code.py tests.py
```

## Success Criteria

Refactoring is successful when:
- ✓ All existing tests pass
- ✓ Complexity metrics improved (documented)
- ✓ No performance regression >10%
- ✓ Documentation coverage improved
- ✓ Code is easier for humans to understand
- ✓ No new security vulnerabilities
- ✓ Changes are atomic and well-documented

## Output Format

Produces structured, consistent output:

### Analysis Phase
- Current metrics vs targets
- Prioritized issue list with risk assessment
- Recommended refactoring plan with time estimates

### Summary Phase
- Detailed change descriptions with rationale
- Before/after metrics comparison table
- Test and performance validation results
- Risk assessment and review recommendations

## Limitations

**When NOT to Use:**
- Performance-critical code needing optimization (profile first)
- Code scheduled for deletion
- External dependencies (contribute upstream instead)
- Already-optimal algorithms where clarity hurts performance

**Cannot Do:**
- Change algorithmic complexity (O(n²) → O(n log n))
- Add domain knowledge not in existing code
- Guarantee correctness without comprehensive tests

## Installation

This skill is ready to use with Claude Code, Claude.ai, or Claude API. Simply load the skill and it will be available when refactoring tasks are requested.

## Contributing

To improve this skill:
1. Test on real codebases
2. Identify patterns that need refinement
3. Add language-specific guidelines
4. Expand example library
5. Enhance validation scripts

## License

This skill is provided as-is for use with Claude AI systems.

## Version

**Version:** 1.1.0
**Last Updated:** 2024
**Compatibility:** Claude Code, Claude.ai, Claude API

**Changelog:**
- **v1.1.0**: Added comprehensive flake8 integration with plugin support, before/after comparison, and HTML/JSON reports
- **v1.0.0**: Initial release with complexity analysis, documentation checking, and refactoring patterns

## Support

For issues or questions about this skill, refer to:
- `SKILL.md` for detailed instructions
- `references/patterns.md` for refactoring patterns
- `references/anti-patterns.md` for issue identification
- `references/examples/` for complete worked examples
