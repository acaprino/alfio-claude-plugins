# repo-hygiene: splitting workspace tidying out of code review

Date: 2026-08-11
Plugins: `repo-hygiene` (new), `senior-review` (modified)
Status: draft, not frozen. Written for external challenge via `/peer-review:review` before any implementation plan exists.

## Context

Step 7c of `/senior-review:code-review --commit` is the only place in this marketplace that performs bulk removal of application code. It runs seven phases in ascending risk order (`garbage`, `brand`, `assets`, `gitignore`, `deps`, `exports`, `docs`), each committed separately, each gated by a build-and-test run against a baseline captured before the first phase. Its detection half is `senior-review:cleanup-auditor`, an always-on dimension of `/senior-review:team-review` covering six dimensions: dead code (D1), assets (D2), VCS hygiene (D3), dependencies (D4), documentation and historical artifacts (D5), lifecycle archaeology (D6).

The seven phases are not the same kind of work. Removing a tracked `nul` file and removing a dead export are both subtraction, but only one of them can break the build, and only one of them requires understanding what the code means. Today they share a pre-flight, a gate, and a command, because they arrived together.

The cost of that shared home is concrete. Deleting `.DS_Store` from git sits behind a full build-and-test gate that exists to protect the `exports` phase. Appending `node_modules/` to `.gitignore` requires a clean working tree, `--commit`, and a review that produced hygiene findings in the first place. A user who wants to tidy a workspace has to run a code review to get there.

## The load-bearing distinction

Every phase is classified by **what kind of evidence decides it**:

- **Filesystem and git evidence.** The question is answered by `git ls-files`, `git check-ignore`, `git stash list`, or a directory listing. No source file has to be read, and no symbol has to be understood. Being wrong here costs a `git revert`, never a broken build.
- **Code comprehension.** The question is answered by understanding what a symbol is for, whether a reference reaches it, and whether removing it changes behavior. Dynamic imports, decorators, framework conventions, and module augmentation are all failure modes of this class. Being wrong here breaks the build, which is exactly what the gate exists to catch.

This is the boundary the split follows. It is not a size or a risk boundary: it is a boundary about which tool answers the question.

## Section 1: phase ownership (agreed in discussion)

| Phase | Owner | Why |
|---|---|---|
| 1 `garbage` | `repo-hygiene` | Filesystem and git are enough |
| 2 `brand` | `senior-review` | Needs a grep of the old name in the source |
| 3 `assets` | `senior-review` | Needs a grep of dynamic references built from template literals |
| 4 `gitignore` | `repo-hygiene` | Filesystem and git are enough |
| 5 `deps` | `senior-review` | Real use of the imported symbols |
| 6 `exports` | `senior-review` | Code comprehension, the pure case |
| 7 `docs` | splits | Scratch directories and orphan doc-assets go to `repo-hygiene`; plans, ADRs, and stale references stay, they are judgments about content |

Also moving: the git auxiliary state of D6 (stale stashes, orphan worktrees, gone-upstream branches, merged-but-undeleted branches) and the whole of D3.

Consequences of the table:

- **Step 7c goes from seven phases to five**: `brand`, `assets`, `deps`, `exports`, `docs`. Its clean-tree pre-flight, its baseline capture, its per-phase commits, and its build-and-test gate stay exactly as written, and now they finally cover only things that can actually break a build.
- **`repo-hygiene` gets its own phases, with no build-and-test gate**: `garbage`, `gitignore`, `scratch`, `git-state`. Removing a stash cannot fail a test run, so a gate there is ceremony.

## Section 2: what `repo-hygiene` is (proposed, not yet discussed)

A small leaf plugin. It vendors nothing, depends on no local plugin, and is the single source of truth for the checks it owns.

| Component | Purpose |
|---|---|
| `commands/tidy.md` (`/repo-hygiene:tidy`) | Detection plus gated application, four phases, per-phase commits, no build gate |
| `agents/workspace-auditor.md` | Detection-only dimension agent, spawnable by other pipelines |
| `skills/repo-hygiene/SKILL.md` | The check catalog: what counts as garbage, the per-ecosystem `.gitignore` signal table, the ignore-archaeology rules, the scratch-directory patterns, the git auxiliary-state queries |

Content moved verbatim rather than rewritten: D3 in full (generated artifacts, filesystem garbage, `.gitignore` completeness, `.gitignore` archaeology with its `git check-ignore -v` provenance rule), the scratch and orphan-doc-asset halves of D5, the git auxiliary-state block of D6, and phases 1, 4, and the scratch clauses of phase 7 from the 7c reference. Moving the text unchanged is what keeps this a relocation instead of a rewrite, and it is what makes the diff reviewable.

Three rules bind the new plugin, by direct analogy to the ones that keep the existing dependency graph a tree:

1. **`repo-hygiene` never references a `senior-review` agent, skill, or command at runtime.** Prose next-step pointers are fine. This is the same rule that binds `codebase-xray` and `frontend-review`.
2. **`repo-hygiene` declares no local dependency.** It stays a leaf, so nothing it acquires can close a cycle back through `senior-review`.
3. **`repo-hygiene` never removes application code.** Bulk removal of application code stays with Step 7c, and bulk removal of test files stays with `/testing:test-consolidate`. Three owners, no overlap.

## Section 3: two decisions the discussion has not reached

Both follow from the table above rather than being separate ideas, and both are places where the split can quietly reduce coverage.

### 3a. The always-on hygiene dimension of `team-review`

`cleanup-auditor` is always-on in `/senior-review:team-review`. If D3 leaves it, that pipeline loses VCS hygiene entirely unless something replaces it. Under the dependency policy of marketplace 21.3.0, a dimension going dark is exactly the failure mode that policy exists to prevent, and "not installed" is not an available excuse.

