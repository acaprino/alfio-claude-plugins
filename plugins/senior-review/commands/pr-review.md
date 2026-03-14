---
description: "Analyze current branch changes, generate a comprehensive PR description with risk assessment and review checklist, and optionally create the PR via gh CLI"
argument-hint: "[--base main] [--create] [--split-check] [--strict-mode]"
---

# PR Enhancement Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Start from git diff.** All analysis comes from `git diff` and `git log` — the actual changes are ground truth.
3. **Run agents in parallel where marked.** Fire parallel agents in a single response.
4. **Confirm before creating PR.** If `--create` flag is set, show the full PR description for approval before running `gh pr create`.
5. **Never enter plan mode.** Execute immediately.
6. **Never push without permission.** If the branch hasn't been pushed, ask the user before pushing.

## Phase 1: Analyze Changes

### Step 1A: Identify the diff

```bash
# Detect base branch (default: main)
git log --oneline $(git merge-base HEAD main)..HEAD
git diff main...HEAD --stat
git diff main...HEAD --name-status
```

If `--base` flag provides a different base branch, use that instead of `main`.

If no commits diverge from base, check for uncommitted changes:
```bash
git diff --name-only
git diff --cached --name-only
```

If nothing to analyze, say so and stop.

### Step 1B: Categorize changed files

Group files by type:
- **Source code**: `.py`, `.js`, `.ts`, `.tsx`, `.rs`, `.go`, `.java`, etc.
- **Tests**: files matching `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`
- **Config**: `.json`, `.yaml`, `.yml`, `.toml`, `Dockerfile`, `Makefile`
- **Docs**: `.md`, `.txt`, `.rst`
- **Styles**: `.css`, `.scss`, `.less`
- **Build/CI**: `.github/`, `Jenkinsfile`, CI configs

### Step 1C: Compute statistics

```bash
git diff main...HEAD --shortstat
```

Present change summary:
```
Branch: [branch name]
Base: [base branch]
Commits: [count]
Files changed: [count] ([source] source, [test] test, [config] config, [docs] docs)
Lines: +[insertions] / -[deletions] (net: [net change])
```

---

## Phase 2: Risk & Architecture Assessment (2 agents in parallel)

Run both agents **in parallel** in a single response.

### Agent A: Architecture & Risk Assessment

```
Task:
  subagent_type: "architect-review"
  description: "Architecture and risk assessment for PR"
  prompt: |
    Analyze the following code changes for architectural soundness and risk.

    ## Changed Files
    [list with categories and line counts]

    ## Diff
    [git diff output]

    ## Instructions
    Assess:
    1. **Change type**: Feature, bugfix, refactor, dependency update, config change
    2. **Architectural impact**: Does this change boundaries, contracts, or data models?
    3. **Risk factors**:
       - Size risk: >500 lines = high, 200-500 = medium, <200 = low
       - Complexity risk: new abstractions, changed interfaces, database migrations
       - Test risk: test coverage of changed code paths
       - Dependency risk: new or updated packages
       - Security risk: auth, input handling, crypto, secrets
    4. **Breaking changes**: Any API contract changes, removed exports, schema changes
    5. **PR split opportunities**: If >500 lines, suggest logical split points

    Output a structured risk assessment with an overall risk level (Low/Medium/High/Critical).
```

### Agent B: Security & Dependency Check

```
Task:
  subagent_type: "security-auditor"
  description: "Security review for PR changes"
  prompt: |
    Review the following code changes for security concerns relevant to a PR.

    ## Changed Files
    [list of changed code files]

    ## Diff
    [git diff output]

    ## Instructions
    Check for:
    1. Secrets or credentials in the diff (API keys, tokens, passwords)
    2. New dependencies — are they trustworthy? Known vulnerabilities?
    3. Input validation gaps in new/modified code
    4. Auth/authorization changes — are they correct?
    5. Insecure defaults introduced (debug mode, verbose errors, permissive CORS)

    If no security issues, say so clearly.
    For each finding: severity, file, issue, fix.
```

---

## Phase 3: Generate PR Description

Using the analysis from Phase 1 and agent findings from Phase 2, generate a complete PR description.

### PR Description Template

```markdown
## Summary

[2-3 sentence executive summary of what this PR does and why]

**Risk Level**: [Low/Medium/High/Critical] | **Review Time**: ~[estimate] min | **Lines**: +[X] / -[Y]

## What Changed

### [Category Icon] [Category] Changes
- [status]: `filename` — [brief description of change]

[Repeat for each category with changes]

## Why These Changes

[Extract motivation from commit messages and code context — the business reason]

## Type of Change

- [ ] New feature
- [ ] Bug fix
- [ ] Refactoring
- [ ] Dependency update
- [ ] Configuration change
- [ ] Documentation

## How to Test

1. [Step-by-step testing instructions]
2. [Include specific commands to run]
3. [Expected outcomes]

## Risk Assessment

| Factor | Level | Details |
|--------|-------|---------|
| Size | [Low/Med/High] | [X files, Y lines] |
| Complexity | [Low/Med/High] | [description] |
| Test Coverage | [Low/Med/High] | [description] |
| Dependencies | [Low/Med/High] | [description] |
| Security | [Low/Med/High] | [description] |

[Include any security findings from Agent B]

## Breaking Changes

[List any breaking changes, or "None"]

## Review Checklist

### General
- [ ] Self-review completed
- [ ] No debugging code left
- [ ] No sensitive data exposed

### Code Quality
[Context-aware items based on file types changed]

### Testing
[Items based on whether tests were added/modified]

### Security
[Items based on security agent findings]
```

### PR Split Suggestions (if applicable)

If `--split-check` flag is set or PR exceeds 500 lines, include:

```markdown
## PR Split Suggestion

This PR is [X] lines across [Y] files. Consider splitting into:

1. **[logical unit 1]**: [files], [purpose]
2. **[logical unit 2]**: [files], [purpose]

This improves review quality and reduces merge conflict risk.
```

---

## Phase 4: Present & Optionally Create PR

### Always: Present the description

Show the complete PR description in the conversation and ask:

```
PR description generated.

Risk Level: [level]
Files: [count] | Lines: +[X]/-[Y]

1. Create PR now (pushes branch and creates PR via gh)
2. Copy description only (I'll create the PR manually)
3. Revise — adjust the description first
```

### If `--create` flag or user chooses option 1:

First check if branch is pushed:
```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
```

If not pushed, ask:
```
Branch [name] hasn't been pushed to remote. Push and create PR?
```

Then create the PR:
```bash
git push -u origin [branch-name]
gh pr create --base [base-branch] --title "[title]" --body "[description]"
```

Present the PR URL when done.

### If `--strict-mode` and Critical risk:

```
STRICT MODE: Critical risk factors detected. Recommend splitting or addressing security findings before creating PR.
```
