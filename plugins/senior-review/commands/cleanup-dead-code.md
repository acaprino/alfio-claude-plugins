---
description: >
  Remove technical debt across 4 dimensions -- dead code (Knip / vulture / ruff), orphan assets, generated artifacts tracked in VCS + .gitignore gaps, and phantom / unused dependencies in monorepo workspaces. Incremental-phase workflow with commit-per-category and build+test gates between phases.
  TRIGGER WHEN: the user asks to find/remove unused code, dead exports, unused dependencies, orphan assets, generated files in git, phantom deps, or run a codebase cleanup pass.
  DO NOT TRIGGER WHEN: the task is code readability (use /clean-code:clean-code) or architectural refactoring (use /python-development:python-refactor). For detection only (no edits) as part of /agent-teams:team-review, the `senior-review:cleanup-auditor` agent is used instead.
argument-hint: "[path] [--dry-run] [--phase=garbage|brand|assets|gitignore|deps|exports] [--dependencies-only] [--exports-only] [--production]"
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

## Step 2: Detection (All 4 Dimensions)

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

Categorize every finding. Present the report. If `--dry-run`, stop here.

## Step 3: Incremental Phase Workflow

Default order, lowest-risk first. If `--phase=<name>` provided, run only that phase. Otherwise run all in order, stopping at first gate failure.

### Phase order

1. `garbage` -- filesystem cruft (`nul`, `.DS_Store`, shell-redirection artifacts)
2. `brand` -- rebrand residue (old logo files, legacy brand strings in asset filenames)
3. `assets` -- orphan static files (images, fonts, SVGs, audio)
4. `gitignore` -- add missing patterns + `git rm --cached` for currently-tracked generated artifacts
5. `deps` -- unused + phantom dependencies in `package.json`
6. `exports` -- dead code (exports, types, unused files, unused Python symbols) -- last because highest review burden

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