**Proposed:** `senior-review` hard-depends on `repo-hygiene` and `/senior-review:team-review` spawns `repo-hygiene:workspace-auditor` as a second always-on hygiene dimension. The transitive cost is one small leaf plugin with no dependencies of its own, which is the cheapest edge in the graph.

**Rejected alternative:** dropping the coverage and telling users to run `/repo-hygiene:tidy` separately. That trades a guaranteed check for a remembered one.

### 3b. The lite pass in `code-review` and `pr-review`

The lite hygiene pass is D1 plus D3 scoped to the diff, and it deliberately adds no spawn: it rides inside `/senior-review:code-review` Agent B2 and inside `/senior-review:pr-review` Agent A. If D3 moves out, either that pass loses its VCS half or the content gets duplicated in two plugins.

**Proposed:** the lite pass keeps both halves and keeps its zero-spawn property, but its VCS check list stops being written inline and is loaded from the `repo-hygiene` skill. One source of truth, no extra agent, and the dependency from 3a already covers the load.

**Rejected alternative:** copying the check list into `senior-review`. Two copies of a check list is how the two copies drift.

## Section 4: blast radius

Files that name the seven phases or the moved dimensions, and therefore change together:

| File | Change |
|---|---|
| `plugins/senior-review/agents/cleanup-auditor.md` | Remove D3, the scratch and orphan-doc-asset parts of D5, and the git auxiliary-state block of D6. Rewrite the `Fix phase` enum, the dimension header, the statistics table, and the recommended execution order for five phases |
| `plugins/senior-review/skills/review-quality-gates/references/code-review-fix-loop.md` | Step 7c phase order goes to five. Renumber. Keep pre-flight, baseline, gate, per-phase template, docs-phase gating, cleanup report |
| `plugins/senior-review/commands/code-review.md` | The 7c summary line names five phases. Agent B2 row and its lite-pass wording |
| `plugins/senior-review/commands/pr-review.md` | The lite-pass description at its two mentions |
| `plugins/senior-review/skills/review-quality-gates/references/code-review-agents.md` | Agent B2 section, the D1-plus-D3 sentence |
| `plugins/repo-hygiene/**` | New |
| `.claude-plugin/marketplace.json` | New plugin entry at `1.0.0`, `senior-review` version bump, `metadata.version` bump, marketplace description count from 40 to 41 |
| `docs/plugins/senior-review.md` | The `cleanup-auditor` paragraph and the lite-versus-full table |
| `docs/plugins/repo-hygiene.md` | New |
| `CLAUDE.md` | The marketplace 18.3.0 paragraph that describes the capability split by scope, plus a new row in the workflow tables if one is warranted |
| `exports/vscode/_pipelines/.github/agents/review-cleanup-auditor.agent.md` | Mirror of the `cleanup-auditor` edits |
| `exports/vscode/repo-hygiene/.github/**` | New bundle, plus manifest regeneration and `exports/vscode/package.json` version bump |

CI obligations that follow: `lint_plugin_registration.py` requires every new file to be declared in `marketplace.json`; `lint_dependency_graph.py` pass 8 requires the new `senior-review` to `repo-hygiene` edge to be backed by a real spawn or skill load, which 3a and 3b both provide; `check_version_bumps.py` requires both version bumps in the same commit range; `check_export.py` and `gen_extension_manifest.py --check` require the mirror in the same commit.

The migration note for anything pointing at the old shape: `Fix phase: garbage` becomes `/repo-hygiene:tidy` phase `garbage`, and the same for `gitignore` and the scratch half of `docs`. The other four phase names keep their meaning at Step 7c.

## Section 5: weaknesses of this design

Stated by the author, per the packet contract of the peer-review protocol.

1. **The boundary needs a split in its first application.** Six phases classify cleanly and the seventh, `docs`, has to be cut in half. A distinction that cannot decide its own last case may be a description of the current phase list rather than a principle. The alternative reading is that `docs` was always two phases wearing one name, which the current 7c reference half-admits by giving it the only per-item confirmation rule of the seven.
2. **The `brand` assignment may be wrong.** It is assigned to `senior-review` because renaming needs a grep of the old name in the source. But the detection in D2 is mostly filename matching plus `git log --diff-filter=R --name-status -M`, which is filesystem and git evidence, exactly the class assigned to `repo-hygiene`. Detection and application may fall on opposite sides of the boundary for this phase alone.
3. **The pain is asserted, not measured.** The claim that the build-and-test gate is a real cost for the `garbage` and `gitignore` phases rests on reading the workflow, not on a record of runs where it hurt. No 7c run log was consulted for this document, and none may exist.
4. **Discoverability regresses.** A user who wants "clean up my repo" now has to know which of two commands owns their case, and the answer depends on a distinction about evidence classes that is invisible from the outside. The current single entry point is worse architecture and better ergonomics.
5. **A 41st plugin is permanent surface.** Every plugin carries a marketplace entry, a docs page, a VS Code bundle, and a mirror obligation on every future change. The moved content is roughly one dimension and three phases, which is small for a plugin.

## Non-goals

- Not rewriting any moved check. The content moves verbatim; behavior changes only where the phase list forces it.
- Not changing the 7c pre-flight, baseline, gate, or commit shape for the five phases that stay.
- Not touching `/testing:test-consolidate`, which keeps ownership of test-file bulk removal.
- Not reviving `/senior-review:cleanup-dead-code`, retired in marketplace 18.3.0.
- Not adding a `repo-hygiene` degrade path. Per the standing dependency policy, the dependency is hard and a failed spawn is a broken install to report, never a dimension to skip.
