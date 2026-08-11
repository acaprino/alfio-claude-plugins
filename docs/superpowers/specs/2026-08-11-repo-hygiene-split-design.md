# repo-hygiene: splitting repo maintenance out of senior-review

**Date**: 2026-08-11
**Status**: design, awaiting implementation plan
**Affects**: new plugin `repo-hygiene`; `senior-review` (agent `cleanup-auditor`, commands `code-review`, `pr-review`, `team-review`, skill `review-quality-gates`); `.claude-plugin/marketplace.json`; `exports/vscode/`; `docs/plugins/`

## Problem

`senior-review:cleanup-auditor` currently detects six dimensions under one name: dead code (D1),
asset hygiene (D2), VCS hygiene (D3), dependency hygiene (D4), documentation and historical-artifact
hygiene (D5), and lifecycle archaeology (D6). Removal for all of them lives in Step 7c of
`/senior-review:code-review --commit`, as seven phases: `garbage`, `brand`, `assets`, `gitignore`,
`deps`, `exports`, `docs`.

Two unrelated kinds of work are bundled here.

Finding a dead export is a code-comprehension problem. It needs to know about dynamic imports,
dependency-injection registration, framework conventions such as Next.js `pages/` and `app/`, and
module augmentation in `*.d.ts`. Getting it wrong breaks the build or, worse, breaks runtime in a
path no test covers. That is why the `exports` phase runs ruff, then Knip verified by Grep, then
vulture behind explicit user approval, in ascending order of risk.

Finding a tracked `dist/` directory, a `nul` file from a shell redirection, or a `.gitignore` missing
`__pycache__/` is a filesystem-and-git problem. It needs `git ls-files` and a regex. Getting it wrong
breaks nothing, which is why the `garbage` phase is documented as "safest phase, no build or
dependency impact expected".

Three concrete consequences of the bundling, each independently sufficient to motivate the split:

1. **The Step 7c pre-flight blocks trivial work on a broken repo.** Step 7c halts if the baseline
   build or tests already fail. Correct for `exports`. Absurd for `garbage`: a repository with a red
   build currently cannot have a `.DS_Store` removed by this toolkit, because a gate protecting
   something the phase does not touch refuses to open.

2. **The install cost is disproportionate.** `senior-review` 10.1.0 declares seven hard dependencies
   (`agent-teams@claude-code-workflows`, `codebase-xray`, `abstraction-architect`, `react-development`,
   `platform-engineering`, `typescript-development`, `testing`), and `codebase-xray` and
   `abstraction-architect` pull further. Fixing a `.gitignore` should not require the review stack.
   This is the same objection that removed the Context Builder role from `research` in marketplace
   21.0.0.

3. **The scope seam is a symptom, not an accident.** Whole-codebase hygiene detection is only
   reachable through `/senior-review:team-review`, because `/senior-review:code-review` is diff-scoped
   by construction (Cases A through E all resolve to a diff). Repo hygiene is repo-scoped by nature.
   Hosting it inside a diff-scoped review command is what forces the awkward handoff where
   `team-review` detects across the repo and `code-review` executes against a diff.

## Decisions

Each decision below records the alternatives that were considered and why they were rejected. The
rationale is part of the artifact deliberately: a decision presented as a bare conclusion cannot be
judged, only accepted or contradicted.

### D-1: `repo-hygiene` owns its own removal

The new plugin performs detection **and** removal for its categories. It is not detection-only.

**Rationale.** The point of the split is that this class of work should cost one command and a few
seconds. If removal stayed in Step 7c, a user wanting to delete a stray `nul` file would still
install `senior-review`, still pull its dependency tree, and still run a diff-scoped review. That
reproduces the problem the split exists to solve.

**Rejected: detection-only, removal stays in Step 7c.** Keeps Step 7c intact at seven phases and
avoids duplicating any removal machinery. Rejected because it preserves every ergonomic defect
listed in the Problem section while adding a plugin boundary, which is the worst of both.

