# codebase-xray incremental update: snapshot, change set, carried claims

**Date**: 2026-09-03
**Plugin**: `codebase-xray` (kernel under `plugins/codebase-xray/`)
**Status**: approved in session, direction and sections; the mtime fast path was the user's amendment

## 1. Goal

An X-ray today is rebuilt from nothing every time it runs. On a project that has already been analyzed, that is the whole reading cost paid again to re-derive claims that have not changed. The goal is to make a run **updatable**: a later run starts from an earlier one, finds mechanically what changed in the tree since then, re-reads only that, carries every unaffected claim over verbatim, and records what it did. Each run points at its parent, so the chain of runs under `.deep-dive/runs/` is the analysis history.

Versioning the output in git is the user's business and is out of scope. What the plugin owes is: a snapshot of the tree it analyzed, a diff of that snapshot against the current worktree, a run that focuses only on the diff, and a lineage.

## 2. Success criteria

1. A run records what it analyzed: a manifest of every file and symbol it saw, with content hashes, plus the git commit as metadata.
2. A later invocation of `/codebase-xray:analyze` on the same target detects the previous run, computes the change set without spending model tokens, and offers the incremental path at the scope checkpoint with the numbers that justify it.
3. In an incremental run the model reads only the files in the change set. Every claim not affected by the change set is carried over byte-for-byte, with its `file:line` citations renumbered where lines shifted.
4. Every affected claim is re-derived, every new symbol gets its claims, every removed symbol loses its claims, and no stale marker survives to publication. The last property is checked mechanically before the publish step.
5. The published mirror is indistinguishable in layout from a full run: downstream consumers change nothing.
6. `changes.md` in the run directory says what changed in the code and what happened to each affected claim. `state.json` and `runs.json` record the parent run.
7. The diff works on a dirty worktree and on a tree that is not a git repository. Git is never required.
8. `/codebase-xray:team-analyze` gets the same behaviour at partition granularity.

## 3. Terms

- **Snapshot**: `$RUN_DIR/snapshot/manifest.json`, the mechanical record of the tree a run analyzed.
- **Parent run**: the completed run an incremental run starts from. Always the `latest_completed` run in `runs.json` whose target normalizes to the same path.
- **Change set**: `$RUN_DIR/changes.json`, the mechanical diff between the parent snapshot and the current worktree, plus the claims that diff affects.
- **Affected file**: a file added, removed or modified since the snapshot, or a file that imports a modified or removed file (one hop).
- **Affected claim**: a line in a parent phase file that cites an affected file or a changed symbol.
- **Carried claim**: a parent claim copied into the child run unchanged, apart from citation renumbering.

## 4. Snapshot

### 4.1 When and who

The orchestrating command writes the snapshot right after scope confirmation and before Phase 0, over the confirmed target. It captures the tree the run is about to read. `team-analyze` writes one snapshot over the whole target in its Phase 0, before partition workers start; workers never touch it.

The writer is a new stdlib-only script, `${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/snapshot.py`:

```
python snapshot.py write <target> --out <run-dir>/snapshot/manifest.json
```

It imports `parse_file` from the existing language adapters. It adds no parser and no dependency.

### 4.2 Format

```json
{
  "schema": 1,
  "target": "src",
  "root": "<absolute repository root the paths are relative to>",
  "created_at": "2026-09-03T10:12:00Z",
  "git": {"commit": "d5a11cef", "branch": "master", "dirty": true},
  "files": {
    "src/orders/service.py": {
      "size": 4210,
      "mtime": 1756890000.417,
      "hash": "sha256:...",
      "language": "python",
      "lines": 132,
      "symbols": {
        "OrderService":        {"kind": "class",    "start": 14, "end": 96,  "hash": "sha256:..."},
        "OrderService.place":  {"kind": "method",   "start": 22, "end": 58,  "hash": "sha256:..."},
        "OrderService.cancel": {"kind": "method",   "start": 60, "end": 96,  "hash": "sha256:..."},
        "retry_policy":        {"kind": "function", "start": 99, "end": 132, "hash": "sha256:..."}
      }
    },
    "src/orders/README.md": {"size": 900, "mtime": 1756880000.0, "hash": "sha256:...", "language": null, "lines": 30, "symbols": {}}
  }
}
```

Rules:

