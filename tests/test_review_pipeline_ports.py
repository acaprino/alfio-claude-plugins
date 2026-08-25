"""Cross-host contract parity for the review pipeline.

`team-review` is the complex canary: fan-out over selected dimensions, isolated
reviewer contexts, a delivery barrier, cross-examination in fresh contexts and a
single writer for the final report. The topology each host picks may differ. The
observable contract may not.
"""

import json
import sys
import tomllib
import unittest
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import HOSTS, load_adapter  # noqa: E402
from scripts.daodan.load import load_plugin  # noqa: E402

CLUSTER = (
    "repo-hygiene",
    "react-development",
    "platform-engineering",
    "typescript-development",
    "testing",
    "codebase-xray",
    "abstraction-architect",
    "senior-review",
)

PHASE_ORDER = (
    "scope",
    "context-building",
    "dimension-detection",
    "independent-review",
    "delivery-accounting",
    "initial-consolidation",
    "cross-examination",
    "consolidation",
    "report-delivery",
)

RECORD_CONTRACTS = (
    "review-brief",
    "reviewer-binding",
    "reviewer-selection",
    "evidenced-finding",
    "reviewer-result",
    "delivery-ledger",
    "final-report",
)


def load_team_review():
    plugin = load_plugin(REPO_ROOT / "plugins/senior-review")
    return next(workflow for workflow in plugin.workflows if workflow.name == "team-review")


def phase(workflow, identity):
    return next(item for item in workflow.phases if item.id == identity)


@dataclass(frozen=True)
class CompiledPackage:
    host: str
    root: Path

    @property
    def _workflow(self) -> dict:
        with (self.root / "contracts/team-review.workflow.toml").open("rb") as handle:
            return tomllib.load(handle)

    @property
    def _strategy(self):
        provenance = json.loads(
            (self.root / ".daodan-provenance.json").read_text(encoding="utf-8")
        )
        name = provenance["harnessStrategies"]["team-review"]
        adapter = load_adapter(REPO_ROOT / "adapters", self.host)
        return next(item for item in adapter.strategies if item.name == name)

    def _phase(self, identity):
        return next(item for item in self._workflow["phases"] if item["id"] == identity)

    @property
    def has_isolated_workers(self) -> bool:
        return (
            self._strategy.isolated
            and self._phase("independent-review")["isolation"] == "required"
        )

    @property
    def has_delivery_barrier(self) -> bool:
        return (
            self._phase("independent-review")["join"] == "all-delivered"
            and (self.root / "contracts/delivery-ledger.toml").is_file()
        )

    @property
    def has_cross_examination(self) -> bool:
        return self._phase("cross-examination")["needs"] == ["initial-consolidation"]

    @property
    def has_consolidation(self) -> bool:
        return self._phase("consolidation")["needs"] == ["cross-examination"]

    def artifact_root(self, name: str) -> str:
        policy = REPO_ROOT / "exports" / self.host / "plugins/codebase-xray/policies/write-confinement.toml"
        with policy.open("rb") as handle:
            return tomllib.load(handle)["roots"][name]


def compiled_review_package(host: str) -> CompiledPackage:
    return CompiledPackage(host, REPO_ROOT / "exports" / host / "plugins/senior-review")


class ReviewPipelinePortTests(unittest.TestCase):
    def test_the_whole_cluster_is_a_neutral_kernel(self):
        for name in CLUSTER:
            with self.subTest(plugin=name):
                self.assertTrue((REPO_ROOT / "plugins" / name / "plugin.toml").is_file())

    def test_team_review_kernel_requires_isolated_fanout_and_barrier(self):
        workflow = load_team_review()
        review = phase(workflow, "independent-review")
        self.assertEqual(review.isolation, "required")
        self.assertEqual(review.join, "all-delivered")
        self.assertEqual(review.concurrency, "preferred")
        self.assertEqual(review.fanout_from, "selection:reviewers")
        self.assertEqual(phase(workflow, "initial-consolidation").needs, ("delivery-accounting",))
        self.assertEqual(phase(workflow, "cross-examination").needs, ("initial-consolidation",))
        self.assertEqual(phase(workflow, "consolidation").needs, ("cross-examination",))

    def test_team_review_declares_every_phase_in_order(self):
        workflow = load_team_review()
        self.assertEqual(tuple(item.id for item in workflow.phases), PHASE_ORDER)

    def test_only_the_final_phase_produces_the_report(self):
        workflow = load_team_review()
        producers = [
            item.id for item in workflow.phases if "artifact:final-report" in item.produces
        ]
        self.assertEqual(producers, ["consolidation"])

    def test_every_record_contract_exists(self):
        for name in RECORD_CONTRACTS:
            with self.subTest(contract=name):
                self.assertTrue(
                    (REPO_ROOT / "plugins/senior-review/contracts" / f"{name}.toml").is_file()
                )

    def test_every_host_preserves_team_review_contract(self):
        for host in HOSTS:
            with self.subTest(host=host):
                package = compiled_review_package(host)
                self.assertTrue(package.has_isolated_workers)
                self.assertTrue(package.has_delivery_barrier)
                self.assertTrue(package.has_cross_examination)
                self.assertTrue(package.has_consolidation)
                self.assertEqual(package.artifact_root("xray"), ".deep-dive")

    def test_senior_review_no_longer_depends_on_an_external_team_runtime(self):
        plugin = load_plugin(REPO_ROOT / "plugins/senior-review")
        self.assertNotIn(
            "agent-teams",
            " ".join(plugin.required_dependencies),
            "scheduling belongs to the host harness, not to a runtime dependency",
        )

    def test_every_dimension_plugin_stays_a_hard_dependency(self):
        plugin = load_plugin(REPO_ROOT / "plugins/senior-review")
        for dimension in (
            "repo-hygiene",
            "codebase-xray",
            "abstraction-architect",
            "react-development",
            "platform-engineering",
            "typescript-development",
            "testing",
        ):
            self.assertIn(dimension, plugin.required_dependencies)


if __name__ == "__main__":
    unittest.main()
