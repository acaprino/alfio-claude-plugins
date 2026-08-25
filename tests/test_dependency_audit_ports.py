"""Cross-host package parity for the first real compiled plugin.

`dependency-audit` is the simple canary: one skill, one workflow, one context.
It proves the compiler produces three installable packages with the same
identity and the same observable contract before anything harder is attempted.
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.load import load_plugin  # noqa: E402

PLUGIN = "dependency-audit"
KERNEL = REPO_ROOT / "plugins" / PLUGIN

MANIFEST = {
    "claude": ".claude-plugin/plugin.json",
    "copilot": "plugin.json",
    "codex": ".codex-plugin/plugin.json",
}

WORKFLOW_ENTRYPOINT = {
    "claude": "commands/deps-audit.md",
    "copilot": "prompts/deps-audit.prompt.md",
    "codex": "skills/deps-audit-workflow/SKILL.md",
}

SKILL_RESOURCES = (
    "skills/dependency-audit/SKILL.md",
    "skills/dependency-audit/references/ecosystems.md",
    "skills/dependency-audit/references/license-analysis.md",
    "skills/dependency-audit/references/supply-chain.md",
)

CONTRACT_OUTCOMES = (
    "dependencies-discovered",
    "direct-and-transitive-classified",
    "licenses-analyzed",
    "supply-chain-findings-evidenced",
)


def normalized(path: Path) -> str:
    """Compare content, not line endings: generated text is always LF."""
    return path.read_text(encoding="utf-8").replace(chr(13) + chr(10), chr(10))


def package(host: str) -> Path:
    return REPO_ROOT / "exports" / host / "plugins" / PLUGIN


class DependencyAuditPortTests(unittest.TestCase):
    def test_every_host_reports_the_same_identity(self):
        kernel = load_plugin(KERNEL)
        for host, manifest in MANIFEST.items():
            with self.subTest(host=host):
                declared = json.loads(
                    (package(host) / manifest).read_text(encoding="utf-8")
                )
                self.assertEqual(declared["name"], kernel.name)
                self.assertEqual(declared["version"], kernel.version)

    def test_every_host_carries_the_skill_resources_byte_for_byte(self):
        for host in MANIFEST:
            for resource in SKILL_RESOURCES:
                with self.subTest(host=host, resource=resource):
                    exported = package(host) / resource
                    self.assertTrue(exported.is_file(), f"missing: {exported}")
                    self.assertEqual(
                        normalized(exported), normalized(KERNEL / resource)
                    )

    def test_every_host_exposes_one_invocable_audit_workflow(self):
        for host, entrypoint in WORKFLOW_ENTRYPOINT.items():
            with self.subTest(host=host):
                target = package(host) / entrypoint
                self.assertTrue(target.is_file(), f"missing: {target}")
                self.assertEqual(
                    normalized(target), normalized(KERNEL / "workflows/deps-audit.md")
                )

    def test_the_kernel_declares_the_audit_contract(self):
        workflow = load_plugin(KERNEL).workflows[0]
        self.assertEqual(workflow.name, "deps-audit")
        for outcome in CONTRACT_OUTCOMES:
            self.assertIn(outcome, workflow.contract.outcomes)
        self.assertEqual(workflow.contract.artifacts, ("dependency-audit-report",))

    def test_the_kernel_needs_no_semantic_override(self):
        for host in MANIFEST:
            with self.subTest(host=host):
                provenance = json.loads(
                    (package(host) / ".daodan-provenance.json").read_text(encoding="utf-8")
                )
                self.assertEqual(provenance["overrides"], [])


if __name__ == "__main__":
    unittest.main()