- **Paths** are POSIX, relative to the repository root when the target is inside a git repository, otherwise relative to the target itself. `root` records the base so a later diff can resolve them.
- **`git`** is `null` outside a repository. `dirty` means the worktree differed from `HEAD` when the snapshot was written. It is metadata for the report and the lineage; nothing in the diff depends on it.
- **File identity** is `path` plus `size`, `mtime` and `hash`. The hash is the truth. `size` and `mtime` exist for the fast path in section 5.1.
- **Symbols** come from the adapters: classes, functions, methods (qualified `Class.method`), and the SQL and PL/SQL kinds the adapters already emit. `start` is the adapter's line. `end` is the exact end line where the adapter has it (Python, from the stdlib `ast` end line, which requires a new optional `end_line` field on `FunctionInfo` and `ClassInfo`, `None` everywhere else) and otherwise the line before the next symbol's `start` in file order, or the last line of the file for the last symbol. A class span contains its methods, so editing a method changes the method hash and the class hash. That is intended: a claim about the class as a whole is affected too.
- **Symbol hash** is the hash of the raw lines in the span. A whitespace-only or comment-only edit changes it. Accepted: a false positive costs one re-derivation, a stale claim costs trust.
- **A file whose extension is a recognized document type** (`DOC_EXTENSIONS` in `snapshot.py`: `.cfg`, `.ini`, `.json`, `.md`, `.ps1`, `.rst`, `.sh`, `.toml`, `.txt`, `.xml`, `.yaml`, `.yml`) gets a file entry with `language: null` and no symbols. Claims about those files are affected whenever the file is.
- **A file whose extension is neither a supported language nor a recognized document type never enters the manifest at all**, not even as a hash. A claim citing it is carried forward without being re-checked. This is a known limit, accepted because the X-ray reads only its seven supported languages plus documents; pulling in every binary and image would bloat the manifest for files no claim can cite by content.
- **Excluded paths** are the same list `team-analyze` always excludes (`node_modules/`, `dist/`, `build/`, `.next/`, `target/`, `vendor/`, `__pycache__/`, `.venv/`) plus `.git/` and the run's own `.deep-dive/`.
- **Forbidden files** (the list in the workflow's `## Forbidden Files`) never appear in the manifest, not even as a hash. Their existence is recorded in the phase files as today, not in the snapshot.

The snapshot lives inside the run directory, so the `write-confinement` policy covers it without change.

## 5. Change set

```
python snapshot.py diff <parent-run-dir> <target> --out <run-dir> [--verify] [--threshold 0.4] [--flags <json>]
```

Reads the parent manifest, walks the current worktree with the same exclusions, and writes `changes.json` and the mechanical part of `changes.md` into the new run directory. No model token is spent.

### 5.1 File comparison

For every path in the manifest that still exists: if `size` and `mtime` both match, the file is **unchanged** and is neither read nor parsed. Otherwise it is hashed; an equal hash means unchanged (a checkout or a `touch` moved the mtime, nothing else), a different hash means **modified**. Paths in the worktree absent from the manifest are **added**; manifest paths absent from the worktree are **removed**. `--verify` hashes every file regardless of `size` and `mtime`.

### 5.2 Symbol comparison

Every modified file is parsed again. Symbols are matched by qualified name: present on both sides with equal hash is **unchanged**, with different hash is **changed**; present only in the new parse is **added**, only in the manifest is **removed**. Every symbol of an added file is added; every symbol of a removed file is removed. For each unchanged symbol in a modified file the diff records `start_old`, `end_old` and `start_new`: mapping a bare `path:line` citation onto its new position needs the old span, not just the old start.

### 5.3 Blast radius

Every manifest entry records the file's internal imports, so the reverse edges are a lookup rather than a search: the index is built over the current view of the tree (the manifest's imports for unchanged files, the fresh parse for added and modified ones), and an import specifier is resolved to a path by candidate extension and package-entry matching, preferring the importer's own directory when several paths match. For every modified or removed file, the files importing it are **importers**, one hop, never the transitive closure: on most codebases the closure is the whole tree, which is the full run by another name. `affected_files` is the union of added, removed, modified and importers.

Two known limits, both erring toward re-reading rather than toward silence. A Python `from . import x` records no module and produces no edge. An ambiguous specifier that resolves to several paths outside the importer's directory produces no edge either. In both cases the changed file itself is still affected; only the importer edge is missed.

### 5.4 Affected claims

The script scans every phase file of the parent (`01` to `07`, plus `08-interconnect-map.md` in a team run) line by line for citations, and matches each against the change set. Citation forms recognized: `path:line`, `path::Symbol`, `path::Symbol.member`, and a bare `path` inside backticks or a table cell. A cited path matches a manifest path when one is a suffix of the other at a path-segment boundary, since phase files cite paths the way the model wrote them.

