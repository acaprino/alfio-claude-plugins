"""Tests for the fingerprinted semantic override gate."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.overrides import (  # noqa: E402
    load_overrides,
    source_digest,
    validate_override,
)

FIXTURE = REPO_ROOT / "tests/fixtures/daodan/overrides/copilot/example/review"
SOURCE = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example/workflows/review.md"


class OverrideTests(unittest.TestCase):
    def load_fixture_override(self, **replacements):
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        destination = temporary / "review"
        shutil.copytree(FIXTURE, destination)
        manifest = destination / "override.toml"
        lines = manifest.read_text(encoding="utf-8").splitlines()
        for key, value in replacements.items():
            rendered = (
                f"{key} = [" + ", ".join(f'"{item}"' for item in value) + "]"
                if isinstance(value, (tuple, list))
                else f'{key} = "{value}"'
            )
            lines = [rendered if line.startswith(f"{key} = ") else line for line in lines]
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return load_overrides(destination)[0]

    def test_changed_source_marks_override_stale(self):
        spec = self.load_fixture_override(reviewed_against="sha256:deadbeef")
        issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
        self.assertEqual([issue.code for issue in issues], ["stale-override"])

    def test_override_cannot_add_undeclared_capability(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("shell.execute",),
        )
        issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
        self.assertEqual([issue.code for issue in issues], ["override-capability-escalation"])

    def test_matching_fingerprint_and_declared_capability_passes(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("repository.read",),
        )
        self.assertEqual(
            validate_override(spec, declared_capabilities=frozenset({"repository.read"})), []
        )

    def test_replacement_outside_the_override_directory_is_rejected(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("repository.read",),
            replacement="../orchestrator.agent.md",
        )
        issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
        self.assertEqual([issue.code for issue in issues], ["override-escapes-directory"])

    def test_contract_absent_from_the_neutral_workflow_is_rejected(self):
        spec = self.load_fixture_override(
            reviewed_against=source_digest([SOURCE]),
            capabilities_affected=("repository.read",),
        )
        issues = validate_override(
            spec,
            declared_capabilities=frozenset({"repository.read"}),
            declared_contracts=frozenset({"some-other-outcome"}),
        )
        self.assertEqual([issue.code for issue in issues], ["override-drops-contract"])

    def test_source_digest_is_order_independent_and_content_sensitive(self):
        other = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example/roles/inspector.md"
        self.assertEqual(source_digest([SOURCE, other]), source_digest([other, SOURCE]))
        self.assertNotEqual(source_digest([SOURCE]), source_digest([other]))


if __name__ == "__main__":
    unittest.main()
