---
description: >
  Remove technical debt across 5 dimensions: dead code (Knip / vulture / ruff), orphan assets, generated artifacts tracked in VCS + .gitignore gaps, phantom / unused dependencies in monorepo workspaces, and stale documentation / historical artifacts (completed plans, scratch directories, backup/legacy folders, orphan doc-assets, broken doc references). Incremental-phase workflow with commit-per-category and build+test gates between phases.
  TRIGGER WHEN: the user asks to find/remove unused code, dead exports, unused dependencies, orphan assets, generated files in git, phantom deps, stale plans, scratch folders, backup files, or run a codebase cleanup pass.
  DO NOT TRIGGER WHEN: the task is code readability (use /clean-code:clean-code) or architectural refactoring (use /python-development:python-refactor). For detection only (no edits) as part of /senior-review:team-review, the `senior-review:cleanup-auditor` agent is used instead.
argument-hint: "[path] [--dry-run] [--phase=garbage|brand|assets|gitignore|deps|exports|docs] [--dependencies-only] [--exports-only] [--docs-only] [--apply] [--production]"
---

# Cleanup Dead Code

Detect and remove technical debt across 4 dimensions. Incremental phases, one commit per category, build+test gate between phases, automatic revert on gate failure.

## CRITICAL RULES

1. **Git pre-flight**: before any phase, `git status` must be clean. Warn and halt if the working tree has uncommitted changes.
2. **Phase isolation**: each phase commits to its own commit, never mix categories. This makes every step independently revertible.
3. **Gate after every phase**: `npm run build` (or project-equivalent) must pass. Tests must not regress vs. baseline. If either gate fails, `git reset --hard HEAD~1` and halt.
4. **Grep-before-delete**: for any asset, export, or dep candidate, run a final confirmation `Grep` with zero results before removal. Skip if any match.
5. **`--dry-run` reports only**: no file edits, no git operations, no gate runs.
6. **Never remove via side effects**: dynamic imports, decorators, framework conventions, module augmentation (`*.d.ts` with `declare module`).
7. **Python functions/classes require approval**: vulture high-FP. Present separately; get explicit user confirmation.

## Step 0: Detect Project Shape

```bash
# Language
ls package.json pnpm-workspace.yaml pyproject.toml setup.py setup.cfg Cargo.toml 2>/dev/null
# Workspace type (if JS/TS)
cat package.json 2>/dev/null | grep -A 3 '"workspaces"'
cat pnpm-workspace.yaml 2>/dev/null
# Frameworks (for gitignore templates)
ls src-tauri/ android/ ios/ 2>/dev/null
cat package.json 2>/dev/null | grep -E '"(react|next|vite|nuxt|svelte|solid|vue)"'
```

Compute:
- `PROJECT_LANG`: ts|js|py|mixed
- `PKG_MANAGER`: npm|pnpm|yarn|bun (from lockfile)
- `WORKSPACE`: none|npm-workspace|pnpm-workspace
- `FRAMEWORKS`: set of detected frameworks
- `BUILD_CMD`: inspect `package.json` scripts or fall back to `npm run build`
- `TEST_CMD`: inspect `package.json` scripts; prefer unit (vitest run, jest, pytest) over e2e

## Step 1: Establish Baseline

Before any phase:
```bash
git status                        # must be clean
git rev-parse HEAD                # record starting commit
$BUILD_CMD                        # must pass
$TEST_CMD                         # record pass/fail counts as baseline
```

If baseline build or tests fail, halt. The user must stabilize main before cleanup.

## Step 2: Detection (All 5 Dimensions)

Run `senior-review:cleanup-auditor` conceptually (or replicate its pipeline):

### 2A: Dead code
- **TS/JS**: invoke `typescript-development:knip` skill; fallback `bunx knip --reporter json || npx knip --reporter json`.
- **Python**: invoke `python-development:python-dead-code` skill; fallback `vulture . --min-confidence 80` + `ruff check . --select F401,F811,F841`.

### 2B: Asset audit
- List all files in `public/`, `src/assets/`, `assets/`, `static/` with image/font/audio/video extensions.
- For each asset, `Grep` the basename + relative path across source files.
- Detect `import.meta.glob('...', { eager: true })` -- expand, count matches, compute usage ratio.
- Detect rebrand residue: ask user for old brand name if not obvious from git history (`git log --diff-filter=R --name-status`).