| Citation | Verdict |
|---|---|
| any citation of an added or removed file | affected, `file-added` or `file-removed` |
| `path::Sym` where `Sym` or a prefix of it is changed or removed | affected, `symbol-changed` or `symbol-removed` |
| `path::Sym` where `Sym` is unchanged, in a modified file | carried; any `path:line` beside it renumbered |
| `path:line` alone, in a modified file, line inside an unchanged symbol span (old numbering) | carried, renumbered |
| `path:line` alone, in a modified file, line outside every unchanged span | affected, `line-outside-known-symbol` |
| any citation of an importer, not itself modified | affected, `importer` |
| any citation of an unchanged file | carried |

A line that carries several citations is affected if any of them is. Each affected claim is recorded with its phase file, line number, nearest enclosing heading and reason.

### 5.5 Output

```json
{
  "schema": 1,
  "parent_run": "src-20260901-101200",
  "base_snapshot_created_at": "...",
  "computed_at": "...",
  "git": {"commit": "...", "branch": "...", "dirty": false},
  "files": {"added": [], "removed": [], "modified": ["src/orders/service.py"]},
  "symbols": {
    "added":   [{"file": "src/orders/service.py", "symbol": "OrderService.refund", "kind": "method"}],
    "removed": [],
    "changed": [{"file": "src/orders/service.py", "symbol": "OrderService", "kind": "class"},
                {"file": "src/orders/service.py", "symbol": "OrderService.place", "kind": "method"}]
  },
  "renumber": {"src/orders/service.py": [{"symbol": "retry_policy", "start_old": 99, "end_old": 132, "start_new": 121}]},
  "importers": [{"file": "src/api/orders.py", "imports": ["src/orders/service.py"]}],
  "affected_files": ["src/orders/service.py", "src/api/orders.py"],
  "claims": [
    {"phase_file": "03-flows.md", "line": 118, "section": "## Critical Paths",
     "cites": ["src/orders/service.py::OrderService.place"], "reason": "symbol-changed"}
  ],
  "totals": {"files_in_snapshot": 41, "affected_files": 2, "ratio": 0.049, "claims_affected": 9},
  "recommendation": "incremental",
  "reasons": []
}
```

`recommendation` is one of:

- `none`: no file affected. The tree is what the parent analyzed.
- `full`: with a reason in `reasons`, any of: `ratio` above `--threshold` (default `0.4`); parent has no manifest (a run from before this feature); parent `status` is not `complete`; `--flags` differ from the parent's `flags` in `state.json` (an update of a lite run is lite; asking for full over a lite parent is a full run, because phases 3, 4 and 6 have nothing to carry).
- `incremental` otherwise.

`changes.md` gets its first three sections from the script: `## Code changes` (files and symbols, with the git line), `## Blast radius` (importers), `## Affected claims` (the table). The model appends the rest in section 6.5.

## 6. The incremental run in `/codebase-xray:analyze`

### 6.1 Pre-flight, new step 1b: detect an update base

After the run is resolved and before state is initialized. Unless `--no-update` was passed:

1. Read `runs.json`. Take `latest_completed`. If its recorded target normalizes to the same path as this invocation's target and `.deep-dive/runs/<id>/snapshot/manifest.json` exists, it is the candidate parent.
2. Run `snapshot.py diff <parent-run-dir> <target> --out $RUN_DIR --flags <this run's flags>`.
3. Read `recommendation`.

`--update` makes step 1 mandatory: no candidate parent is an error that names the reason and points at a full run. `--no-update` skips the step entirely.

### 6.2 Scope confirmation

The existing checkpoint gains the numbers and reorders its options by the recommendation.

With `incremental`:

```
X-ray target: src
Run: src-20260903-101500   parent: src-20260901-101200 (commit d5a11cef, 2 days ago)
Since parent: 1 file modified, 0 added, 0 removed, 2 symbols changed, 1 added, 1 importer
Affected claims: 9 of 214 (03-flows: 4, 02-interfaces: 3, 05-risks: 2)
Files to read: 2 of 41

1. Incremental update from src-20260901-101200 (reads 2 files)
2. Full analysis (reads 41 files)
3. Cancel
```

With `full`, option 1 is the full analysis and the incremental appears second, with the reason printed (for example `ratio 0.62 over threshold 0.4`); the user may still pick it. With `none`, the checkpoint says the tree is unchanged since the parent and offers a full analysis or exit. Without a candidate parent the checkpoint is exactly today's.

An incremental run inherits `flags` from the parent. `--critical`, `--comments`, `--depth`, `--phase` and `--docs-only` on the command line make the flags differ, which the diff reports as `full`.

