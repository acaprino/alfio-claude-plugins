"""What the publication workflow must and must not do.

The mirror workflow it replaces wrote one host's export. This one writes all
three or none, because a marketplace where one host is a commit ahead of the
others is the drift the whole compiler exists to prevent.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github/workflows"

PUBLISH = WORKFLOWS / "publish-marketplaces.yml"
CONSISTENCY = WORKFLOWS / "consistency.yml"

STAGED_PATHS = (
    "exports/claude",
    "exports/copilot",
    "exports/codex",
    ".claude-plugin/marketplace.json",
    ".github/plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
)

FORBIDDEN = ("vsce", "exports/vscode", "gen_extension_manifest.py", "mirror_export.py")


def workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class PublishWorkflowContractTests(unittest.TestCase):
    def test_the_publication_workflow_exists(self):
        self.assertTrue(PUBLISH.is_file(), f"missing: {PUBLISH}")

    def test_the_mirror_workflow_is_gone(self):
        self.assertFalse((WORKFLOWS / "mirror-export.yml").exists())

    def test_publication_runs_the_universal_check(self):
        text = workflow_text(PUBLISH)
        self.assertIn("scripts/daodan_build.py --check", text)
        self.assertIn("scripts/daodan_build.py", text)

    def test_publication_stages_every_host(self):
        text = workflow_text(PUBLISH)
        for path in STAGED_PATHS:
            with self.subTest(path=path):
                self.assertIn(path, text)

    def test_publication_guards_against_answering_itself(self):
        text = workflow_text(PUBLISH)
        self.assertIn("github-actions[bot]", text)
        self.assertIn("concurrency", text)

    def test_publication_commit_message_is_fixed(self):
        self.assertIn("Publish native Daodan marketplaces", workflow_text(PUBLISH))

    def test_consistency_runs_the_drift_gate(self):
        self.assertIn("scripts/daodan_build.py --check", workflow_text(CONSISTENCY))

    def test_consistency_pins_python_311_or_later(self):
        text = workflow_text(CONSISTENCY)
        self.assertNotIn("python-version: '3.10'", text)
        self.assertIn("python-version:", text)

    def test_no_workflow_mentions_the_extension_surface(self):
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = workflow_text(path)
            for token in FORBIDDEN:
                with self.subTest(workflow=path.name, token=token):
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
