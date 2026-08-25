"""Capability-parity tests for the three peer harnesses."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.daodan.adapter import (  # noqa: E402
    HOSTS,
    CoordinationStrategy,
    load_adapter,
    resolve_support,
    select_coordination,
)
from scripts.daodan.load import load_plugin  # noqa: E402
from scripts.daodan.validate import CAPABILITY_REGISTRY  # noqa: E402

ADAPTERS = REPO_ROOT / "adapters"
VALID = REPO_ROOT / "tests/fixtures/daodan/valid/plugins/example"

STRATEGY_TABLE = {
    "parallel-subagents": CoordinationStrategy(
        "parallel-subagents", "baseline", True, True, False, False, "inline-prompt"
    ),
    "serial-isolated": CoordinationStrategy(
        "serial-isolated", "baseline", True, False, False, False, "inline-prompt"
    ),
    "single-context": CoordinationStrategy(
        "single-context", "baseline", False, False, False, False, "inline-prompt"
    ),
}


def load_example_plugin():
    return load_plugin(VALID)


def load_review_workflow():
    return load_example_plugin().workflows[0]


def adapter_with_strategies(*names: str):
    adapter = load_adapter(ADAPTERS, "codex")
    return replace(adapter, strategies=tuple(STRATEGY_TABLE[name] for name in names))


class AdapterParityTests(unittest.TestCase):
    def test_every_host_binds_every_registry_capability(self):
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ADAPTERS, host)
                self.assertEqual(set(adapter.bindings), set(CAPABILITY_REGISTRY))

    def test_example_plugin_is_supported_on_every_host(self):
        for host in HOSTS:
            with self.subTest(host=host):
                report = resolve_support(load_example_plugin(), load_adapter(ADAPTERS, host))
                self.assertIn(report.state, {"native", "adapted"})
                self.assertEqual(report.missing_capabilities, ())

    def test_required_capability_without_binding_is_unsupported(self):
        adapter = replace(load_adapter(ADAPTERS, "codex"), bindings={})
        report = resolve_support(load_example_plugin(), adapter)
        self.assertEqual(report.state, "unsupported")
        self.assertIn("repository.read", report.missing_capabilities)

    def test_optional_capability_never_hides_a_required_failure(self):
        adapter = load_adapter(ADAPTERS, "codex")
        bindings = dict(adapter.bindings)
        bindings["contexts.isolate"] = replace(bindings["contexts.isolate"], state="unsupported")
        report = resolve_support(load_example_plugin(), replace(adapter, bindings=bindings))
        self.assertEqual(report.state, "unsupported")

    def test_preferred_parallelism_can_fall_back_to_serial_isolation(self):
        adapter = adapter_with_strategies("serial-isolated")
        strategy = select_coordination(load_review_workflow(), adapter)
        self.assertEqual(strategy.name, "serial-isolated")
        self.assertTrue(strategy.isolated)
        self.assertFalse(strategy.parallel)

    def test_shared_context_cannot_satisfy_independent_review(self):
        adapter = adapter_with_strategies("single-context")
        self.assertIsNone(select_coordination(load_review_workflow(), adapter))

    def test_host_order_selects_the_first_viable_strategy(self):
        adapter = adapter_with_strategies("parallel-subagents", "serial-isolated")
        self.assertEqual(select_coordination(load_review_workflow(), adapter).name, "parallel-subagents")

    def test_required_concurrency_cannot_select_serial(self):
        workflow = load_review_workflow()
        phases = (replace(workflow.phases[0], concurrency="required"),)
        workflow = replace(workflow, phases=phases)
        self.assertIsNone(select_coordination(workflow, adapter_with_strategies("serial-isolated")))
        self.assertEqual(
            select_coordination(workflow, adapter_with_strategies("parallel-subagents")).name,
            "parallel-subagents",
        )

    def test_no_host_offers_a_single_context_fallback(self):
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ADAPTERS, host)
                self.assertTrue(all(strategy.isolated for strategy in adapter.strategies))


if __name__ == "__main__":
    unittest.main()
