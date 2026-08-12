---
name: repo-hygiene
description: >
  The check catalog for workspace tidying: filesystem garbage, generated artifacts tracked in
  git, `.gitignore` completeness and archaeology, scratch directories, orphan doc-assets, and git
  auxiliary state. Two profiles, full and lite, over one set of check definitions.
  Use when running /tidy, auditing a repository for committed build output or ignore-rule rot, or
  running the diff-scoped VCS check inside a code or PR review. Not for questions needing source
  comprehension (dead exports, unused dependencies, orphan application assets, rebrand residue),
  which `review-cleanup-auditor` in the `_pipelines` bundle covers.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: repo-hygiene
---

# Repo hygiene

Every check here is decided by the filesystem and by git. No source file is read, and
no symbol is understood. That is the whole membership rule: a check that needs to know
what a symbol is for, or whether a reference reaches it, does not belong in this
catalog and belongs to `review-cleanup-auditor` in the `_pipelines` bundle instead.

## Two profiles over one catalog

The checks are defined once. Two profiles decide the perimeter, and nothing else
differs between them. A caller names its profile; a check that has no meaning at the
chosen perimeter is skipped rather than silently widened.

| | **full** | **lite** |
|---|---|---|
| Perimeter | The whole working tree | Only files the diff ADDS |
| Callers | `/tidy`, `workspace-auditor` | The inline hygiene pass of `/code-review` in the `_pipelines` bundle and `/pr-review` in the `_pipelines` bundle |
| C1 filesystem garbage | yes | yes, restricted to added paths |
| C2 generated artifacts tracked | yes | yes, restricted to added paths |
| C3 `.gitignore` completeness | yes | only for the ecosystems the added paths belong to |
| C4 `.gitignore` archaeology | yes | **no** |
| C5 scratch directories | yes | **no** |
| C6 orphan doc-assets | yes | **no** |
| C7 git auxiliary state | yes | **no** |

**The lite profile cannot widen.** C4 through C7 are repository-historical by
construction: an ignore rule stale since 2024, a scratch directory nobody touched, a
stash from last month. None of them can be caused by the diff under review, so
reporting them there is noise attributed to an innocent change. A lite caller that
finds itself listing a Python ignore rule on a pull request that added one TypeScript
file has widened, and that is a defect.

## The catalog

### C1 Filesystem garbage

```bash
git ls-files 2>/dev/null | grep -iE '(^|/)(nul|\.DS_Store|Thumbs\.db|desktop\.ini|\.swp|\.swo|#.*#|~$)|(^|/)[<>|&]|2>&1'
```

Shell-redirection artifacts (`nul`, files named `2>&1` or starting with `>`) are the
highest-confidence class in this catalog: nothing legitimately produces them.

### C2 Generated artifacts tracked in git

```bash
git ls-files 2>/dev/null | grep -E '(^|/)(dist|build|out|\.next|\.nuxt|\.cache|\.turbo|\.parcel-cache|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.venv|venv|node_modules|target|\.gradle|android/app/build|ios/build|src-tauri/gen|src-tauri/target)(/|$)'
git ls-files 2>/dev/null | grep -E '\.(bundle\.js|chunk\.js|min\.js\.map|pyc|class|o|obj)$'
```

**A tracked build output is not automatically a mistake.** Repositories commit `dist/`
on purpose: GitHub Pages serves from it, a generated SDK ships to package consumers, a
vendored bundle exists so installs need no build step. Untracking those breaks the next
clean checkout while every local command keeps passing, because the files are still on
disk. Before flagging, check for a publication convention that requires the path:

```bash
ls .github/workflows/*pages* .nojekyll CNAME 2>/dev/null      # Pages publication
git show HEAD:package.json 2>/dev/null | grep -A5 '"files"'   # npm publish allowlist
grep -rl "$(basename <path>)" --include='*.yml' .github/ 2>/dev/null
```

A hit means the artifact is intentional. Report it as **KEEP** with the convention
named, never as a removal candidate.

### C3 `.gitignore` completeness

Detect project signals, then check the corresponding patterns exist:

| Signal | Expected patterns |
|---|---|
| `package.json` | `node_modules/`, `dist/`, `build/`, `.env`, `.env.local`, `npm-debug.log*` |
| `vite.config.*` | `dist/`, `.vite/` |
| `next.config.*` | `.next/`, `out/` |
| `src-tauri/` | `src-tauri/target/`, `src-tauri/gen/` |
| `Cargo.toml` | `target/`, and `Cargo.lock` only for libraries |
| `pyproject.toml` or `requirements.txt` | `__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info/`, `.pytest_cache/` |
| `*.gradle` | `android/app/build/`, `android/build/`, `android/.gradle/` |
| `Podfile` | `ios/build/`, `ios/Pods/` |
| any | `.DS_Store`, `Thumbs.db` |

