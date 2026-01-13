# Deep Dive Analysis

Use the `deep-dive-analysis` skill to perform comprehensive codebase analysis combining mechanical structure extraction with AI-powered semantic understanding.

## Target

$ARGUMENTS

## Quick Examples

- `/deep-dive-analysis src/` - Full codebase analysis
- `/deep-dive-analysis src/auth/ --critical` - Analyze critical authentication module
- `/deep-dive-analysis docs/ --phase 8` - Documentation maintenance and health check
- `/deep-dive-analysis src/main.py --comments` - Analyze and improve code comments

## Capabilities

### Source Code Analysis (Phases 1-7)

Extracts and documents:
- **WHAT** the code does (structure, functions, classes)
- **WHY** it exists (business purpose, design decisions)
- **HOW** it integrates (dependencies, contracts, flows)
- **CONSEQUENCES** of changes (side effects, failure modes)

### Documentation Maintenance (Phase 8)

- Scan documentation health
- Validate and fix broken links
- Verify docs against source code
- Update navigation indexes

### Comment Quality (Antirez Standards)

- Analyze comment quality
- Identify trivial/debt/backup comments
- Rewrite comments following antirez standards

## Available Commands

### Analyze Single File
```bash
python .claude/skills/deep-dive-analysis/scripts/analyze_file.py \
  --file <path> \
  --output-format markdown
```

### Check Progress
```bash
python .claude/skills/deep-dive-analysis/scripts/check_progress.py \
  --phase <1-7> \
  --status pending
```

### Documentation Health
```bash
python .claude/skills/deep-dive-analysis/scripts/doc_review.py scan \
  --path docs/ \
  --output doc_health_report.json
```

### Comment Analysis
```bash
python .claude/skills/deep-dive-analysis/scripts/rewrite_comments.py analyze \
  <file> --report
```

## Workflow Options

### Full Codebase Analysis
1. Set up `analysis_progress.json` in project root
2. Analyze files phase by phase (critical first)
3. Generate semantic documentation
4. Verify against runtime behavior

### Documentation Review
1. Scan docs for health issues
2. Fix broken links
3. Verify against source code
4. Update navigation indexes

### Comment Cleanup
1. Scan for comment issues
2. Generate health report
3. Apply rewrites (with backup)
4. Verify improvements

## Prerequisites

- Python >= 3.13
- `analysis_progress.json` in project root (for full analysis)

## References

See `plugins/code-review/skills/deep-dive-analysis/references/` for:
- `DEEP_DIVE_PLAN.md` - Master analysis plan
- `AI_ANALYSIS_METHODOLOGY.md` - Semantic analysis methodology
- `SEMANTIC_PATTERNS.md` - Pattern recognition guide
- `ANTIREZ_COMMENTING_STANDARDS.md` - Comment quality standards
