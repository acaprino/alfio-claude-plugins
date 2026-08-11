#!/usr/bin/env python3
"""Concept index freshness and delta partitioning for abstraction-architect.

Stdlib only, deterministic work only. This script never discovers concepts.
It validates the index schema, resolves the three distinct notions of change
(index baseline, repository state, review delta), and partitions the changed
files into those an indexed concept already claims and those it does not.

Every semantic judgement, including whether two representations encode the
same knowledge, belongs to the agent. When any of the three notions of
change cannot be determined (a bad ref, an unreadable listing, a failed git
call), the result is `unusable`, never a silently empty `fresh`.

Usage:

    concept_index.py validate --index PATH
    concept_index.py status   --index PATH [--repo PATH]
                              [--base REF] [--head REF]
                              [--working-tree] [--changed-files PATH]

status prints one JSON object on stdout. Exit code 0 on success, including
the unusable state, which is a normal outcome and not an error. Exit 1 when
validate rejects an index. Exit 2 on bad invocation.
"""
import argparse
import json
import os
import subprocess
import sys

SCHEMA_VERSION = 1
REQUIRED_KEYS = ("schema_version", "generated_from_commit",
                 "generated_from_tree", "generated_at", "scope", "concepts")

# Sibling report artifacts that share a directory with the index file but
# are never passed via --index (see agents/abstraction-architect.md).
SIBLING_ARTIFACT_FILENAMES = ("findings.md", "findings-diff.md")


def git(repo, *args):
    """Run git in repo. Returns (ok, stdout_rstripped).

    -c core.quotePath=false stops git from octal-escaping and quoting any
    path containing a non-ASCII byte. Without it, a real file named
    domain/café_policy.py comes back from `git diff`/`git status` as the
    literal string "domain/caf\\303\\251_policy.py": a path that exists
    nowhere on disk, which this script would then hand to the agent as an
    unmapped changed file while the concept that owns the real file is
    reported clean. The two callers that list changed paths (diff_files,
    worktree_files) also pass -z, which drops quoting entirely, including
    for control characters that core.quotePath alone does not cover.

    Only the trailing newline is stripped. A blanket strip() would eat a
    leading space from the first line of multi-line output such as
    `git status --porcelain`, where a leading space is a meaningful part
    of a status code (" M path"), and that would misalign every path
    parsed from that line.
    """
    try:
        result = subprocess.run(["git", "-c", "core.quotePath=false", *args],
                                cwd=repo, capture_output=True, text=True,
                                encoding="utf-8")
    except OSError:
        # A --repo that does not exist, is not a directory, or no git on
        # PATH: fail like any other git error instead of letting
        # subprocess raise past every caller that expects (ok, out).
        return False, ""
    return result.returncode == 0, result.stdout.rstrip("\r\n")