### 2C: VCS hygiene
- `git ls-files` filtered for common generated-artifact patterns (see `cleanup-auditor.md` D3 for the full regex list).
- `git ls-files` filtered for filesystem garbage (`nul`, `.DS_Store`, shell-redirection filenames).
- `.gitignore` completeness audit per detected framework.

### 2D: Dependency hygiene (monorepo-aware)
- Per workspace, list deps; `Grep` each within the workspace directory only.
- Phantom deps: declared in `W` but imported only from sibling workspaces.
- Unused deps: declared, zero imports anywhere.
- Barrel-file bloat: files with >= 30 re-exports, usage ratio < 20%.
- Eager-bundle bloat: top-level imports of known-heavy packages (`lodash`, `moment`, `@mui/icons-material`, `react-icons/*`, `rxjs`, `@aws-sdk/client-*`) without code-splitting.

### 2E: Stale documentation & historical artifacts

Detection-only by default. Removal requires `--phase=docs --apply` (or the global `--apply` flag) because doc FP-rate is much higher than code.

**2E.1 Completed / abandoned plans**
- Scan `docs/plans/`, `plans/`, `.plans/`, `PLAN.md` files at root.
- For each plan file, extract signals: explicit `status:` frontmatter (`done`, `complete`, `implemented`, `archived`, `superseded`), checklist completion ratio (`- [x]` vs `- [ ]`), last-modified date via `git log -1 --format='%ai' -- <file>`, references to files that no longer exist (`Grep` plan body for `path/to/file` then `Test-Path`).
- Candidate = (status marker says done) OR (100% checklist complete + not modified in 90 days) OR (>50% of referenced files no longer exist).

**2E.2 Scratch / WIP / pipeline-output directories**
- Patterns to flag if present and tracked or untracked-but-clutter:
  - `.upstream-scratch/`, `.deep-dive/`, `.team-review/`, `.codebase-map/`, `.research/`, `.brainstorm/`
  - `tmp/`, `temp/`, `scratch/`, `_wip/`, `wip/`, `_drafts/`
  - Root-level `NOTES.md`, `TODO.md`, `SCRATCH.md` older than 60 days
- Distinguish: scratch dirs in `.gitignore` but present on disk -> safe to remove locally (no commit). Scratch dirs currently tracked -> propose `git rm -r` + `.gitignore` addition.

**2E.3 Backup / legacy / archive folders**
```bash
git ls-files 2>/dev/null | grep -iE '\.(bak|old|orig|swp|backup)$|(^|/)(_archive|archive|legacy|old|deprecated|_old|_legacy|backup)/'
```
Also scan untracked: same patterns via `Glob`. Always require user confirmation; `_archive/` may be deliberate cold storage.

**2E.4 Orphan doc-assets**
- List images/diagrams in `docs/`, `docs/images/`, `docs/assets/`, `docs/diagrams/`, `.github/assets/`.
- For each, `Grep` basename across `**/*.md`, `**/*.mdx`, `**/*.rst`, `**/*.adoc`.
- Zero references -> orphan doc-asset candidate.

**2E.5 Stale doc references (run AFTER phases `assets`, `deps`, `exports`)**
- Collect the list of paths/symbols/dep names removed by prior phases of this same cleanup run (read from prior commit diffs).
- `Grep` each removed token across `**/*.md`, `**/*.mdx`, `README*`, `CHANGELOG*`, `CLAUDE.md`, `AGENTS.md`.
- Each hit is a stale-reference finding. Removal here = edit, not delete: rewrite the doc paragraph or strike the bullet; never `rm` an entire doc file just because one link inside became stale.

**2E.6 Superseded ADRs**
- Scan `docs/adr/`, `docs/decisions/`, `architecture/decisions/`.
- Files with `Status: Superseded` (or equivalent) front-matter > 1 year old are candidates for moving to an `adr/superseded/` subfolder (not deletion -- ADRs are historical record).

Categorize every finding. Present the report. If `--dry-run`, stop here.

