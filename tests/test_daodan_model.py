"""Loader tests for the neutral Daodan plugin model."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError  # noqa: E402

VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


class NeutralModelTests(unittest.TestCase):
    def test_loads_plugin_and_workflow(self):
        plugin = load_plugin(VALID)
        self.assertEqual(plugin.name, "example")
        self.assertEqual(plugin.version, "1.2.3")
        self.assertEqual(plugin.workflows[0].phases[0].id, "inspect")
        self.assertEqual(plugin.workflows[0].phases[0].isolation, "required")
        self.assertEqual(plugin.workflows[0].phases[0].join, "all-delivered")
        self.assertEqual(plugin.workflows[0].contract.artifacts, ("report",))
        self.assertEqual(
            plugin.workflows[0].contract.schemas,
            (Path("contracts/reviewer-result.toml"),),
        )

    def test_capabilities_are_loaded_separately(self):
        plugin = load_plugin(VALID)
        self.assertEqual(
            plugin.capabilities.required,
            ("repository.read", "contexts.isolate", "roles.dispatch"),
        )
        self.assertEqual(plugin.capabilities.optional, ("execution.parallel",))

    def test_entrypoint_is_plugin_relative_and_normalized(self):
        plugin = load_plugin(VALID)
        self.assertEqual(plugin.workflows[0].entrypoint, Path("workflows/review.md"))

    def test_components_index_is_loaded(self):
        plugin = load_plugin(VALID)
        self.assertEqual(plugin.components.roles, ("inspector",))
        self.assertEqual(plugin.components.workflows, ("review",))
        self.assertEqual(plugin.components.skills, ())

    def test_unknown_top_level_key_is_rejected(self):
        with self.assertRaises(ModelError):
            load_plugin(self._mutated("prompt = \"do the thing\"\n"))

    def test_missing_required_table_is_rejected(self):
        with self.assertRaises(ModelError):
            load_plugin(self._mutated(drop="[capabilities]"))

    def _mutated(self, extra: str = "", drop: str | None = None) -> Path:
        import shutil
        import tempfile

        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporary, True)
        destination = temporary / "example"
        shutil.copytree(VALID, destination)
        manifest = destination / "plugin.toml"
        text = manifest.read_text(encoding="utf-8")
        if drop is not None:
            lines = text.splitlines(keepends=True)
            start = next(index for index, line in enumerate(lines) if line.strip() == drop)
            end = start + 1
            while end < len(lines) and not lines[end].startswith("["):
                end += 1
            text = "".join(lines[:start] + lines[end:])
        manifest.write_text(text + extra, encoding="utf-8")
        return destination


if __name__ == "__main__":
    unittest.main()
