"""Immutable types for the neutral Daodan control plane.

Every type here is host-neutral by construction: nothing names a Claude team
API, a Copilot subagent tool or a Codex dispatch primitive. Markdown remains the
behavioural source, so no type carries a prompt body.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SCHEMA = "daodan/v1"

Isolation = Literal["shared", "required"]
JoinPolicy = Literal["all-delivered", "best-effort"]
Concurrency = Literal["preferred", "required", "forbidden"]

ISOLATIONS: tuple[str, ...] = ("shared", "required")
JOIN_POLICIES: tuple[str, ...] = ("all-delivered", "best-effort")
CONCURRENCIES: tuple[str, ...] = ("preferred", "required", "forbidden")


@dataclass(frozen=True)
class ContractSpec:
    inputs: tuple[str, ...]
    outcomes: tuple[str, ...]
    artifacts: tuple[str, ...]
    schemas: tuple[Path, ...] = ()


@dataclass(frozen=True)
class PhaseSpec:
    id: str
    needs: tuple[str, ...] = ()
    invoke: str | None = None
    role: str | None = None
    fanout: tuple[str, ...] = ()
    fanout_from: str | None = None
    isolation: Isolation = "shared"
    join: JoinPolicy | None = None
    concurrency: Concurrency = "preferred"
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowSpec:
    name: str
    entrypoint: Path
    phases: tuple[PhaseSpec, ...]
    contract: ContractSpec


@dataclass(frozen=True)
class CapabilityRequirements:
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentIndex:
    skills: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    workflows: tuple[str, ...] = ()
    policies: tuple[str, ...] = ()


@dataclass(frozen=True)
class McpServerSpec:
    """One stdio MCP server the plugin ships and needs the host to start.

    The command and its arguments are written the way a kernel writes every
    path, with `${CLAUDE_PLUGIN_ROOT}` naming the installed package; each
    adapter decides whether it can render the declaration as a manifest the
    host starts on its own, or must ask the user to register it.
    """

    name: str
    command: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class PluginSpec:
    root: Path
    schema: str
    name: str
    version: str
    description: str
    license: str
    capabilities: CapabilityRequirements
    required_dependencies: tuple[str, ...]
    components: ComponentIndex
    workflows: tuple[WorkflowSpec, ...]
    mcp_servers: tuple[McpServerSpec, ...] = ()


class ModelError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")