## Step 3: Incremental Phase Workflow

Default order, lowest-risk first. If `--phase=<name>` provided, run only that phase. Otherwise run all in order, stopping at first gate failure.

### Phase order

1. `garbage` -- filesystem cruft (`nul`, `.DS_Store`, shell-redirection artifacts)
2. `brand` -- rebrand residue (old logo files, legacy brand strings in asset filenames)
3. `assets` -- orphan static files (images, fonts, SVGs, audio)
4. `gitignore` -- add missing patterns + `git rm --cached` for currently-tracked generated artifacts
5. `deps` -- unused + phantom dependencies in `package.json`
6. `exports` -- dead code (exports, types, unused files, unused Python symbols)
7. `docs` -- stale documentation & historical artifacts (completed plans, scratch dirs, backup folders, orphan doc-assets, broken doc refs). Last on purpose: must run after `exports` so it can also catch newly-stale doc references to code just removed. Detection-only by default; requires `--apply` for removal.

### Per-phase template

For every phase `P`:

**P.1: Confirm zero references** (idempotent Grep):
```bash
for item in $CANDIDATES; do
  # strict string match across source; exclude the file being removed
  Grep -r "$item" --include='*.{ts,tsx,js,jsx,mjs,cjs,html,css,scss,md,mdx,vue,svelte,py}' \
    src/ packages/ apps/ public/ 2>/dev/null
done
```
Skip any item with matches. Log skipped items separately.

**P.2: Apply removals in small batches** (5-20 items per batch). For each batch:
- JS/TS code: delete file or edit export line.
- Assets: `git rm` the file.
- Generated artifacts: `git rm --cached` (keep on disk, ignore going forward).
- Deps: edit `package.json`, re-run `$PKG_MANAGER install` (or `pnpm install`).
- `.gitignore`: append missing patterns.

**P.3: Gate**:
```bash
$BUILD_CMD || { git reset --hard HEAD; echo "BUILD FAILED in phase $P, reverted"; exit 1; }
$TEST_CMD || { git reset --hard HEAD; echo "TESTS FAILED in phase $P, reverted"; exit 1; }
```

**P.4: Commit** (one per phase):
```bash
git add -A
git commit -m "chore(cleanup): $P -- <count> items removed

- <short summary of what was removed>
"
```

**P.5: Proceed to next phase or halt** if gate failed.

## Step 4: Phase-Specific Notes

### `garbage`
Safest phase. `git rm` or `rm` (for untracked). No build/dep impact expected.

### `brand`
Requires user confirmation of old brand name. Run grep for the old name across code, config, docs, asset filenames. Remove matches.

### `assets`
- Confirm each asset has zero references before `git rm`.
- Watch for dynamic references: `` `/assets/${name}.svg` `` template literals. Grep for partial basenames too.
- For eager `import.meta.glob` bloat: do NOT just remove the glob; switch to `{ eager: false }` + lazy `.then()` unless ALL files are provably unused. Removing the glob entirely requires user sign-off.

### `gitignore`
Two sub-steps:
1. Add missing patterns to `.gitignore`.
2. `git rm --cached <paths>` for currently-tracked files now matched by the new patterns.
Regenerate `.gitignore` only if it was empty or clearly minimal; otherwise append.

### `deps`
- Phantom deps: move to the correct workspace's `package.json` instead of deleting, unless confirmed unused everywhere.
- After editing `package.json`, re-install to update the lockfile. Commit both `package.json` AND the lockfile.
- Do NOT edit `devDependencies` that are implicitly used (`prettier`, `eslint`, `typescript`, `@types/*` matching runtime deps) without a grep of config files.

### `exports`
- Safest to riskiest order:
  1. `ruff` unused imports (F401) + unused variables (F841) -- auto-fix.
  2. Knip unused dependencies (already covered in `deps` phase).
  3. Knip unused exports / types -- verify with `Grep` of symbol name across ALL workspaces.
  4. Knip unused files -- verify no dynamic require/import, no framework-convention path.
  5. vulture unused functions/classes -- **require user confirmation**.

### `docs`
Highest FP-rate phase. Removal is opt-in.