### 6.3 Carry step

```
python snapshot.py carry <parent-run-dir> <run-dir>
```

Mechanical, before any phase runs:

1. Copy the parent's `01` to `06` (those that exist) and `knowledge/` into the run directory.
2. Rewrite every carried `path:line` citation in a modified file using `renumber`: `line_new = start_new + (line - start_old)` for the span the line fell in.
3. Insert, immediately above every affected claim line, a marker: `<!-- xray:stale reason=symbol-changed cites=src/orders/service.py::OrderService.place -->`.
4. For every removed symbol and removed file, insert a marker with `reason=symbol-removed` or `file-removed` above each claim citing it, so the model retires rather than rewrites.
5. Append a `## Added symbols` list to `changes.md` naming what has no claim yet, per phase file it belongs to (`01`, `02` always; `03`, `04`, `05`, `06` only at full depth).

### 6.4 Execution order, incremental depth

1. **Snapshot** is written first, over the confirmed target (section 4.1). It records the tree this run reads.
2. **Phase 0** runs in full, exactly as today. It is cheap and its leads shape what the re-derivation looks for. Its output overwrites the carried `knowledge/`.
3. **Phases 1 to 6, in order, only where markers exist.** For each phase file in order: open it, find every `xray:stale` marker, and for each one re-derive the claim by reading the affected files it cites and nothing else. Replace the claim, or delete it when the reason is a removal, and delete the marker. Then add claims for the symbols listed under `## Added symbols` for that phase file. A phase file with no marker and no added symbol is not opened by the model at all.
4. **Reading budget.** The model reads only `affected_files`. When re-deriving a flow or a contract genuinely requires a file outside that set (a callee the changed code now reaches), reading it is allowed and is logged under `## Extra reads` in `changes.md` with the claim that needed it. That log is how a future threshold gets tuned from evidence.
5. **Flows.** A flow description that cites even one affected symbol is re-derived as a whole, because flows cite every step and a step that changed can change the steps after it.
6. **Phase 7** is regenerated from the phase files as today. It is a synthesis and costs little.
7. **Check**: `python snapshot.py check <run-dir>` fails if any `xray:stale` marker remains in any phase file, or if any `## Added symbols` entry has no claim citing it in its phase file. A failing check blocks publication; the run stays `in_progress` and the command reports which markers survive. This is the mechanical guarantee behind success criterion 4.
8. **Publish** as today. The mirror receives `01` to `07` and `state.json`; `changes.md`, `changes.json` and `snapshot/` stay in the run directory, since the mirror is the latest-state contract and history lives under `runs/`.

`--phase N` and `--docs-only` are full-run flags: passing them changes `flags`, so the diff already recommends `full`.

### 6.5 What the run records

`state.json` gains:

```json
"parent_run": "src-20260901-101200",
"base_snapshot_created_at": "...",
"git": {"commit": "...", "branch": "...", "dirty": false},
"incremental": {"affected_files": 2, "files_in_snapshot": 41, "claims_affected": 9, "extra_reads": 1}
```

A full run writes `parent_run: null` and `incremental: null`, and still writes `git` and the snapshot: every run from now on is a possible parent.

`changes.md` after the model's pass has these sections in this order: `## Code changes`, `## Blast radius`, `## Affected claims` (from the script), `## Added symbols` (from the carry step), then `## Claims confirmed` (affected claims re-derived to the same conclusion), `## Claims revised` (old and new text, one row each), `## Claims retired`, `## Claims added`, `## Extra reads`. The first line under the title states the parent run and the commit range when git is present.

`runs.json` entries gain `parent_run` (`null` for a full run). The registry schema number stays 2: the field is additive and readers that ignore it lose nothing. The chain of `parent_run` values is the history; no other structure is added.

### 6.6 Completion output

The summary printed today gains two lines: the parent run, and the counts of carried, revised, retired and added claims, with a pointer at `changes.md`.

## 7. `/codebase-xray:team-analyze`

Partition granularity, deliberately coarser than section 6:

1. **Parent** must be a completed team run on the same target whose partition names are the same set as this run's detection produces. Anything else is a full run, with the reason stated at the checkpoint.
2. **Diff** runs once over the whole target. Each partition's affected files are `affected_files` filtered by partition path.
3. **Untouched partitions** (no affected file) are copied verbatim from the parent's `partitions/<name>/` into the run. No worker is spawned for them.
4. **Touched partitions** run both waves in full, exactly as a fresh run would. Workers never see the change set and their roles do not change. Symbol-level carry inside a worker is out of scope (section 10).
5. **Synthesis and the interconnect map** always run, over the mix of copied and fresh partition outputs, because both are cross-partition by construction.
6. The checkpoint lists partitions as `unchanged (copied)` or `re-analyzed (N affected files)`, and the same `full` reasons as section 5.5 apply, computed over the whole target.

