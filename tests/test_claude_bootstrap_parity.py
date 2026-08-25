"""Parity between the live Claude catalog and the generated Claude export.

The bootstrap moves distribution behind ``exports/claude`` without changing a
byte of what a user installs. This test is what makes that claim checkable: every
component the marketplace registers must exist under the export at the same
relative path with the same bytes.
"""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO_ROOT / ".claude-plugin/marketplace.json"
EXPORT_ROOT = REPO_ROOT / "exports/claude/plugins"

COMPONENT_KEYS = ("agents", "skills", "commands", "hooks")


def load_marketplace() -> dict:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def registered_files(plugin: dict) -> list[str]:
    """Return every registered component path, relative to the plugin root."""
    kernel = REPO_ROOT / "plugins" / plugin["name"]
    files: list[str] = []
    for key in COMPONENT_KEYS:
        for entry in plugin.get(key, []):
            reference = entry["source"] if isinstance(entry, dict) else entry
            relative = Path(reference.lstrip("./"))
            candidate = kernel / relative
            if candidate.is_dir():
                files.extend(
                    item.relative_to(kernel).as_posix()
                    for item in sorted(candidate.rglob("*"))
                    if item.is_file() and "__pycache__" not in item.parts
                )
            elif candidate.is_file():
                files.append(relative.as_posix())
    return files


class ClaudeBootstrapParityTests(unittest.TestCase):
    def test_bootstrap_export_matches_registered_components(self):
        for plugin in load_marketplace()["plugins"]:
            kernel = REPO_ROOT / "plugins" / plugin["name"]
            if (kernel / "plugin.toml").is_file():
                # A migrated plugin is compiled rather than copied: its package
                # is covered by that plugin's own port test, and its generated
                # text is LF-normalized rather than byte-identical.
                continue
            for component in registered_files(plugin):
                with self.subTest(plugin=plugin["name"], component=component):
                    source = kernel / component
                    exported = EXPORT_ROOT / plugin["name"] / component
                    self.assertTrue(exported.is_file(), f"missing export: {exported}")
                    self.assertEqual(exported.read_bytes(), source.read_bytes())

    def test_every_marketplace_source_points_at_the_export(self):
        for plugin in load_marketplace()["plugins"]:
            with self.subTest(plugin=plugin["name"]):
                self.assertEqual(
                    plugin["source"], f"./exports/claude/plugins/{plugin['name']}"
                )

    def test_every_exported_plugin_carries_a_native_manifest(self):
        for plugin in load_marketplace()["plugins"]:
            with self.subTest(plugin=plugin["name"]):
                manifest = EXPORT_ROOT / plugin["name"] / ".claude-plugin/plugin.json"
                self.assertTrue(manifest.is_file(), f"missing manifest: {manifest}")
                declared = json.loads(manifest.read_text(encoding="utf-8"))
                self.assertEqual(declared["name"], plugin["name"])
                self.assertEqual(declared["version"], plugin["version"])

    def test_the_catalog_still_lists_every_plugin_directory(self):
        registered = {plugin["name"] for plugin in load_marketplace()["plugins"]}
        on_disk = {
            path.name
            for path in (REPO_ROOT / "plugins").iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        self.assertEqual(registered, on_disk)

    def test_no_build_artifact_reached_the_export(self):
        for path in EXPORT_ROOT.rglob("*"):
            self.assertNotIn("__pycache__", path.parts)
            self.assertNotIn(path.suffix, {".pyc", ".pyo"})


if __name__ == "__main__":
    unittest.main()
