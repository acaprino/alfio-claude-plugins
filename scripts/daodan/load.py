"""Strict TOML loading for the neutral Daodan control plane.

Loading is deliberately unforgiving: a missing required table or an unknown key
is a ``ModelError`` rather than a default, because a silently defaulted control
plane produces a package that validates and then behaves differently on one
host. Prompt bodies are never accepted here; they live in Markdown.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Mapping

from .model import (
    CONCURRENCIES,
    ISOLATIONS,
    JOIN_POLICIES,
    SCHEMA,
    CapabilityRequirements,
    ComponentIndex,
    ContractSpec,
    McpServerSpec,
    ModelError,
    PhaseSpec,
    PluginSpec,
    WorkflowSpec,
)

PLUGIN_KEYS = frozenset(
    {
        "schema",
        "name",
        "version",
        "description",
        "license",
        "capabilities",
        "dependencies",
        "components",
        "mcp",
    }
)
PLUGIN_REQUIRED_KEYS = ("schema", "name", "version", "description", "license")
PLUGIN_REQUIRED_TABLES = ("capabilities", "dependencies", "components")

CAPABILITY_KEYS = frozenset({"required", "optional"})
DEPENDENCY_KEYS = frozenset({"required"})
COMPONENT_KEYS = frozenset({"skills", "roles", "workflows", "policies"})
MCP_KEYS = frozenset({"servers"})
MCP_SERVER_KEYS = frozenset({"name", "command", "args"})

WORKFLOW_KEYS = frozenset({"name", "entrypoint", "phases", "contract"})
PHASE_KEYS = frozenset(
    {
        "id",
        "needs",
        "invoke",
        "role",
        "fanout",
        "fanout_from",
        "isolation",
        "join",
        "concurrency",
        "consumes",
        "produces",
    }
)
CONTRACT_KEYS = frozenset({"inputs", "outcomes", "artifacts", "schemas"})


def _read(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise ModelError(path, "file does not exist")
    with path.open("rb") as handle:
        try:
            return tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            raise ModelError(path, f"invalid TOML: {error}") from error


def _reject_unknown(
    path: Path, table: Mapping[str, Any], allowed: frozenset[str], where: str
) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ModelError(path, f"unknown {where} key(s): {', '.join(unknown)}")


def _string(path: Path, table: Mapping[str, Any], key: str, where: str) -> str:
    value = table.get(key)
    if not isinstance(value, str):
        raise ModelError(path, f"{where} requires a string {key!r}")
    return value


def _strings(path: Path, table: Mapping[str, Any], key: str, where: str) -> tuple[str, ...]:
    value = table.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ModelError(path, f"{where}.{key} must be an array of strings")
    return tuple(value)


def _choice(path: Path, value: Any, allowed: tuple[str, ...], where: str) -> str:
    if value not in allowed:
        raise ModelError(path, f"{where} must be one of {', '.join(allowed)}, got {value!r}")
    return value


def _relative(path: Path, value: str, where: str) -> Path:
    candidate = Path(value.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ModelError(path, f"{where} must stay inside the plugin: {value!r}")
    return Path(*candidate.parts)


def load_contract(path: Path, table: Mapping[str, Any]) -> ContractSpec:
    _reject_unknown(path, table, CONTRACT_KEYS, "contract")
    schemas = tuple(
        _relative(path, item, "contract.schemas")
        for item in _strings(path, table, "schemas", "contract")
    )
    return ContractSpec(
        inputs=_strings(path, table, "inputs", "contract"),
        outcomes=_strings(path, table, "outcomes", "contract"),
        artifacts=_strings(path, table, "artifacts", "contract"),
        schemas=schemas,
    )


def load_phase(path: Path, table: Mapping[str, Any]) -> PhaseSpec:
    _reject_unknown(path, table, PHASE_KEYS, "phase")
    identity = _string(path, table, "id", "phase")
    join = table.get("join")
    if join is not None:
        join = _choice(path, join, JOIN_POLICIES, f"phase {identity!r} join")
    for optional_key in ("invoke", "role", "fanout_from"):
        if optional_key in table and not isinstance(table[optional_key], str):
            raise ModelError(path, f"phase {identity!r} {optional_key} must be a string")
    return PhaseSpec(
        id=identity,
        needs=_strings(path, table, "needs", f"phase {identity!r}"),
        invoke=table.get("invoke"),
        role=table.get("role"),
        fanout=_strings(path, table, "fanout", f"phase {identity!r}"),
        fanout_from=table.get("fanout_from"),
        isolation=_choice(
            path, table.get("isolation", "shared"), ISOLATIONS, f"phase {identity!r} isolation"
        ),
        join=join,
        concurrency=_choice(
            path,
            table.get("concurrency", "preferred"),
            CONCURRENCIES,
            f"phase {identity!r} concurrency",
        ),
        consumes=_strings(path, table, "consumes", f"phase {identity!r}"),
        produces=_strings(path, table, "produces", f"phase {identity!r}"),
    )


def load_workflow(path: Path, workflow_directory: Path) -> WorkflowSpec:
    table = _read(path)
    _reject_unknown(path, table, WORKFLOW_KEYS, "workflow")
    for key in ("name", "entrypoint"):
        if key not in table:
            raise ModelError(path, f"workflow requires {key!r}")
    if "contract" not in table:
        raise ModelError(path, "workflow requires a [contract] table")
    phases = table.get("phases", [])
    if not isinstance(phases, list) or not phases:
        raise ModelError(path, "workflow requires at least one [[phases]] entry")

    entrypoint = workflow_directory / _relative(
        path, _string(path, table, "entrypoint", "workflow"), "entrypoint"
    )
    contract_table = table["contract"]
    if not isinstance(contract_table, dict):
        raise ModelError(path, "[contract] must be a table")

    return WorkflowSpec(
        name=_string(path, table, "name", "workflow"),
        entrypoint=entrypoint,
        phases=tuple(load_phase(path, phase) for phase in phases),
        contract=load_contract(path, contract_table),
    )


def load_mcp_servers(manifest: Path, table: Mapping[str, Any]) -> tuple[McpServerSpec, ...]:
    """Read the optional `[mcp]` table: `[[mcp.servers]]` entries with name, command, args."""
    mcp_table = table.get("mcp")
    if mcp_table is None:
        return ()
    if not isinstance(mcp_table, dict):
        raise ModelError(manifest, "[mcp] must be a table")
    _reject_unknown(manifest, mcp_table, MCP_KEYS, "mcp")
    rows = mcp_table.get("servers", [])
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ModelError(manifest, "mcp.servers must be an array of tables")
    servers = []
    for row in rows:
        _reject_unknown(manifest, row, MCP_SERVER_KEYS, "mcp.servers")
        servers.append(
            McpServerSpec(
                name=_string(manifest, row, "name", "mcp.servers"),
                command=_string(manifest, row, "command", "mcp.servers"),
                args=_strings(manifest, row, "args", "mcp.servers"),
            )
        )
    return tuple(servers)


def load_plugin(path: Path) -> PluginSpec:
    """Load one plugin content kernel from its directory."""
    root = Path(path)
    manifest = root / "plugin.toml"
    table = _read(manifest)
    _reject_unknown(manifest, table, PLUGIN_KEYS, "plugin")

    for key in PLUGIN_REQUIRED_KEYS:
        if key not in table:
            raise ModelError(manifest, f"plugin requires {key!r}")
    for key in PLUGIN_REQUIRED_TABLES:
        if not isinstance(table.get(key), dict):
            raise ModelError(manifest, f"plugin requires a [{key}] table")

    schema = _string(manifest, table, "schema", "plugin")
    if schema != SCHEMA:
        raise ModelError(manifest, f"unsupported schema {schema!r}, expected {SCHEMA!r}")

    capabilities_table = table["capabilities"]
    _reject_unknown(manifest, capabilities_table, CAPABILITY_KEYS, "capabilities")
    capabilities = CapabilityRequirements(
        required=_strings(manifest, capabilities_table, "required", "capabilities"),
        optional=_strings(manifest, capabilities_table, "optional", "capabilities"),
    )

    dependencies_table = table["dependencies"]
    _reject_unknown(manifest, dependencies_table, DEPENDENCY_KEYS, "dependencies")
    required_dependencies = _strings(manifest, dependencies_table, "required", "dependencies")

    components_table = table["components"]
    _reject_unknown(manifest, components_table, COMPONENT_KEYS, "components")
    components = ComponentIndex(
        skills=_strings(manifest, components_table, "skills", "components"),
        roles=_strings(manifest, components_table, "roles", "components"),
        workflows=_strings(manifest, components_table, "workflows", "components"),
        policies=_strings(manifest, components_table, "policies", "components"),
    )

    workflows = tuple(
        load_workflow(root / "workflows" / f"{name}.toml", Path("workflows"))
        for name in components.workflows
    )

    return PluginSpec(
        root=root,
        schema=schema,
        name=_string(manifest, table, "name", "plugin"),
        version=_string(manifest, table, "version", "plugin"),
        description=_string(manifest, table, "description", "plugin"),
        license=_string(manifest, table, "license", "plugin"),
        capabilities=capabilities,
        required_dependencies=required_dependencies,
        components=components,
        workflows=workflows,
        mcp_servers=load_mcp_servers(manifest, table),
    )