def load_index(path):
    """Returns (index, error_message). One of the two is always None.

    Beyond key presence, this also checks that `concepts` is a list of
    objects and that each concept's `representations`, when present, is a
    list of objects. The index is authored by a language model, so a shape
    error here (a string where an object belongs, a dict where a list
    belongs) is not exotic, and without this check it reaches partition()
    or validate()'s per-concept loop and crashes both with an
    AttributeError instead of degrading to the normal unusable/FAIL path.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            index = json.load(handle)
    except FileNotFoundError:
        return None, f"index not found at {path}"
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"index at {path} is not readable JSON: {exc}"
    if not isinstance(index, dict):
        return None, "index root is not an object"
    missing = [key for key in REQUIRED_KEYS if key not in index]
    if missing:
        return None, f"index is missing required keys: {', '.join(missing)}"
    if index["schema_version"] != SCHEMA_VERSION:
        return None, (f"incompatible schema_version {index['schema_version']}, "
                      f"this script speaks {SCHEMA_VERSION}")
    concepts = index["concepts"]
    if not isinstance(concepts, list):
        return None, "'concepts' must be a list"
    for position, concept in enumerate(concepts):
        if not isinstance(concept, dict):
            return None, f"concepts[{position}] is not an object"
        representations = concept.get("representations", [])
        if not isinstance(representations, list):
            return None, f"concepts[{position}].representations must be a list"
        for rep_position, rep in enumerate(representations):
            if not isinstance(rep, dict):
                return None, (f"concepts[{position}].representations"
                              f"[{rep_position}] is not an object")
    return index, None


def scope_tree(repo, rev, scope):
    """Tree hash of scope at rev, or None when it cannot be resolved."""
    if scope in (".", "", None):
        ok, out = git(repo, "rev-parse", f"{rev}^{{tree}}")
        return out if ok and out else None
    ok, out = git(repo, "rev-parse", f"{rev}:{scope}")
    return out if ok and out else None


def commit_exists(repo, rev):
    ok, _ = git(repo, "cat-file", "-e", f"{rev}^{{commit}}")
    return ok


def pathspec(scope):
    return [] if scope in (".", "", None) else [scope]


def nul_split(out):
    return [entry for entry in out.split("\0") if entry]


def diff_files(repo, base, head, scope):
    """(ok, files): changed paths between base and head within scope.

    -z NUL-terminates each entry and disables quoting entirely (paired
    with core.quotePath=false on every git() call, see its docstring).
    --no-renames reports a rename as an ordinary delete-and-add of two
    full paths instead of a single record naming only the destination,
    so the concept owning the old path is not silently spared: the file
    its representation points at no longer exists, which is exactly the
    change that invalidates a representation.

    ok is False when the git call itself fails, for example a --base ref
    that does not resolve. Callers must treat that as "the delta cannot
    be determined", which is an unusable condition, never as "nothing
    changed".
    """
    ok, out = git(repo, "diff", "--name-only", "--no-renames", "-z",
                  base, head, "--", *pathspec(scope))
    if not ok:
        return False, []
    return True, nul_split(out)


def worktree_files(repo, scope):
    """(ok, files): staged, unstaged and untracked paths within scope.

    Same -z / --no-renames reasoning as diff_files: no quoted or escaped
    paths, and a rename shows up as its old and new path separately
    rather than only its destination. --untracked-files=all additionally
    asks git to list every untracked file individually rather than
    collapsing a wholly untracked directory into one directory entry;
    the script partitions by file path, so a collapsed directory entry
    would never match a representation's `file` and would silently hide
    every file inside it, index included, from the partition.
    """
    ok, out = git(repo, "status", "--porcelain", "--untracked-files=all",
                  "--no-renames", "-z", "--", *pathspec(scope))
    if not ok:
        return False, []
    return True, [entry[3:] for entry in nul_split(out) if len(entry) > 3]


def own_artifact_paths(repo, index_path):
    """Repo-relative, forward-slash paths of this plugin's own report
    artifacts: whatever file --index names, plus its siblings findings.md
    and findings-diff.md, in whatever directory --index resolves to,
    including the repository root. Returns an empty set when that
    directory cannot be resolved at all (outside repo, or on a different
    filesystem root than --repo on Windows).

    None of these files is under review, so none may appear in
    autodetected git state: without this exclusion, writing or updating
    any of them would make it look like changed content, a concept in
    need of discovery that is actually the discovery record.

    An earlier version excluded the whole containing directory by path
    prefix. That deleted real files from the answer whenever --index
    lived alongside genuine source content (an index at
    docs/concept-index.json swallowed docs/refunds.md too, and its
    owning concept was reported clean while the file was in fact
    modified), and it disabled the exclusion entirely for an index at
    the repository root, where "the containing directory" is the whole
    repository. Naming the files exactly fixes both: every placement is
    protected, and nothing else is.
    """
    try:
        repo_abs = os.path.realpath(repo)
        index_abs = os.path.realpath(index_path)
        rel_dir = os.path.relpath(os.path.dirname(index_abs), repo_abs)
    except (OSError, ValueError):
        # ValueError: --index and --repo resolve to different drives on
        # Windows, which os.path.relpath cannot express as a relative
        # path. Disable the exclusion rather than crash; without it the
        # index just is not excluded, the same degradation already used
        # when --index lives outside repo entirely.
        return set()
    if rel_dir == os.pardir or rel_dir.startswith(os.pardir + os.sep):
        return set()
    prefix = "" if rel_dir == os.curdir else rel_dir.replace(os.sep, "/") + "/"
    names = set(SIBLING_ARTIFACT_FILENAMES)
    names.add(os.path.basename(index_abs))
    return {prefix + name for name in names}


def without_own_artifacts(files, own_paths):
    if not own_paths:
        return files
    return [path for path in files if path not in own_paths]


def partition(index, changed_files):
    """Split changed files into indexed concepts touched and unclaimed files.

    A concept with a missing or empty `concept` name still falls back to
    a positional label (concepts[3], matching validate()'s convention)
    instead of being dropped from the dirty list. Dropping it would
    silently remove its changed files from both halves of the partition,
    the one invariant this function exists to hold: every changed file
    accounted for in exactly one half.
    """
    changed = set(changed_files)
    claimed = set()
    dirty = []
    for position, concept in enumerate(index.get("concepts", [])):
        files = {rep.get("file") for rep in concept.get("representations", [])
                 if rep.get("file")}
        claimed |= files
        if files & changed:
            dirty.append(concept.get("concept") or f"concepts[{position}]")
    unmapped = sorted(path for path in changed if path not in claimed)
    return sorted(dirty), unmapped


def resolve_review_delta(repo, args, scope, own_paths=None):
    """Returns (review_delta, error). error is None on success.

    error is set when the requested delta source could not actually be
    computed (a bad --base ref, an unreadable --changed-files listing, a
    failed working-tree read), so the caller can report unusable instead
    of silently treating "the git call failed" the same as "nothing
    changed".
    """
    if args.changed_files:
        # An explicit list is the caller's deliberate scope, so it is
        # never filtered against own_paths: only autodetected git state
        # is.
        try:
            with open(args.changed_files, encoding="utf-8") as handle:
                files = [line.strip() for line in handle if line.strip()]
        except OSError as exc:
            error = f"cannot read --changed-files {args.changed_files}: {exc}"
            return {"source": "changed-files", "files": []}, error
        return {"source": "changed-files", "files": files}, None
    if args.base:
        head = args.head or "HEAD"
        source = f"{args.base}..{head}"
        ok, raw = diff_files(repo, args.base, head, scope)
        if not ok:
            return ({"source": source, "files": []},
                    f"could not compute the diff for --base {source}")
        files = without_own_artifacts(raw, own_paths)
        return {"source": source, "files": files}, None
    if args.working_tree:
        ok, raw = worktree_files(repo, scope)
        if not ok:
            return ({"source": "working-tree", "files": []},
                    "could not read git status for --working-tree")
        files = without_own_artifacts(raw, own_paths)
        return {"source": "working-tree", "files": files}, None
    return {"source": "none", "files": []}, None


def unusable(reason, index_baseline=None, review_delta=None):
    return {
        "freshness_state": "unusable",
        "reason": reason,
        "index_baseline": index_baseline or {},
        "repository_state": {},
        "review_delta": review_delta or {"source": "none", "files": []},
        "changed_files": [],
        "dirty_indexed_concepts": [],
        "unmapped_changed_files": [],
    }


def status(args):
    repo = args.repo
    index, error = load_index(args.index)
    if error:
        return unusable(error)

    scope = index.get("scope", ".")
    baseline = {
        "commit": index["generated_from_commit"],
        "tree": index["generated_from_tree"],
        "scope": scope,
    }

    ok, head_commit = git(repo, "rev-parse", "HEAD")
    if not ok or not head_commit:
        return unusable(f"{repo} is not a git repository with a HEAD commit",
                        baseline)

    head_tree = scope_tree(repo, "HEAD", scope)
    if head_tree is None:
        return unusable(f"scope {scope!r} does not resolve at HEAD", baseline)

    own_paths = own_artifact_paths(repo, args.index)

    worktree_ok, worktree_raw = worktree_files(repo, scope)
    if not worktree_ok:
        return unusable(f"could not read git status for {repo}", baseline)
    dirty_paths = without_own_artifacts(worktree_raw, own_paths)
    repository_state = {
        "head_commit": head_commit,
        "head_tree": head_tree,
        "dirty": bool(dirty_paths),
    }

    review_delta, delta_error = resolve_review_delta(repo, args, scope, own_paths)
    if delta_error:
        result = unusable(delta_error, baseline, review_delta)
        result["repository_state"] = repository_state
        return result

    if not commit_exists(repo, baseline["commit"]):
        result = unusable(
            f"index baseline commit {baseline['commit'][:7]} is not reachable",
            baseline, review_delta)
        result["repository_state"] = repository_state
        return result

    drift_ok, drift_raw = diff_files(repo, baseline["commit"], "HEAD", scope)
    if not drift_ok:
        result = unusable(
            (f"could not compute the drift between baseline "
             f"{baseline['commit'][:7]} and HEAD"),
            baseline, review_delta)
        result["repository_state"] = repository_state
        return result
    baseline_drift = without_own_artifacts(drift_raw, own_paths)
    drift = baseline_drift + dirty_paths
    changed_files = sorted(set(drift) | set(review_delta["files"]))

    if baseline["tree"] == head_tree and not dirty_paths:
        state = "fresh"
        reason = f"indexed tree matches current tree for scope {scope!r}"
    else:
        state = "delta-stale"
        if dirty_paths and baseline["tree"] == head_tree:
            reason = ("indexed tree matches HEAD but the worktree carries "
                      f"{len(dirty_paths)} uncommitted change(s)")
        else:
            reason = (f"indexed tree {baseline['tree'][:4]} does not match "
                      f"current tree {head_tree[:4]}")

    dirty_concepts, unmapped = partition(index, changed_files)
    return {
        "freshness_state": state,
        "reason": reason,
        "index_baseline": baseline,
        "repository_state": repository_state,
        "review_delta": review_delta,
        "changed_files": changed_files,
        "dirty_indexed_concepts": dirty_concepts,
        "unmapped_changed_files": unmapped,
    }


def validate(args):
    index, error = load_index(args.index)
    if error:
        print(f"FAIL  {error}")
        return 1
    problems = []
    for position, concept in enumerate(index["concepts"]):
        label = concept.get("concept") or f"concepts[{position}]"
        if not concept.get("concept"):
            problems.append(f"{label}: missing 'concept' name")
        representations = concept.get("representations")
        if not isinstance(representations, list) or not representations:
            problems.append(f"{label}: 'representations' must be a non-empty list")
            continue
        for rep in representations:
            if not rep.get("file"):
                problems.append(f"{label}: a representation has no 'file'")
    if problems:
        print("FAIL  concept index:")
        for problem in problems:
            print("        ", problem)
        return 1
    print(f"ok    concept index: {len(index['concepts'])} concept(s), "
          f"schema {index['schema_version']}, baseline "
          f"{index['generated_from_commit'][:7]}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--index", required=True)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--index", required=True)
    status_parser.add_argument("--repo", default=".")
    status_parser.add_argument("--base")
    status_parser.add_argument("--head")
    status_parser.add_argument("--working-tree", action="store_true")
    status_parser.add_argument("--changed-files")

    args = parser.parse_args()
    if args.command == "validate":
        return validate(args)
    print(json.dumps(status(args), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