**Rejected: detection-only, no executor anywhere.** The removal commands appear in the finding text
and the user runs them, which is what `cleanup-auditor` already does for stashes and worktrees.
Maximum safety, zero automation. Rejected as a regression against the current state: Step 7c already
automates `garbage` and `gitignore` today, so shipping this would remove a working capability.

### D-2: the boundary rule is "does resolving it require reading source code?"

If resolving a finding requires understanding the source, it stays in `senior-review`. If the
filesystem and git are sufficient, it moves to `repo-hygiene`.

**Rationale.** The rule is stateable in one sentence, decidable per finding without judgment calls in
most cases, and it generates the allocation rather than enumerating it, so it also governs dimensions
added later. It aligns the boundary with the actual difference in required competence, which is also
what determines whether a build-and-test gate is needed.

**Rejected: "files or symbols?"** Whole files move, symbols inside files stay. Produces a larger and
arguably more useful standalone plugin, since orphan assets and dead whole files would move too.
Rejected because orphan assets carry their code comprehension with them: the fix-loop rule for the
`assets` phase requires grepping partial basenames to catch references built from template literals.
The boundary would leak.

**Rejected: "can removal break the build?"** Aligns the boundary to the gates instead of to the work.
Rejected because it moves the entire `docs` phase into `repo-hygiene`, and that phase has the highest
false-positive rate of the seven and requires per-item confirmation with last-modified date and
checklist completion shown. Judging whether a plan document is stale is not a filesystem operation.

### D-3: `team-review` gains a second always-on dimension

`senior-review` declares `repo-hygiene` as a hard dependency and `/senior-review:team-review` gains a
second always-on dimension, "Repo hygiene", spawning the new plugin's agent. The existing "Codebase
hygiene" dimension survives, slimmed.

**Rationale.** This is the established pattern in this marketplace: `testing:test-suite-auditor` and
`typescript-development:type-safety-auditor` both live in the plugin that owns them and are spawned by
`senior-review` as dimensions. `cleanup-auditor` is currently the only dimension agent that lives
inside `senior-review` while addressing something other than correctness of the code. A full review
stays full.

**Rejected: `team-review` drops repo hygiene entirely.** Follows the `research` precedent from 21.0.0:
remove the capability rather than soften the dependency. Rejected because the transitive cost runs the
other way here. `senior-review` already pulls seven plugins, so one more is marginal, whereas a review
that stops reporting a tracked `dist/` loses real coverage.

**Rejected: `team-review` prints a pointer without spawning.** Explicitly forbidden by the
mandatory-dependency policy of marketplace 21.0.0, which bans "skip with a note" prose precisely
because a blind spot announced in a status line is still a blind spot.

### D-4: the lite pass keeps its VCS check, sourced from `repo-hygiene`

Agent B2 inside `/senior-review:code-review` and `/senior-review:pr-review` continues to check the
diff for newly tracked generated artifacts and `.gitignore` gaps. The rule set it applies (the path
regexes, the per-ecosystem expected-pattern table) lives in `repo-hygiene`'s skill and is loaded from
there via the declared hard dependency from D-3.

**Rationale.** Catching a `dist/` added to git costs least at review time, before the merge. Removing
that check would trade a real detection for boundary purity. Sourcing the rules from one place keeps
the split from introducing the duplication it is meant to remove.

**Rejected: drop VCS hygiene from the lite pass.** Sharper boundary, `senior-review` genuinely
slimmer. Rejected on the coverage argument above.

**Rejected: keep a duplicate rule set in `senior-review`.** No runtime cross-plugin load needed.
Rejected because two copies of the same regexes and the same per-ecosystem pattern table will
diverge, which is the defect this split should eliminate rather than introduce.

### D-5: the removal flags mirror `senior-review`

`--fix` edits and verifies, leaving the working tree modified with no commits. `--commit` implies
`--fix` and adds one commit per category.

**Rationale.** This is the contract `/senior-review:code-review` has carried since senior-review 8.0.0,
so a user who knows one command knows the other. Unlike Step 7c, `--fix` without commits is genuinely
safe here, because there is no build-and-test gate whose revert mechanism the commits would be.