A missing pattern with a tracked file matching it is a **`.gitignore` gap**.

### C4 `.gitignore` archaeology

Establish provenance before judging anything:

```bash
git check-ignore -v <path>
```

It names the source file and line: `.gitignore`, a nested ignore file, `.git/info/exclude`,
or the global ignore. **Only rules in tracked ignore files become findings.** Local and
global sources get a note at most, because they are not the repository's to change.

- **Stale rule**: a pattern matching nothing on disk and nothing plausible in recent
  history. LOW. Never flag prophylactic ecosystem defaults (`node_modules/`,
  `__pycache__/`, `.DS_Store`): their value is precisely that they match nothing yet.
- **Overly-broad rule**: a pattern whose ignored matches include source- or
  config-shaped files outside generated directories. Action **UNIGNORE**. Verify each
  candidate is not generated before flagging.

### C5 Scratch and pipeline-output directories

```bash
for d in .upstream-scratch .deep-dive .team-review .codebase-map .research .brainstorm \
         .peer-review .frontend-review tmp temp scratch _wip wip _drafts; do
  [ -d "$d" ] && echo "$d"
done
ls NOTES.md TODO.md SCRATCH.md 2>/dev/null
```

Three states, three dispositions:

- **Untracked and already ignored**: local clutter only. LOW, removable without a commit.
- **Tracked**: clutters every clone. HIGH, `git rm -r` plus an ignore entry.
- **Tracked and already ignored**: an impossible state that means the file was committed
  before the pattern existed. Sanity-check before acting.

### C6 Orphan doc-assets

List images and diagrams under `docs/`, `docs/images/`, `docs/assets/`,
`docs/diagrams/`, `.github/assets/`, then Grep each basename across `**/*.md`,
`**/*.mdx`, `**/*.rst`, `**/*.adoc`.

**Zero literal references is not proof of orphanhood.** A documentation asset reaches
the rendered site through paths a basename Grep never sees: a value in `mkdocs.yml` or
`docusaurus.config.js`, a `url()` in a stylesheet, a generated navigation entry, a path
composed in a template. Widen the search before believing the result:

```bash
grep -rl "$(basename <asset>)" --include='*.yml' --include='*.yaml' --include='*.toml' \
  --include='*.json' --include='*.css' --include='*.scss' --include='*.html' --include='*.j2' .
grep -rlE "(logo|banner|icon|favicon|social)" mkdocs.yml docusaurus.config.* _config.yml 2>/dev/null
```

An asset that survives both searches is a **candidate**, never a confirmed orphan.
Removal requires item-level approval, and the finding says so.

### C7 Git auxiliary state

```bash
git stash list
git worktree list
git branch -vv | grep ': gone]'
git branch --merged
```

Stashes idle beyond 90 days, worktrees pointing at deleted branches or paths, local
branches whose upstream is gone, and merged-but-undeleted branches are LOW to MEDIUM
findings.

**This dimension is detection-only, permanently, and the reason is structural.** Every
other check in this catalog mutates tracked content, so a commit records what changed
and reverting that commit restores it. These four do not. A dropped stash leaves no
trace in any commit; a removed worktree with uncommitted files inside takes them with
it; a deleted branch's tip survives only in a reflog that expires. Per-phase commits
cannot be the rollback mechanism for a mutation that produces no diff, so nothing here
is applied automatically at any confirmation level. Removal commands belong in the
finding text, for the user to run and own.

## Finding format

Every finding carries the same six fields, whatever the profile:

```
[C<n>] <one-line description>
  path:        <path or ref>
  evidence:    <the command output that decided it>
  disposition: KEEP | KEEP+IGNORE | REMOVE | REMOVE+IGNORE | UNIGNORE | REVIEW | REPORT-ONLY
  confidence:  HIGH | MEDIUM | LOW
  phase:       garbage | gitignore | scratch | git-state
```

`phase` names the `/tidy` phase that resolves it. It never names a
`senior-review` phase: the two commands own disjoint sets, and a finding that crosses
that line is misfiled rather than merely mislabelled.

## Application safety

What the catalog permits, by disposition. A caller that only detects ignores this
section entirely.

| Disposition | Applied how |
|---|---|
| `REMOVE` on untracked files | Moved to `.repo-hygiene/quarantine/<timestamp>/`, never deleted. Git holds no copy of an untracked file, so deletion is the one irreversible operation available and it is not taken. |
| `REMOVE` on tracked files | `git rm`, recoverable from history. |
| `KEEP+IGNORE`, `REMOVE+IGNORE` | Append the pattern, then `git rm --cached` **per item, each confirmed**, because C2's publication check is a heuristic and being wrong breaks a clean checkout while every local signal stays green. |
| `UNIGNORE` | Edit the ignore rule only. Never `git add` on the user's behalf. |
| `REVIEW`, `REPORT-ONLY` | Never applied. Reported with the command the user would run. |