`state.json` and `runs.json` record `parent_run` as in section 6.5; `changes.md` holds the script's three sections plus a `## Partitions` table.

## 8. Skill, documentation, tests, evals

- **`xray-method` SKILL.md.** The run layout in `## Concurrent Runs Model` gains `snapshot/manifest.json`, `changes.json` and `changes.md`, and a rule 7, **Lineage**: a run records its parent, the chain is the history, and a mirror consumer never needs it. A new section `## Incremental Updates` states the snapshot and change-set contracts (sections 4 and 5, condensed), the reading budget, and the check that gates publication. `## Script Commands` gains `14. Write a snapshot` and `15. Diff, carry, check`.
- **`analyze.md`** gains pre-flight step 1b, the checkpoint variants, `### Incremental depth` under `## Execution Order`, the state fields, and two quick examples (`--update`, `--no-update`). **`team-analyze.md`** gains section 7. The argument hints of both list the new flags.
- **`docs/plugins/codebase-xray.md`** describes the update path and the lineage in one paragraph next to the runs model.
- **Fact anchor.** The run layout listing is stated in SKILL.md and in the plugin doc. Add an anchor on the snapshot path so a rename lands in both.
- **`tests/test_xray_snapshot.py`** is a new file (the existing `test_xray_scripts.py` covers the parsers and stays focused on them): the manifest is deterministic over two writes; editing one function leaves the other symbols' hashes unchanged and changes the class hash when the function is a method; `diff` classifies added, removed, modified files and added, removed, changed symbols; the mtime fast path skips an untouched file and `--verify` does not; a touched but identical file is unchanged; importers are one hop; the claim scan resolves every row of the table in section 5.4; renumbering moves a carried `path:line`; `check` fails on a surviving marker and passes when none remains; the threshold flips the recommendation; a forbidden file never enters the manifest.
- **`evals/codebase-xray/cases/incremental-carry-and-rederive`**: an incremental run reads only affected files, carries unaffected claims byte-for-byte, re-derives every marked claim, retires claims on removed symbols, and writes a new snapshot. Behavioural invariant, in the shape of the existing eight cases.
- **Host rendering.** The new script lives under the skill's `scripts/`, which the compiler already ships to all three hosts. `test_daodan_host_rendering.py` needs no new expectation unless the argument hints are asserted, in which case they are updated.

## 9. Versions and rollout

`codebase-xray` 3.2.0, marketplace minor bump, rebuild all three hosts, one commit for kernel plus generated output per the marketplace workflow. The first run after upgrade is a full run that writes a snapshot; every run after it can be incremental. A parent without a manifest is reported, never guessed at.

## 10. Out of scope, deliberately

- **Symbol-level carry inside team workers.** A touched partition is re-analyzed whole. Making workers carry claims would put the change set into every spawn prompt and change four roles for a saving the partition split already provides most of.
- **`/senior-review:team-review` Phase 1a.** It runs `analyze` on the Phase 0 file scope; when that scope matches a previous run's target it gets the incremental path from the auto-detect, and otherwise it does not. No change to that workflow in this pass.
- **Transitive blast radius.** One hop, measured by `## Extra reads` over real runs before anything wider is considered.
- **Committing `.deep-dive/`.** The user's choice; `repo-hygiene` keeps treating it as pipeline output.
- **A standalone `/codebase-xray:update` command.** `--update` on `analyze` is the explicit form; a second entry point would duplicate the pre-flight for no new behaviour.

## 11. Alternatives rejected

- **Git-range delta (`<run-commit>..HEAD`)** as the source of the change set. Needs a clean commit at every run, cannot see a dirty worktree, which is exactly the state a developer is in when they want the X-ray refreshed, and fails outside a repository. Git stays as metadata.
- **File-level snapshot only.** Simpler, but a single-function edit in a large module would invalidate every claim about the module. Kept only as the granularity for languages the adapters do not parse.
- **A separate delta document instead of updated phase files.** Downstream consumers read `01` to `07` from the mirror and would have to merge the delta themselves. The carried-plus-re-derived phase files keep the contract; `changes.md` is the delta as a record, not as the product.
- **Trusting `mtime` alone.** A checkout rewrites mtimes over the whole tree; hashing on mismatch costs one read per touched file and removes the false positives.
