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


def write_index(repo, commit, tree, concepts=None, scope=".", schema_version=1):
    index = {
        "schema_version": schema_version,
        "generated_from_commit": commit,
        "generated_from_tree": tree,
        "generated_at": "2026-08-10T12:00:00Z",
        "scope": scope,
        "concepts": concepts if concepts is not None else [],
    }
    path = Path(repo) / ".abstraction-architect" / "concept-index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index), encoding="utf-8")
    return str(path)


def run_status(repo, index_path, *extra):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "status", "--index", index_path,
         "--repo", str(repo), *extra],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


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


if __name__ == "__main__":
    unittest.main()
