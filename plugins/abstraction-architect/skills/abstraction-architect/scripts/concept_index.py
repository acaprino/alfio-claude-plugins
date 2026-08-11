#!/usr/bin/env python3
"""Concept index freshness and delta partitioning for abstraction-architect.

Stdlib only, deterministic work only. This script never discovers concepts.
It validates the index schema, resolves the three distinct notions of change
(index baseline, repository state, review delta), and partitions the changed
files into those an indexed concept already claims and those it does not.

Every semantic judgement, including whether two representations encode the
same knowledge, belongs to the agent.

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


def git(repo, *args):
    """Run git in repo. Returns (ok, stdout_rstripped).

    Only the trailing newline is stripped. A blanket strip() would eat a
    leading space from the first line of multi-line output such as
    `git status --porcelain`, where a leading space is a meaningful part
    of a status code (" M path"), and that would misalign every path
    parsed from that line.
    """
    result = subprocess.run(["git", *args], cwd=repo,
                            capture_output=True, text=True, encoding="utf-8")
    return result.returncode == 0, result.stdout.rstrip("\r\n")


def load_index(path):
    """Returns (index, error_message). One of the two is always None."""
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


def diff_files(repo, base, head, scope):
    ok, out = git(repo, "diff", "--name-only", base, head, "--", *pathspec(scope))
    return [line for line in out.splitlines() if line] if ok else []


def worktree_files(repo, scope):
    """Staged, unstaged and untracked paths within scope.

    --untracked-files=all asks git to list every untracked file
    individually rather than collapsing a wholly untracked directory into
    one directory entry. The script partitions by file path, so a
    collapsed directory entry would never match a representation's `file`
    and would silently hide every file inside it from the partition.
    """
    ok, out = git(repo, "status", "--porcelain", "--untracked-files=all",
                  "--", *pathspec(scope))
    if not ok:
        return []
    files = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:            # rename: take the destination
            path = path.split(" -> ", 1)[1]
        files.append(path.strip().strip('"'))
    return files


def own_artifact_dir(repo, index_path):
    """Repo-relative, forward-slash, trailing-slash directory that holds the
    index file, or None when it cannot be resolved or sits at repo root.

    That directory is this script's and the agent's own report directory:
    concept-index.json alongside findings.md and findings-diff.md (see
    agents/abstraction-architect.md). None of the three is a file under
    review. Excluding the whole directory, derived from the resolved
    --index path rather than a hardcoded string, rather than only the
    index file, keeps writing or updating any of them from making itself
    look like changed content, a concept in need of discovery that is
    actually the discovery record.
    """
    try:
        repo_abs = os.path.realpath(repo)
        index_dir_abs = os.path.dirname(os.path.realpath(index_path))
    except OSError:
        return None
    rel = os.path.relpath(index_dir_abs, repo_abs)
    if rel == os.curdir:
        return None            # index sits at repo root: nothing to exclude
    if rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return None
    rel = rel.replace(os.sep, "/")
    return rel if rel.endswith("/") else rel + "/"


def without_own_artifacts(files, own_dir):
    if own_dir is None:
        return files
    return [path for path in files if not path.startswith(own_dir)]


def partition(index, changed_files):
    """Split changed files into indexed concepts touched and unclaimed files."""
    changed = set(changed_files)
    claimed = set()
    dirty = []
    for concept in index.get("concepts", []):
        files = {rep.get("file") for rep in concept.get("representations", [])
                 if rep.get("file")}
        claimed |= files
        if files & changed:
            dirty.append(concept.get("concept"))
    unmapped = sorted(path for path in changed if path not in claimed)
    return sorted(name for name in dirty if name), unmapped


def resolve_review_delta(repo, args, scope, own_dir=None):
    if args.changed_files:
        # An explicit list is the caller's deliberate scope, so it is never
        # filtered against own_dir: only autodetected git state is.
        try:
            with open(args.changed_files, encoding="utf-8") as handle:
                files = [line.strip() for line in handle if line.strip()]
        except OSError as exc:
            return {"source": "changed-files", "files": [],
                    "error": f"cannot read {args.changed_files}: {exc}"}
        return {"source": "changed-files", "files": files}
    if args.base:
        head = args.head or "HEAD"
        files = without_own_artifacts(diff_files(repo, args.base, head, scope), own_dir)
        return {"source": f"{args.base}..{head}", "files": files}
    if args.working_tree:
        files = without_own_artifacts(worktree_files(repo, scope), own_dir)
        return {"source": "working-tree", "files": files}
    return {"source": "none", "files": []}


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

    own_dir = own_artifact_dir(repo, args.index)
    dirty_paths = without_own_artifacts(worktree_files(repo, scope), own_dir)
    repository_state = {
        "head_commit": head_commit,
        "head_tree": head_tree,
        "dirty": bool(dirty_paths),
    }

    review_delta = resolve_review_delta(repo, args, scope, own_dir)

    if not commit_exists(repo, baseline["commit"]):
        result = unusable(
            f"index baseline commit {baseline['commit'][:7]} is not reachable",
            baseline, review_delta)
        result["repository_state"] = repository_state
        return result

    baseline_drift = without_own_artifacts(
        diff_files(repo, baseline["commit"], "HEAD", scope), own_dir)
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
