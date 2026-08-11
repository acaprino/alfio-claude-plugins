"""Tests for the abstraction-architect concept index script.

Stdlib only. Each test builds a real throwaway git repository, because the
script's whole job is to answer questions about git state and a mocked git
would test the mock.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (REPO_ROOT / "plugins" / "abstraction-architect" / "skills"
          / "abstraction-architect" / "scripts" / "concept_index.py")


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


def make_repo(tmp):
    git(tmp, "init", "-q")
    git(tmp, "config", "user.email", "t@example.com")
    git(tmp, "config", "user.name", "T")
    return tmp


def write(repo, rel, text):
    path = Path(repo) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit_all(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                          capture_output=True, text=True).stdout.strip()


def tree_of(repo, rev="HEAD"):
    return subprocess.run(["git", "rev-parse", f"{rev}^{{tree}}"], cwd=repo,
                          capture_output=True, text=True).stdout.strip()


def write_index(repo, commit, tree, concepts=None, scope=".", schema_version=1,
                path=None):
    index = {
        "schema_version": schema_version,
        "generated_from_commit": commit,
        "generated_from_tree": tree,
        "generated_at": "2026-08-10T12:00:00Z",
        "scope": scope,
        "concepts": concepts if concepts is not None else [],
    }
    if path is None:
        path = Path(repo) / ".abstraction-architect" / "concept-index.json"
    else:
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index), encoding="utf-8")
    return str(path)


# The eight keys status must return on every code path, including unusable.
STATUS_KEYS = ("freshness_state", "reason", "index_baseline", "repository_state",
              "review_delta", "changed_files", "dirty_indexed_concepts",
              "unmapped_changed_files")


def run_status(repo, index_path, *extra):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "status", "--index", index_path,
         "--repo", str(repo), *extra],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    missing = [key for key in STATUS_KEYS if key not in out]
    assert not missing, f"status output is missing keys: {missing}"
    return out


REFUND_CONCEPT = {
    "concept": "Refund eligibility",
    "kind": "policy",
    "representations": [
        {"symbol": "RefundPolicy.can_refund",
         "file": "domain/refund_policy.py", "role": "candidate_owner"},
        {"symbol": "REFUND_WINDOW_DAYS",
         "file": "config/refunds.py", "role": "parameter"},
    ],
    "writers": ["RefundPolicy"],
    "consumers": ["checkout"],
    "canonical_owner": {"status": "ambiguous"},
    "evidence": ["same 30-day policy in two places"],
}


class ConceptIndexStatus(unittest.TestCase):

    def test_missing_index_is_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "a.py", "x = 1\n")
            commit_all(tmp, "init")
            out = run_status(tmp, str(Path(tmp) / "nope.json"))
            self.assertEqual(out["freshness_state"], "unusable")

    def test_incompatible_schema_version_is_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "a.py", "x = 1\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), schema_version=99)
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "unusable")
            self.assertIn("schema_version", out["reason"])

    def test_matching_tree_and_clean_worktree_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "fresh")
            self.assertEqual(out["changed_files"], [])

    def test_matching_tree_with_uncommitted_change_is_not_fresh(self):
        """The false-freshness hazard: HEAD tree matches, but the
        uncommitted work is exactly what is under review."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "domain/refund_policy.py", "def can_refund(): return 1\n")
            out = run_status(tmp, idx)
            self.assertNotEqual(out["freshness_state"], "fresh")
            self.assertEqual(out["freshness_state"], "delta-stale")
            self.assertTrue(out["repository_state"]["dirty"])
            self.assertIn("domain/refund_policy.py", out["changed_files"])

    def test_advanced_head_with_reachable_baseline_is_delta_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            base = commit_all(tmp, "init")
            base_tree = tree_of(tmp)
            idx = write_index(tmp, base, base_tree, [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            commit_all(tmp, "add config")
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "delta-stale")
            self.assertIn("config/refunds.py", out["changed_files"])

    def test_unreachable_baseline_is_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "a.py", "x = 1\n")
            commit_all(tmp, "init")
            idx = write_index(tmp, "0" * 40, "1" * 40, [REFUND_CONCEPT])
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "unusable")
            self.assertIn("not reachable", out["reason"])

    def test_partition_splits_indexed_from_unmapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            base = commit_all(tmp, "init")
            idx = write_index(tmp, base, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            write(tmp, "support/new_thing.py", "x = 1\n")
            commit_all(tmp, "two files")
            out = run_status(tmp, idx)
            self.assertEqual(out["dirty_indexed_concepts"], ["Refund eligibility"])
            self.assertEqual(out["unmapped_changed_files"], ["support/new_thing.py"])

    def test_changed_files_input_is_unioned_with_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            write(tmp, "unrelated/other.py", "y = 2\n")
            base = commit_all(tmp, "init")
            idx = write_index(tmp, base, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            commit_all(tmp, "drift")
            listing = Path(tmp) / "changed.txt"
            listing.write_text("unrelated/other.py\n", encoding="utf-8")
            out = run_status(tmp, idx, "--changed-files", str(listing))
            self.assertIn("config/refunds.py", out["changed_files"])
            self.assertIn("unrelated/other.py", out["changed_files"])
            self.assertEqual(out["review_delta"]["source"], "changed-files")

    # --- --base / --head / --working-tree were previously untested, and a
    # review probe found a Critical defect through --base. One test per
    # delta source.

    def test_base_and_head_delta_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            base = commit_all(tmp, "init")
            idx = write_index(tmp, base, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            head = commit_all(tmp, "second")
            out = run_status(tmp, idx, "--base", base, "--head", head)
            self.assertEqual(out["review_delta"]["source"], f"{base}..{head}")
            self.assertIn("config/refunds.py", out["review_delta"]["files"])
            self.assertIn("Refund eligibility", out["dirty_indexed_concepts"])

    def test_base_without_head_defaults_to_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            base = commit_all(tmp, "init")
            idx = write_index(tmp, base, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "config/refunds.py", "REFUND_WINDOW_DAYS = 30\n")
            commit_all(tmp, "second")
            out = run_status(tmp, idx, "--base", base)
            self.assertEqual(out["review_delta"]["source"], f"{base}..HEAD")
            self.assertIn("config/refunds.py", out["review_delta"]["files"])

    def test_working_tree_delta_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            write(tmp, "domain/refund_policy.py", "def can_refund(): return 1\n")
            out = run_status(tmp, idx, "--working-tree")
            self.assertEqual(out["review_delta"]["source"], "working-tree")
            self.assertIn("domain/refund_policy.py", out["review_delta"]["files"])

    # --- Regression tests, one per review-round-1 bug, named after the bug
    # so a future rewrite that regresses one of these fails a named test
    # instead of a coincidental assertion inside an unrelated test.

    def test_non_ascii_path_is_not_mangled_and_concept_flagged_dirty(self):
        """Critical #1: a git-quoted path (any filename with a non-ASCII
        byte, under git's default core.quotePath) must come back as the
        real path, not an escaped, quoted string that names no file on
        disk, and its owning concept must be flagged dirty rather than
        reported clean."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/café_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            concept = {
                "concept": "Refund eligibility",
                "kind": "policy",
                "representations": [
                    {"symbol": "can_refund", "file": "domain/café_policy.py",
                     "role": "candidate_owner"},
                ],
                "writers": [], "consumers": [],
                "canonical_owner": {"status": "ambiguous"},
                "evidence": [],
            }
            idx = write_index(tmp, head, tree_of(tmp), [concept])
            write(tmp, "domain/café_policy.py", "def can_refund(): return 1\n")
            out = run_status(tmp, idx)
            self.assertIn("domain/café_policy.py", out["changed_files"])
            self.assertEqual(out["dirty_indexed_concepts"], ["Refund eligibility"])
            self.assertEqual(out["unmapped_changed_files"], [])

    def test_uncommitted_rename_flags_owning_concept_dirty(self):
        """Critical #2, worktree path: an uncommitted rename must not let
        the owning concept look untouched. The file its representation
        points at no longer exists at that path, which is exactly the
        change that invalidates a representation."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            git(tmp, "mv", "domain/refund_policy.py", "domain/refunds.py")
            out = run_status(tmp, idx)
            self.assertIn("Refund eligibility", out["dirty_indexed_concepts"])

    def test_committed_rename_flags_owning_concept_dirty(self):
        """Critical #2, drift path: git's default rename detection folds a
        committed rename into a single diff record naming only the
        destination. The owning concept must still be flagged dirty."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            base = commit_all(tmp, "init")
            idx = write_index(tmp, base, tree_of(tmp), [REFUND_CONCEPT])
            git(tmp, "mv", "domain/refund_policy.py", "domain/refunds.py")
            commit_all(tmp, "rename")
            out = run_status(tmp, idx)
            self.assertIn("Refund eligibility", out["dirty_indexed_concepts"])

    def test_unusable_delta_source_reports_unusable_not_fresh(self):
        """Critical #3: a --base ref that does not resolve must report
        unusable, never a clean fresh result with a silently empty
        delta."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            out = run_status(tmp, idx, "--base", "no-such-ref")
            self.assertEqual(out["freshness_state"], "unusable")

    def test_unreadable_changed_files_listing_reports_unusable(self):
        """Critical #3: a --changed-files listing that fails to read must
        report unusable, not a clean fresh result with the read error
        buried in review_delta and ignored everywhere else."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT])
            missing_listing = str(Path(tmp) / "nope-changed.txt")
            out = run_status(tmp, idx, "--changed-files", missing_listing)
            self.assertEqual(out["freshness_state"], "unusable")

    def test_self_exclusion_does_not_swallow_sibling_source_files(self):
        """Review finding D1: excluding the index's own artifacts must not
        exclude real source files that merely share its directory. An
        index at docs/concept-index.json must not make docs/refunds.md,
        or the concept it represents, look untouched."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            write(tmp, "docs/refunds.md", "the refund window is 30 days\n")
            base = commit_all(tmp, "init")
            concept = {
                "concept": "Refund eligibility",
                "kind": "policy",
                "representations": [
                    {"symbol": "can_refund", "file": "domain/refund_policy.py",
                     "role": "candidate_owner"},
                    {"symbol": "refund window doc", "file": "docs/refunds.md",
                     "role": "implementation"},
                ],
                "writers": [], "consumers": [],
                "canonical_owner": {"status": "ambiguous"},
                "evidence": [],
            }
            idx = write_index(tmp, base, tree_of(tmp), [concept],
                              path=Path(tmp) / "docs" / "concept-index.json")
            write(tmp, "docs/refunds.md", "the refund window is 45 days now\n")
            out = run_status(tmp, idx)
            self.assertIn("docs/refunds.md", out["changed_files"])
            self.assertIn("Refund eligibility", out["dirty_indexed_concepts"])

    def test_self_exclusion_works_when_index_sits_at_repo_root(self):
        """Review finding D2: an index placed directly at the repository
        root must still be excluded from its own answer, not silently
        disable the exclusion because 'the containing directory' is the
        whole repository."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/refund_policy.py", "def can_refund(): pass\n")
            head = commit_all(tmp, "init")
            idx = write_index(tmp, head, tree_of(tmp), [REFUND_CONCEPT],
                              path=Path(tmp) / "concept-index.json")
            out = run_status(tmp, idx)
            self.assertEqual(out["freshness_state"], "fresh")
            self.assertEqual(out["changed_files"], [])

    def test_malformed_concepts_list_reports_unusable_not_crash(self):
        """Important #1: a concepts value that is not a list of objects
        must degrade to unusable, never crash the process."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "a.py", "x = 1\n")
            head = commit_all(tmp, "init")
            idx = Path(tmp) / ".abstraction-architect" / "concept-index.json"
            idx.parent.mkdir(parents=True, exist_ok=True)
            idx.write_text(json.dumps({
                "schema_version": 1,
                "generated_from_commit": head,
                "generated_from_tree": tree_of(tmp),
                "generated_at": "2026-08-10T12:00:00Z",
                "scope": ".",
                "concepts": ["Refund eligibility"],
            }), encoding="utf-8")
            out = run_status(tmp, str(idx))
            self.assertEqual(out["freshness_state"], "unusable")

    def test_unnamed_concept_still_accounts_for_its_changed_files(self):
        """Important #4: a concept with no 'concept' name must not vanish
        from the partition. Its changed files must land in
        dirty_indexed_concepts under a positional label, never disappear
        from both halves."""
        with tempfile.TemporaryDirectory() as tmp:
            make_repo(tmp)
            write(tmp, "domain/other.py", "x = 1\n")
            base = commit_all(tmp, "init")
            concept = {
                "concept": "",
                "kind": "policy",
                "representations": [
                    {"symbol": "x", "file": "domain/other.py",
                     "role": "candidate_owner"},
                ],
                "writers": [], "consumers": [],
                "canonical_owner": {"status": "ambiguous"},
                "evidence": [],
            }
            idx = write_index(tmp, base, tree_of(tmp), [concept])
            write(tmp, "domain/other.py", "x = 2\n")
            out = run_status(tmp, idx)
            self.assertIn("domain/other.py", out["changed_files"])
            self.assertEqual(out["dirty_indexed_concepts"], ["concepts[0]"])
            self.assertNotIn("domain/other.py", out["unmapped_changed_files"])


class ConceptIndexValidate(unittest.TestCase):

    def test_validate_rejects_missing_required_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--index", str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("generated_from_commit", result.stdout + result.stderr)

    def test_validate_accepts_a_well_formed_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "generated_from_commit": "a" * 40,
                "generated_from_tree": "b" * 40,
                "generated_at": "2026-08-10T12:00:00Z",
                "scope": ".",
                "concepts": [REFUND_CONCEPT],
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--index", str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)

    def test_validate_rejects_malformed_concepts_list(self):
        """Important #1: validate must reject a malformed concepts shape
        with a FAIL line and exit 1, never traceback."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "generated_from_commit": "a" * 40,
                "generated_from_tree": "b" * 40,
                "generated_at": "2026-08-10T12:00:00Z",
                "scope": ".",
                "concepts": ["Refund eligibility"],
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--index", str(path)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