1. **Detection-only by default.** Without `--apply`, output the categorized report and stop. The user reviews it, then re-runs with `--phase=docs --apply` (optionally with `--only=plans,scratch` to scope).
2. **Per-item confirmation gate for plans, ADRs, archives.** A stale plan looks identical to an active plan to a tool. Ask the user per-file (or per-folder when the folder is the whole unit, e.g. `_archive/`) before any `git rm`. Show: path, last-modified date, checklist completion %, first 5 lines of body.
3. **Scratch directories: distinguish tracked vs untracked.**
   - Untracked + in `.gitignore` -> safe local cleanup, no commit needed. Use `rm -rf` after confirmation. Do NOT include in the commit message bullet list.
   - Tracked -> `git rm -r` + add to `.gitignore`. Commit normally.
4. **Stale doc references = edit, not delete.** Section 2E.5 produces line-level findings. Rewrite the paragraph or strike the bullet; never delete the entire doc because of one stale link. If the doc is now ~empty after edits, propose deletion as a separate finding requiring confirmation.
5. **Orphan doc-assets**: same Grep-before-delete rule as 2C, but search only `*.md`, `*.mdx`, `*.rst`, `*.adoc`. Watch for inline base64 images that don't reference filenames.
6. **ADRs are historical record**: default action for `Status: Superseded` ADRs is *move* to `docs/adr/superseded/`, not delete. Only delete on explicit user instruction.
7. **Commit message convention**: `chore(cleanup): docs -- N items archived/removed` with a per-category breakdown in the body (plans: N, scratch: N, doc-assets: N, stale-refs: N edits).

## Step 5: Final Report

After all phases (or at first gate failure):
```markdown
## Cleanup Summary

| Phase | Status | Items removed | Bytes freed | Commit |
|-------|--------|---------------|-------------|--------|
| garbage | ok | N | X KB | `<sha>` |
| brand | ok | N | X KB | `<sha>` |
| assets | ok | N | X MB | `<sha>` |
| gitignore | ok | N | Y MB (uncached) | `<sha>` |
| deps | ok | N | Z MB install | `<sha>` |
| exports | partial (build failed) | N | - | reverted |
| docs | ok (detection-only, no --apply) | N candidates | - | none |

Bundle size before: X MB
Bundle size after: Y MB
Build time before: Xs
Build time after: Ys
Tests: [baseline] N passed -> [after] N passed

Next steps:
- Rerun `/senior-review:cleanup-dead-code --phase=exports` after investigating the build failure
- Review `CLAUDE.md` for references to removed symbols (see "CLAUDE.md Alignment Check" below)
```

## What It Does

- **Dead code (TS/JS)**: Knip for unused dependencies, exports, files, types.
- **Dead code (Python)**: vulture + ruff for unused imports, variables, functions, classes, unreachable code.
- **Assets**: orphan detection via grep-by-basename + eager-glob bloat analysis.
- **VCS**: generated-artifact detection, filesystem garbage removal, `.gitignore` completeness per framework.
- **Dependencies**: unused + phantom (monorepo-aware) + barrel-file bloat + eager-bundle anti-patterns.
- **Docs & historical artifacts** (detection-only by default): completed/superseded plans, scratch and pipeline-output directories (`.upstream-scratch/`, `.deep-dive/`, `.team-review/`), backup/legacy folders (`*.bak`, `_archive/`, `legacy/`, `deprecated/`), orphan doc-assets, stale doc references to symbols removed earlier in the run, superseded ADRs.

## What It Does NOT Do

- Remove code used via side effects, dynamic imports, or reflection (flags as FP candidate instead).
- Modify framework-convention files (Next.js `pages/`, `app/`, Django views, pytest fixtures).
- Touch test files unless they reference removed symbols.
- Run a bundle analyzer. Use `source-map-explorer` or `vite-bundle-visualizer` separately for measurement.
- Refactor architecture. This command is pure subtraction, not redesign.

## CLAUDE.md Alignment Check

After cleanup, verify `CLAUDE.md` still reflects the codebase:

1. Read `CLAUDE.md` (if it exists).
2. `Grep` removed symbols, file paths, and dep names against `CLAUDE.md`.
3. If references found, propose updates to the user.

$ARGUMENTS