**Rejected: `--commit` only.** Mirrors Step 7c's requirement. Rejected because Step 7c requires
`--commit` for a specific reason that does not apply: its per-phase commits are how it reverts a
failed build gate. With no gate, forcing a commit on someone who wanted to delete two `.DS_Store`
files is friction without a purpose.

**Rejected: interactive confirmation per category, no flags.** Safest against the irreversible-deletion
problem below. Rejected because it is not scriptable and diverges from every other command here. The
irreversibility problem is addressed directly by D-6 instead.

### D-6: untracked deletions are quarantined, never removed

Two tiers, decided by whether git already has the file:

- **Tracked**: `git rm` or `git rm --cached`. Recoverable from history. Proceeds under `--fix` or
  `--commit` normally.
- **Untracked**: never `rm`. The file is **moved** into `.repo-hygiene/quarantine/<timestamp>/`,
  preserving its path relative to the repo root. The quarantine directory is added to `.gitignore` by
  the same run. The user deletes the quarantine directory when satisfied.

**Rationale.** For an untracked file, neither git nor a per-category commit is a revert mechanism:
once deleted it is gone. Since D-5 chose a `--fix` mode that leaves no commits, an untracked deletion
under `--fix` would be the only unrecoverable operation in the design. Quarantine costs a move instead
of a delete and makes every operation in the plugin reversible. The marketplace already uses this
shape: `/testing:test-audit --fix` quarantines to `tests/_quarantine/` rather than deleting.

This is not a separate safety feature bolted on. It is what makes D-5's choice defensible.

## Boundary allocation

Applying D-2 to the existing seven Step 7c phases:

| Step 7c phase today | Destination | Why |
|---|---|---|
| 1 `garbage` | **repo-hygiene** | Filesystem and git suffice |
| 2 `brand` | senior-review | Requires grepping the old name across source |
| 3 `assets` | senior-review | Requires grepping dynamic references built from template literals |
| 4 `gitignore` | **repo-hygiene** | Filesystem and git suffice |
| 5 `deps` | senior-review | Requires real usage of imported symbols |
| 6 `exports` | senior-review | Code comprehension, the pure case |
| 7 `docs` | **splits** | Scratch directories and orphan doc-assets move; stale plans, ADRs, and stale references stay, being judgments about content |

Also moving: all of D3 (VCS hygiene), and D6's git auxiliary state (stashes idle beyond 90 days,
worktrees pointing at deleted branches or paths, local branches whose upstream is gone,
merged-but-undeleted branches).

Staying: D1, D2, D4, D5's plan and ADR judgment, and D6's archaeology over code artifacts (the
session-transcript and commit-sequence inference that establishes whether a migration completed).

**Resulting phase sets.** Step 7c goes from seven phases to five: `brand`, `assets`, `deps`,
`exports`, `docs`. Its pre-flight, baseline capture, gate-after-every-phase rule, and grep-before-delete
rule are unchanged, and now guard only things that can actually break a build.

`repo-hygiene` gets four of its own, with no build-and-test gate: `garbage`, `gitignore`, `scratch`,
`git-state`.

## Architecture

Three components, chosen so that detection is described once and consumed three times.

### Command: `/repo-hygiene:audit`

Runs detection **inline**, not through a subagent. The detection is roughly ten git invocations plus
a handful of file reads, and the value of this command depends on it being fast enough to run
casually. Owns removal under `--fix` and `--commit` per D-5, and owns the quarantine mechanism per
D-6.

Argument shape: `[path] [--fix] [--commit] [--categories=garbage,gitignore,scratch,git-state]`.

### Agent: `repo-hygiene:repo-hygiene-auditor`

Exists because `/senior-review:team-review` needs a `subagent_type` to spawn for the dimension added
in D-3. Report-only: it never removes anything, matching `cleanup-auditor`'s existing prime directive
and this marketplace's general split between detection and removal. Writes to the output path the
pipeline gives it, inline otherwise.

