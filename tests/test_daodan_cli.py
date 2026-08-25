"""CLI behaviour tests for the Daodan compiler."""

import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan_build import build_repository, main  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


class CompilerCliTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        shutil.copytree(REPO_ROOT / "adapters", self.root / "adapters")
        shutil.copytree(VALID, self.root / "plugins/example")
        (self.root / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    def run_cli(self, *arguments) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = main([*arguments, "--root", str(self.root)])
        return code, out.getvalue()

    def test_publication_then_check_is_clean(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_check_reports_drift_after_a_kernel_edit(self):
        self.assertEqual(self.run_cli()[0], 0)
        role = self.root / "plugins/example/roles/inspector.md"
        role.write_text(role.read_text(encoding="utf-8") + "\nEdited.\n", encoding="utf-8")
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("generated-drift", output)

    def test_check_reports_drift_when_output_is_missing(self):
        code, output = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("generated-drift", output)

    def test_partial_publication_is_an_invocation_error(self):
        code, output = self.run_cli("--host", "claude")
        self.assertEqual(code, 2)
        self.assertIn("together", output)

    def test_partial_host_is_allowed_under_check(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--check", "--host", "claude")[0], 0)

    def test_validation_failure_writes_nothing(self):
        manifest = self.root / "plugins/example/plugin.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                '"repository.read"', '"telepathy.read"'
            ),
            encoding="utf-8",
        )
        code, output = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("unknown-capability", output)
        self.assertFalse((self.root / "exports").exists())

    def test_all_three_hosts_are_published_together(self):
        self.assertEqual(self.run_cli()[0], 0)
        for host in ("claude", "copilot", "codex"):
            self.assertTrue((self.root / "exports" / host / "plugins/example").is_dir())
        self.assertTrue((self.root / ".claude-plugin/marketplace.json").is_file())
        self.assertTrue((self.root / ".github/plugin/marketplace.json").is_file())
        self.assertTrue((self.root / ".agents/plugins/marketplace.json").is_file())

    def test_support_table_names_every_host(self):
        report = build_repository(self.root, ("claude", "copilot", "codex"), check=True)
        self.assertEqual({item.host for item in report.support}, {"claude", "copilot", "codex"})


if __name__ == "__main__":
    unittest.main()
