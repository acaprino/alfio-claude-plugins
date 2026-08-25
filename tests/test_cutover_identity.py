"""The cutover gate: one marketplace identity, three hosts, no extension surface."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.sync_codex_instructions import (  # noqa: E402
    WORKFLOW_SKILLS,
    adapt_claude_instructions_for_codex,
)

CATALOGS = {
    "claude": REPO_ROOT / ".claude-plugin/marketplace.json",
    "copilot": REPO_ROOT / ".github/plugin/marketplace.json",
    "codex": REPO_ROOT / ".agents/plugins/marketplace.json",
}

IDENTITY = "daodan"

EXTENSION_TOKENS = ("vsce", "vscode-v", "release-vscode")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout.splitlines()


class CutoverIdentityTests(unittest.TestCase):
    def test_all_three_native_manifests_exist(self):
        for host, path in CATALOGS.items():
            with self.subTest(host=host):
                self.assertTrue(path.is_file(), f"missing: {path}")

    def test_every_catalog_declares_the_same_identity(self):
        for host, path in CATALOGS.items():
            with self.subTest(host=host):
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["name"], IDENTITY)

    def test_versions_and_plugin_sets_match_across_hosts(self):
        reference = None
        version = None
        for host, path in CATALOGS.items():
            catalog = json.loads(path.read_text(encoding="utf-8"))
            entries = {entry["name"]: entry["version"] for entry in catalog["plugins"]}
            with self.subTest(host=host):
                if reference is None:
                    reference, version = entries, catalog["metadata"]["version"]
                else:
                    self.assertEqual(entries, reference)
                    self.assertEqual(catalog["metadata"]["version"], version)

    def test_the_extension_export_is_gone(self):
        self.assertFalse((REPO_ROOT / "exports/vscode").exists())

    def test_no_tracked_file_carries_the_extension_release_surface(self):
        for path in tracked_files():
            if path.startswith("docs/") or path.startswith("evals/"):
                # History and migration notes are allowed to name what was removed.
                continue
            if path.startswith("tests/"):
                # The contract tests name what must not appear elsewhere; that is
                # their subject matter, not a leftover of it.
                continue
            if path in {"README.md", "CLAUDE.md"}:
                continue
            if not (REPO_ROOT / path).is_file():
                continue
            if not path.endswith((".yml", ".yaml", ".py", ".json", ".js")):
                continue
            content = (REPO_ROOT / path).read_text(encoding="utf-8", errors="ignore")
            for token in EXTENSION_TOKENS:
                with self.subTest(path=path, token=token):
                    self.assertNotIn(token, content)

    def test_no_extension_workflow_or_script_remains(self):
        for path in (
            ".github/workflows/release-vscode.yml",
            ".github/workflows/mirror-export.yml",
            "scripts/extension_release_notes.py",
            "scripts/mirror_export.py",
        ):
            with self.subTest(path=path):
                self.assertFalse((REPO_ROOT / path).exists())

    def test_codex_root_instructions_are_the_native_adaptation(self):
        canonical = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        codex = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(codex, adapt_claude_instructions_for_codex(canonical))

    def test_codex_instructions_keep_all_three_distribution_commands(self):
        codex = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for host in ("claude", "copilot", "codex"):
            with self.subTest(host=host):
                self.assertEqual(
                    codex.count(f"{host} plugin marketplace add acaprino/daodan"),
                    1,
                )

    def test_codex_workflow_skills_are_native_adaptations(self):
        for name in WORKFLOW_SKILLS:
            with self.subTest(skill=name):
                canonical = (
                    REPO_ROOT / ".claude" / "skills" / name / "SKILL.md"
                ).read_text(encoding="utf-8")
                codex = (
                    REPO_ROOT / ".agents" / "skills" / name / "SKILL.md"
                ).read_text(encoding="utf-8")
                self.assertEqual(codex, adapt_claude_instructions_for_codex(canonical))

    def test_removed_codex_workflow_helpers_stay_removed(self):
        scripts = REPO_ROOT / ".agents/skills/downstream-exports/scripts"
        self.assertFalse(scripts.exists())

    def test_the_migration_note_exists(self):
        note = REPO_ROOT / "docs/migration-from-claude-code-daodan.md"
        self.assertTrue(note.is_file())
        text = note.read_text(encoding="utf-8")
        self.assertIn("acaprino/daodan", text)
        self.assertIn("Rollback", text)


if __name__ == "__main__":
    unittest.main()
