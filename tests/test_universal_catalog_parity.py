"""The completed-migration gate.

Every plugin is a neutral kernel, every kernel is in every catalog at the same
version, and no host reports a required component it cannot express.
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter, resolve_support  # noqa: E402
from scripts.daodan_build import discover_plugins  # noqa: E402

EXPECTED_PLUGIN_COUNT = 40

CATALOG_PATH = {
    "claude": ".claude-plugin/marketplace.json",
    "copilot": ".github/plugin/marketplace.json",
    "codex": ".agents/plugins/marketplace.json",
}


def core_plugins() -> set[str]:
    return {path.parent.name for path in (REPO_ROOT / "plugins").glob("*/plugin.toml")}


def catalog(host: str) -> dict:
    return json.loads((REPO_ROOT / CATALOG_PATH[host]).read_text(encoding="utf-8"))


def catalog_names(host: str) -> set[str]:
    return {entry["name"] for entry in catalog(host)["plugins"]}


def parity_states(host: str) -> set[str]:
    adapter = load_adapter(REPO_ROOT / "adapters", host)
    return {resolve_support(plugin, adapter).state for plugin in discover_plugins(REPO_ROOT)}


class UniversalCatalogParityTests(unittest.TestCase):
    def test_every_core_plugin_is_in_every_catalog(self):
        core = core_plugins()
        self.assertEqual(len(core), EXPECTED_PLUGIN_COUNT)
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(catalog_names(host), core)
                self.assertNotIn("unsupported", parity_states(host))

    def test_every_plugin_directory_is_a_neutral_kernel(self):
        directories = {
            path.name
            for path in (REPO_ROOT / "plugins").iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        self.assertEqual(directories, core_plugins())

    def test_every_host_packages_every_plugin(self):
        for host in HOSTS:
            for name in sorted(core_plugins()):
                with self.subTest(host=host, plugin=name):
                    package = REPO_ROOT / "exports" / host / "plugins" / name
                    self.assertTrue(package.is_dir(), f"missing package: {package}")
                    self.assertTrue((package / ".daodan-provenance.json").is_file())

    def test_versions_are_identical_across_hosts(self):
        reference = {
            entry["name"]: entry["version"] for entry in catalog("claude")["plugins"]
        }
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(
                    {entry["name"]: entry["version"] for entry in catalog(host)["plugins"]},
                    reference,
                )

    def test_no_override_is_stale(self):
        from scripts.daodan.overrides import load_overrides, validate_override
        from scripts.daodan.load import load_plugin

        for host in HOSTS:
            root = REPO_ROOT / "adapters" / host / "overrides"
            if not root.is_dir():
                continue
            for manifest in sorted(root.rglob("override.toml")):
                plugin_name = manifest.relative_to(root).parts[0]
                plugin = load_plugin(REPO_ROOT / "plugins" / plugin_name)
                declared = frozenset(plugin.capabilities.required) | frozenset(
                    plugin.capabilities.optional
                )
                for spec in load_overrides(manifest.parent):
                    with self.subTest(host=host, override=str(manifest)):
                        self.assertEqual(
                            validate_override(spec, declared, repository_root=REPO_ROOT), []
                        )


if __name__ == "__main__":
    unittest.main()