### Skill: `repo-hygiene:repo-hygiene`

Holds the rule tables, and is the single source of truth for all three consumers:

1. `/repo-hygiene:audit`, inline
2. `repo-hygiene:repo-hygiene-auditor`, when spawned by `team-review`
3. `senior-review`'s Agent B2 lite pass, per D-4

Contents: the tracked-generated-artifact path regexes, the filesystem-garbage regexes, the
per-ecosystem `.gitignore` expected-pattern table (Node, Vite, Next.js, Tauri, Rust, Python, Android,
iOS, platform), the ignore-rule archaeology procedure including the `git check-ignore -v` provenance
step, the git auxiliary state queries and their thresholds, and the residue classification vocabulary
this plugin shares with `cleanup-auditor` (confidence tiers CONFIRMED / HIGH / MEDIUM / LOW; actions
DELETE, KEEP, KEEP+IGNORE, DELETE+IGNORE, DELETE+PREVENT-GENERATION, UNIGNORE, REVIEW).

**Constraint.** `senior-review` must load this through the skill mechanism
(`repo-hygiene:repo-hygiene`), never by reading `plugins/repo-hygiene/skills/...` by path. The
bundled-path linter (`scripts/lint_bundled_paths.py`) forbids one plugin reaching into another's
files by path, and such a read fails at runtime for any installed user, since plugins install into
Claude Code's cache rather than into a checkout of this repository.

## Changes to `senior-review`

| File | Change |
|---|---|
| `agents/cleanup-auditor.md` | Remove D3 entirely. Remove the git auxiliary state block from D6. Remove scratch directories and orphan doc-assets from D5. Update the agent description, the dimension count (six becomes five), the statistics table, and the recommended execution order, which currently lists all seven Step 7c phases. Add a cross-reference naming `repo-hygiene` as the owner of what left, so a user reading a report knows where the rest is. |
| `commands/code-review.md` | Step 7c drops from seven phases to five. Update the Step 7c summary line and the phase list. |
| `skills/review-quality-gates/references/code-review-fix-loop.md` | Same, in the authoritative copy: remove phases 1 and 4, renumber, split phase 7's scratch-directory clause out. |
| `skills/review-quality-gates/references/code-review-agents.md` | Agent B2 keeps its VCS check but sources the rules from the `repo-hygiene` skill per D-4, instead of carrying inline regexes. Its `Fix phase:` instruction now names phases across two plugins, so the finding format needs to say which. |
| `commands/team-review.md` | Add "Repo hygiene" to the always-on dimensions table and to the dimension-to-agent mapping table. Narrow the existing "Codebase hygiene" row to the five surviving dimensions. |
| `commands/pr-review.md` | Same lite-pass rule sourcing as `code-review`. |

## Marketplace and CI contracts

Six CI checks run on push to `master`. Each is satisfied as follows.

1. **`scripts/lint_dependency_graph.py`**: `senior-review` gains `"repo-hygiene"` in `dependencies`
   (bare name, since it is local to this marketplace). `repo-hygiene` itself declares no
   dependencies. The forbidden edge `codebase-xray → senior-review` is untouched. Per the 21.0.0
   policy, `optionalDependencies` is not used, and `repo-hygiene` must not appear in any plugin's
   `optionalDependencies`, which the linter enforces mechanically.

2. **`scripts/lint_bundled_paths.py`**: the new plugin's self-references use `${CLAUDE_PLUGIN_ROOT}/...`
   or skill-relative `references/...`. `senior-review` reaches `repo-hygiene` only through the skill
   mechanism, never by path. See the constraint under Architecture.

3. **`scripts/lint_plugin_registration.py`**: the `repo-hygiene` entry in `marketplace.json` must list
   its command, its agent, and its skill. An agent present on disk but absent from the array does not
   exist at runtime, and `subagent_type: repo-hygiene:repo-hygiene-auditor` would fail with "Agent
   type not found", taking the new `team-review` dimension down with it. This check exists because
   senior-review 9.0.0 shipped exactly that defect.

