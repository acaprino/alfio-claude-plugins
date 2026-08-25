"""Host harness contracts.

The core owns roles, workflow dependencies, required context isolation, joins and
observable contracts. A harness owns host APIs, dispatch, scheduling, retries and
result collection. This module is the seam: it loads what one host can actually
do, decides whether a neutral plugin is expressible there, and picks the
coordination strategy that satisfies the workflow's declared constraints.

Nothing here decides what a plugin means. It decides only how a host runs it.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from .model import PluginSpec, WorkflowSpec

HOSTS: tuple[str, ...] = ("claude", "copilot", "codex")

CapabilityState = Literal["native", "adapted", "unsupported"]

#: Worst state wins, so the order here is the comparison order.
STATE_ORDER: tuple[str, ...] = ("native", "adapted", "unsupported")


@dataclass(frozen=True)
class CapabilityBinding:
    state: CapabilityState
    strategy: str
    value: str | None = None


@dataclass(frozen=True)
class CoordinationStrategy:
    name: str
    availability: Literal["baseline", "runtime-optional"]
    isolated: bool
    parallel: bool
    shared_tasks: bool
    peer_messaging: bool
    role_delivery: Literal["named-agent", "inline-prompt"]


@dataclass(frozen=True)
class SupportReport:
    host: str
    plugin: str
    state: str
    missing_capabilities: tuple[str, ...]
    workflow_strategies: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class HostAdapter:
    host: str
    bindings: Mapping[str, CapabilityBinding]
    strategies: tuple[CoordinationStrategy, ...]
    layout: Mapping[str, str]


class AdapterError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def _read(path: Path) -> Mapping[str, object]:
    if not path.is_file():
        raise AdapterError(path, "file does not exist")
    with path.open("rb") as handle:
        try:
            return tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            raise AdapterError(path, f"invalid TOML: {error}") from error


def load_adapter(root: Path, host: str) -> HostAdapter:
    """Load one host's capability bindings, coordination order and layout."""
    if host not in HOSTS:
        raise AdapterError(Path(root), f"unknown host {host!r}")
    directory = Path(root) / host

    capabilities_path = directory / "capabilities.toml"
    capabilities_table = _read(capabilities_path).get("capabilities", {})
    if not isinstance(capabilities_table, dict):
        raise AdapterError(capabilities_path, "[capabilities] must be a table")
    bindings: dict[str, CapabilityBinding] = {}
    for name, entry in capabilities_table.items():
        if not isinstance(entry, dict):
            raise AdapterError(capabilities_path, f"{name} must be a table")
        state = entry.get("state")
        if state not in STATE_ORDER:
            raise AdapterError(capabilities_path, f"{name} has invalid state {state!r}")
        strategy = entry.get("strategy")
        if not isinstance(strategy, str):
            raise AdapterError(capabilities_path, f"{name} requires a string strategy")
        value = entry.get("value")
        if value is not None and not isinstance(value, str):
            raise AdapterError(capabilities_path, f"{name} value must be a string")
        bindings[name] = CapabilityBinding(state=state, strategy=strategy, value=value)

    coordination_path = directory / "coordination.toml"
    rows = _read(coordination_path).get("strategies", [])
    if not isinstance(rows, list) or not rows:
        raise AdapterError(coordination_path, "at least one [[strategies]] entry is required")
    strategies: list[CoordinationStrategy] = []
    for row in rows:
        if not isinstance(row, dict):
            raise AdapterError(coordination_path, "each strategy must be a table")
        try:
            strategy = CoordinationStrategy(
                name=row["name"],
                availability=row["availability"],
                isolated=bool(row["isolated"]),
                parallel=bool(row["parallel"]),
                shared_tasks=bool(row["shared_tasks"]),
                peer_messaging=bool(row["peer_messaging"]),
                role_delivery=row["role_delivery"],
            )
        except KeyError as error:
            raise AdapterError(coordination_path, f"strategy is missing {error.args[0]!r}") from error
        if strategy.availability not in {"baseline", "runtime-optional"}:
            raise AdapterError(coordination_path, f"{strategy.name}: invalid availability")
        if strategy.role_delivery not in {"named-agent", "inline-prompt"}:
            raise AdapterError(coordination_path, f"{strategy.name}: invalid role_delivery")
        strategies.append(strategy)

    layout_path = directory / "layout.toml"
    layout = _read(layout_path).get("layout", {})
    if not isinstance(layout, dict) or not all(isinstance(item, str) for item in layout.values()):
        raise AdapterError(layout_path, "[layout] must be a table of strings")

    return HostAdapter(
        host=host,
        bindings=bindings,
        strategies=tuple(strategies),
        layout=dict(layout),
    )


def _workflow_demands(workflow: WorkflowSpec) -> tuple[bool, bool, bool]:
    """Return (needs isolation, needs parallelism, forbids parallelism)."""
    needs_isolation = any(phase.isolation == "required" for phase in workflow.phases)
    fanout_phases = [phase for phase in workflow.phases if phase.fanout or phase.fanout_from]
    needs_parallel = any(phase.concurrency == "required" for phase in fanout_phases)
    forbids_parallel = any(phase.concurrency == "forbidden" for phase in workflow.phases)
    return needs_isolation, needs_parallel, forbids_parallel


def select_coordination(
    workflow: WorkflowSpec, adapter: HostAdapter
) -> CoordinationStrategy | None:
    """Pick the first host strategy that satisfies the workflow's constraints.

    Preferred concurrency is a preference: it can settle for serial isolation.
    Required concurrency cannot.
    """
    needs_isolation, needs_parallel, forbids_parallel = _workflow_demands(workflow)
    for strategy in adapter.strategies:
        if needs_isolation and not strategy.isolated:
            continue
        if needs_parallel and not strategy.parallel:
            continue
        if forbids_parallel and strategy.parallel:
            continue
        return strategy
    return None


def resolve_support(plugin: PluginSpec, adapter: HostAdapter) -> SupportReport:
    """Decide whether one plugin is expressible on one host.

    The worst required capability state is the plugin state. Optional
    capabilities can select a stronger strategy but never mask a required
    failure, and a workflow with no viable coordination strategy is unsupported
    however well its capabilities bind.
    """
    missing: list[str] = []
    state_index = 0
    for capability in plugin.capabilities.required:
        binding = adapter.bindings.get(capability)
        if binding is None or binding.state == "unsupported":
            missing.append(capability)
            state_index = STATE_ORDER.index("unsupported")
            continue
        state_index = max(state_index, STATE_ORDER.index(binding.state))

    workflow_strategies: list[tuple[str, str]] = []
    for workflow in plugin.workflows:
        strategy = select_coordination(workflow, adapter)
        if strategy is None:
            state_index = STATE_ORDER.index("unsupported")
            workflow_strategies.append((workflow.name, "none"))
        else:
            workflow_strategies.append((workflow.name, strategy.name))

    return SupportReport(
        host=adapter.host,
        plugin=plugin.name,
        state=STATE_ORDER[state_index],
        missing_capabilities=tuple(missing),
        workflow_strategies=tuple(workflow_strategies),
    )
