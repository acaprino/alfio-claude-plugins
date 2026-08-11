# Code-review output templates (Steps 5, 5b, 6)

Full output structure for `/senior-review:code-review`: the final review template,
the CLAUDE.md alignment check, and the PR auto-comment flow. Loaded on demand by
the command when it reaches Step 5.

## Step 5: Final Review Output

After validation completes, synthesize everything into the final structured review:

```
## Code Review -- [PR title or branch name]

### Review Scope
- **Scope:** [diff source -- e.g., origin/main..HEAD, uncommitted changes, PR #42]
- **Intent:** [2-3 line intent summary from Step 1b]
- **Reviewers:** code-auditor, security-auditor, dead-code, [+ conditional agents with justification]
- Files reviewed: [N]
- Lines changed: +X / -Y
- CLAUDE.md compliance: [checked / not found]
- Verification: X of Y findings verified (4-lens panel), Z false positives, W contested, V premise-refuted, U premise-contested{cost_guard_note}

### Overall Score: X/10 (confidence: X%)

### Critical & High Findings
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|
| 1 | Critical | ...       | ...     | 95%        | ... |

### Medium & Low Findings
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### Dead Code & Unused Parameters
| # | Source | Severity | File:Line | Finding | Confidence | Action |
|---|--------|----------|-----------|---------|------------|--------|

### Failure Flow & Resilience
| # | Severity | File:Line | Scenario | Confidence | Fix |
|---|----------|-----------|----------|------------|-----|

### UI Race Conditions (if applicable)
| # | Severity | File:Line | Timeline | Confidence | Fix |
|---|----------|-----------|----------|------------|-----|

### Platform Engineering (if applicable)
| # | Severity | File:Line | Rule | Confidence | Fix |
|---|----------|-----------|------|------------|-----|

### Git History & Churn (if applicable)
| # | Severity | File:Line | Pattern | Commits Referenced | Confidence |
|---|----------|-----------|---------|-------------------|------------|

### Testing Issues (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### API Contract Issues (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### Data Migration Issues (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### React Performance (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### Abstraction & Reuse (if applicable)
| # | Class | Severity | New Code | Prior Art | Difference | Direction |
|---|-------|----------|----------|-----------|------------|-----------|

Second occurrences (R4), listed without flagging: [one line each, or "none"]

### Coverage
- Suppressed: [N] findings below 0.50 confidence
- Deduplicated: [N] cross-agent duplicates merged
- Residual risks: [risks noticed but not confirmed as findings]
- Testing gaps: [missing test coverage identified]

### Coverage Gaps
[paste the ## Coverage Gaps list from the completeness critic, or "None identified"]

### Pattern Consistency
- [pattern deviations found, or "Changes follow established patterns"]

### CLAUDE.md Compliance
- [list any violations, or "All changes comply with project conventions"]

### Pre-existing Issues (does not count toward verdict)
| # | File:Line | Issue | Reviewer |
|---|-----------|-------|----------|
[issues in unchanged code unrelated to the diff, or "None"]

---

> **Verdict:** [Ready to merge / Ready with fixes / Not ready]
>
> **Reasoning:** [1-2 sentences explaining why]
>
> **Fix order:** [severity-ordered list of what to fix first, if applicable]
```

Where `{cost_guard_note}` is `, narrowed to stakes+band (N unverified)` when the cost guard fired, else empty.

If `--strict` and there are Critical findings:

```
STRICT MODE: Critical issues found. Not ready to merge.
```

## Step 5b: CLAUDE.md Alignment Check

After producing the review output, check if findings suggest the project's `CLAUDE.md` is stale:

1. Read `CLAUDE.md` (if it exists -- it was already read in Step 2)
2. Cross-reference review findings with documented conventions, structure, and workflows
3. If any documented information is outdated or missing, add a `### CLAUDE.md Staleness` section to the review output noting what needs updating

---

## Step 6: Auto-Comment on PR (if --auto-comment)

If `--auto-comment` flag is set and reviewing a PR:

Post only **CRITICAL and HIGH severity** findings as inline PR comments. Do NOT auto-comment MEDIUM or LOW findings -- include those only in the summary report. This prevents comment spam and focuses reviewer attention on what matters.

Write each comment body to a temp file first, then use `-F` to avoid shell injection from LLM-generated content.

### Committable Suggestions

For each inline comment, decide whether to include a committable suggestion:

- **Include suggestion** when the fix is small and self-contained (< 6 lines changed, single location, committing the suggestion fully resolves the issue)
- **No suggestion** when the fix is large (6+ lines), structural, spans multiple locations, or committing the suggestion alone would not fully fix the problem
- **Never** post a committable suggestion unless committing it fixes the issue entirely -- partial suggestions that require follow-up steps are worse than no suggestion

### Inline comment format

```bash
mkdir -p .code-review-tmp

# Without committable suggestion (large or multi-location fix)
cat > .code-review-tmp/temp_inline_comment.md << 'COMMENT_EOF'
**[Severity]** -- [finding summary]

[concrete fix recommendation describing what to change]
COMMENT_EOF

# With committable suggestion (small, self-contained fix)
cat > .code-review-tmp/temp_inline_comment.md << 'COMMENT_EOF'
**[Severity]** -- [finding summary]

```suggestion
[corrected code that fully fixes the issue when committed]
```
COMMENT_EOF

# Post as inline PR comment using -F (file input)
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  -F body=@.code-review-tmp/temp_inline_comment.md \
  -f path="[file]" \
  -f line=[line] \
  -f commit_id="$(gh pr view {number} --json headRefOid --jq '.headRefOid')"
```

Post the overall summary as a regular PR comment (also via temp file):

```bash
mkdir -p .code-review-tmp

cat > .code-review-tmp/temp_summary_comment.md << 'SUMMARY_EOF'
## Automated Code Review

**Overall Score: X/10**

[summary of critical/high findings]

[top 3 recommended actions]

---
*Reviewed by: code-auditor, security-auditor, dead-code-and-lint-detector, ui-race-auditor, git-history-analyzer | Findings verified by 4-lens panel*
SUMMARY_EOF

gh pr comment {number} -F .code-review-tmp/temp_summary_comment.md
```

---