4. **`.claude/skills/downstream-exports/scripts/check_export.py`**: a new bundle
   `exports/vscode/repo-hygiene/.github/` is required, and the `_pipelines` bundle that carries
   `senior-review` needs its mirrored copies updated for every file changed above.

5. **`gen_extension_manifest.py --check`**: the export adds one agent and one prompt, so the manifest
   must be regenerated and `exports/vscode/package.json` `version` bumped.

6. **`scripts/check_version_bumps.py`**: `senior-review` goes to **11.0.0** (breaking: Step 7c loses
   phases and `cleanup-auditor` loses dimensions), `repo-hygiene` starts at **1.0.0**, and
   `metadata.version` goes from 21.4.0 to **22.0.0**.

Documentation: a new `docs/plugins/repo-hygiene.md`, and edits to `docs/plugins/senior-review.md`,
whose Lite / Full / Removal table describes the current seven-phase shape. `CLAUDE.md` needs the new
plugin recorded in the dependency table and the split rule stated, since it currently documents
`cleanup-auditor` as the single owner of all five hygiene dimensions.

## Known weaknesses of this design

Declared deliberately, because a design that presents no weaknesses has usually hidden them.

1. **The boundary rule has a genuinely ambiguous case, and this design resolves it by assertion.**
   Orphan doc-assets (an image in `docs/` referenced by no `.md` file) require grepping content, not
   just listing files, which is the same shape of work as an orphan source asset. D-2 sends orphan
   source assets to `senior-review` and orphan doc-assets to `repo-hygiene`, on the grounds that the
   latter greps documentation rather than source. That distinction is real but thin, and a reasonable
   reviewer could put both on either side. If the rule needs an exception this early, that is evidence
   against the rule.

2. **Removing the build-and-test gate is a removal of protection, justified by a claim about the
   categories rather than by measurement.** The design asserts that `garbage`, `gitignore`, `scratch`,
   and `git-state` cannot break a build. This is true for the documented detection patterns, but the
   `.gitignore` phase appends patterns and runs `git rm --cached`, and an over-broad appended pattern
   could untrack a file some build step reads. The `UNIGNORE` action in the residue vocabulary exists
   precisely because ignore rules can hide files that should be version-controlled, which is the same
   hazard in the other direction. No gate means nothing catches that mistake automatically.

3. **The split raises the cost of every future change to hygiene detection, and the estimate of that
   cost is unmeasured.** Today one agent file changes. Afterwards, a rule change may touch the
   `repo-hygiene` skill, the command that consumes it inline, the agent, `senior-review`'s Agent B2,
   and two export bundles. D-4's single-source-of-truth rule is what keeps this bounded, but it is a
   convention enforced by review, not by any of the six CI checks. Nothing mechanically prevents a
   future edit from reintroducing an inline copy of the regexes in `senior-review`.

## Open questions

- **Command name.** `/repo-hygiene:audit` reads well and matches `--fix` signalling removal, as
  `/testing:test-audit --fix` already does. `/repo-hygiene:tidy` states the removal intent more
  directly. Not decided.

- **Whether `.repo-hygiene/` is the right quarantine location.** It mirrors `.frontend-review/`,
  `.team-review/`, and `.deep-dive/`, but those hold reports rather than user files, and a directory
  holding recoverable data has a different lifetime from one holding a regenerable report.

## Out of scope

- Any change to `dependency-audit`. Its boundary with hygiene work is already documented in both
  directions: it covers CVEs, licenses, and versions from registries, while unused and phantom
  dependency detection stays with `cleanup-auditor` D4.
- Any change to `/testing:test-consolidate`, which keeps ownership of bulk test-file removal.
- Re-litigating the mandatory-dependency policy of marketplace 21.0.0.
- The `python-development` dependency drift noted while reading `CLAUDE.md`, which documents it as a
  `senior-review` dependency though `marketplace.json` no longer lists it. Real, unrelated, tracked
  separately.
