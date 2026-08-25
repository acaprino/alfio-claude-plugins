"""Reproducibility and rollback tests for the package renderer."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.overrides import source_digest  # noqa: E402
from scripts.daodan.render import (  # noqa: E402
    RenderError,
    publish_plugin,
    render_plugin,
    replace_tree,
    tree_digest,
)

ADAPTERS = REPO_ROOT / "adapters"
VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)

    def compile_fixture(self, host: str) -> Path:
        live = self.temp / f"live-{host}-{len(list(self.temp.iterdir()))}"
        publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, host), live)
        return live

    def compile_invalid_fixture(self, live: Path) -> None:
        adapter = load_adapter(ADAPTERS, "codex")
        bindings = dict(adapter.bindings)
        bindings["contexts.isolate"] = replace(bindings["contexts.isolate"], state="unsupported")
        publish_plugin(load_plugin(VALID), replace(adapter, bindings=bindings), live)

    def test_equal_inputs_produce_equal_bytes(self):
        first = self.compile_fixture("claude")
        second = self.compile_fixture("claude")
        self.assertEqual(tree_digest(first), tree_digest(second))

    def test_hosts_produce_different_trees(self):
        self.assertNotEqual(
            tree_digest(self.compile_fixture("claude")),
            tree_digest(self.compile_fixture("copilot")),
        )

    def test_failed_validation_keeps_live_tree(self):
        live = self.temp / "live"
        live.mkdir()
        (live / "sentinel").write_text("old", encoding="utf-8")
        with self.assertRaises(RenderError):
            self.compile_invalid_fixture(live)
        self.assertEqual((live / "sentinel").read_text(encoding="utf-8"), "old")

    def test_nothing_is_written_outside_the_destination(self):
        live = self.temp / "live"
        self.compile_fixture("claude")
        publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, "claude"), live)
        self.assertFalse((self.temp / ".previous").exists())

    def test_provenance_has_exactly_the_declared_keys(self):
        live = self.compile_fixture("claude")
        provenance = json.loads(
            (live / ".daodan-provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sorted(provenance),
            [
                "adapterVersion",
                "coreDigest",
                "harnessStrategies",
                "host",
                "overrides",
                "plugin",
                "version",
            ],
        )
        self.assertEqual(provenance["host"], "claude")
        self.assertEqual(provenance["plugin"], "example")
        self.assertEqual(provenance["version"], "1.2.3")
        self.assertEqual(provenance["harnessStrategies"], {"review": "native-team"})
        self.assertTrue(provenance["coreDigest"].startswith("sha256:"))
        self.assertEqual(len(provenance["coreDigest"].split(":")[1]), 64)

    def test_core_digest_is_independent_of_checkout_location(self):
        """The digest is a property of the kernel, not of where it sits.

        It used to hash absolute paths and raw bytes, so the same source hashed
        differently on a Windows checkout and a Linux runner, and CI reported
        drift against a tree that was identical.
        """
        first = render_plugin(
            load_plugin(VALID), load_adapter(ADAPTERS, "claude"), self.temp / "staging"
        ).core_digest

        elsewhere = self.temp / "relocated" / "example"
        shutil.copytree(VALID, elsewhere)
        second = render_plugin(
            load_plugin(elsewhere), load_adapter(ADAPTERS, "claude"), self.temp / "staging2"
        ).core_digest
        self.assertEqual(first, second)

    def test_core_digest_ignores_line_endings(self):
        crlf = self.temp / "crlf" / "example"
        shutil.copytree(VALID, crlf)
        for path in crlf.rglob("*"):
            if path.is_file():
                path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(
            render_plugin(
                load_plugin(VALID), load_adapter(ADAPTERS, "claude"), self.temp / "s1"
            ).core_digest,
            render_plugin(
                load_plugin(crlf), load_adapter(ADAPTERS, "claude"), self.temp / "s2"
            ).core_digest,
        )

    def test_generated_text_is_lf_normalized(self):
        live = self.compile_fixture("claude")
        for path in live.rglob("*.md"):
            self.assertNotIn(b"\r\n", path.read_bytes())

    def test_replace_tree_restores_the_previous_tree_on_failure(self):
        live = self.temp / "swap"
        live.mkdir()
        (live / "sentinel").write_text("old", encoding="utf-8")
        staging = self.temp / "staging-missing"
        with self.assertRaises(RenderError):
            replace_tree(staging, live)
        self.assertEqual((live / "sentinel").read_text(encoding="utf-8"), "old")

    @unittest.skipUnless(os.name == "nt", "Windows ACL regression")
    def test_published_tree_inherits_the_store_acl(self):
        store = Path(tempfile.gettempdir()) / f"daodan-render-{uuid.uuid4().hex}"
        store.mkdir()
        self.addCleanup(shutil.rmtree, store, True)
        live = store / "example"

        publish_plugin(load_plugin(VALID), load_adapter(ADAPTERS, "codex"), live)

        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "& { param($target) (Get-Item -LiteralPath $target).GetAccessControl().AreAccessRulesProtected }",
                str(live),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            (completed.returncode, completed.stdout.strip()),
            (0, "False"),
            completed.stderr.strip(),
        )


if __name__ == "__main__":
    unittest.main()
