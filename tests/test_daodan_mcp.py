"""MCP server declarations: a manifest where the host starts them, a note where it does not.

The motivating case is `peer-review`, whose `.mcp.json` and server lived at the kernel root
and shipped nowhere after the universal cutover: the compiler had no MCP concept, so the
package rendered cleanly and the workflow's transport calls could never connect.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import load_adapter  # noqa: E402
from scripts.daodan.catalogs import catalog_document  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.model import ModelError  # noqa: E402
from scripts.daodan.render import publish_plugin  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY, validate_plugins  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
FIXTURE = REPO_ROOT / "tests/fixtures/daodan/valid-mcp/plugins/example"
SERVER = "skills/tools/scripts/server.py"
DECLARATION = (
    '\n[[mcp.servers]]\nname = "example-tools"\ncommand = "uv"\n'
    'args = ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/server.py"]\n'
)


class McpRenderingTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)

    def publish(self, host: str) -> Path:
        live = self.temp / host
        publish_plugin(load_plugin(FIXTURE), load_adapter(ADAPTERS, host), live)
        return live

    def test_fixture_is_valid(self):
        self.assertEqual(validate_plugins([load_plugin(FIXTURE)], CAPABILITY_REGISTRY), [])

    def test_claude_renders_the_manifest_and_the_catalog_pointer(self):
        live = self.publish("claude")
        manifest = json.loads((live / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(
            manifest,
            {
                "mcpServers": {
                    "example-tools": {
                        "command": "uv",
                        "args": ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/" + SERVER],
                    }
                }
            },
        )
        self.assertTrue((live / SERVER).is_file())
        catalog = catalog_document("claude", [load_plugin(FIXTURE)], "1.0.0", {"example": live})
        self.assertEqual(catalog["plugins"][0]["mcpServers"], "./.mcp.json")
        # The manifest is the mechanism; nothing needs telling the user on Claude.
        for path in live.rglob("*.md"):
            self.assertNotIn("register that command", path.read_text(encoding="utf-8"))

    def test_other_hosts_ship_the_server_and_a_registration_note(self):
        for host, root_reference in (("codex", "<plugin-root>"), ("copilot", "${PLUGIN_ROOT}")):
            with self.subTest(host=host):
                live = self.publish(host)
                self.assertFalse((live / ".mcp.json").exists())
                self.assertTrue((live / SERVER).is_file())
                noted = [
                    path.read_text(encoding="utf-8")
                    for path in live.rglob("*.md")
                    if "register that command" in path.read_text(encoding="utf-8")
                ]
                self.assertTrue(noted, f"{host}: no workflow carries the registration note")
                for text in noted:
                    self.assertIn("`example-tools`", text)
                    self.assertIn(f"uv run --script {root_reference}/{SERVER}", text)
                    self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
                catalog = catalog_document(
                    host, [load_plugin(FIXTURE)], "1.0.0", {"example": live}
                )
                self.assertNotIn("mcpServers", catalog["plugins"][0])


class McpValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.root = self.temp / "example"
        shutil.copytree(FIXTURE, self.root)
        self.manifest = self.root / "plugin.toml"

    def rewrite(self, old: str, new: str) -> None:
        text = self.manifest.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.manifest.write_text(text.replace(old, new), encoding="utf-8")

    def codes(self) -> set[str]:
        return {issue.code for issue in validate_plugins([load_plugin(self.root)], CAPABILITY_REGISTRY)}

    def test_servers_require_the_capability(self):
        self.rewrite('"roles.dispatch", "mcp.servers"]', '"roles.dispatch"]')
        self.assertIn("mcp-capability-undeclared", self.codes())

    def test_capability_requires_a_server(self):
        self.rewrite(DECLARATION, "\n")
        self.assertIn("mcp-capability-without-servers", self.codes())

    def test_server_must_start_from_a_shipped_file(self):
        self.rewrite("${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/server.py", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py")
        self.assertIn("mcp-server-file-not-shipped", self.codes())

    def test_server_must_stay_inside_the_plugin(self):
        self.rewrite("${CLAUDE_PLUGIN_ROOT}/skills/tools/scripts/server.py", "${CLAUDE_PLUGIN_ROOT}/../server.py")
        self.assertIn("path-outside-plugin", self.codes())

    def test_unknown_server_keys_are_rejected_at_load(self):
        self.rewrite('command = "uv"\n', 'command = "uv"\nenv = { KEY = "value" }\n')
        with self.assertRaises(ModelError):
            load_plugin(self.root)


if __name__ == "__main__":
    unittest.main()
