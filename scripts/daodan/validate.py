"""Semantic validation of neutral Daodan plugin kernels.

The loader proves a control plane is well-formed TOML. This module proves it is
coherent: identities are kebab-case, every referenced path stays inside its
plugin, every component and dependency reference resolves, every capability
comes from the closed registry, workflow graphs are acyclic, and a workflow that
declares independent review actually asks for isolation and an all-delivered
barrier.

Passes run in a fixed order so diagnostics are deterministic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, Sequence

from .model import PluginSpec

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

#: The closed capability registry. A capability outside this set is a typo or an
#: unbound host mechanism, and either way no adapter can promise it.
CAPABILITY_REGISTRY: frozenset[str] = frozenset(
    {
        "repository.read",
        "repository.write",
        "shell.execute",
        "network.fetch",
        "contexts.isolate",
        "roles.dispatch",
        "execution.parallel",
        "tasks.share",
        "peers.message",
        "hooks.lifecycle",
    }
)

#: Declaring this outcome is what makes a workflow's fan-out independent, and
#: therefore what makes isolation mandatory rather than an optimization.
INDEPENDENT_REVIEW_OUTCOME = "reviewers-use-isolated-contexts"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: Path
    message: str


def _is_escaping(reference: str) -> bool:
    candidate = Path(reference.replace("\\", "/"))
    return candidate.is_absolute() or ".." in candidate.parts


def _split_reference(reference: str) -> tuple[str, str]:
    """Split ``kind:name`` into its parts, defaulting the kind to ``role``."""
    kind, separator, name = reference.partition(":")
    if not separator:
        return "role", kind
    return kind, name


def validate_identity(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    if not KEBAB.match(plugin.name):
        issues.append(ValidationIssue("non-kebab-identity", manifest, plugin.name))
    for group, names in (
        ("skills", plugin.components.skills),
        ("roles", plugin.components.roles),
        ("workflows", plugin.components.workflows),
        ("policies", plugin.components.policies),
    ):
        for name in names:
            if not KEBAB.match(name):
                issues.append(
                    ValidationIssue("non-kebab-identity", manifest, f"components.{group}: {name}")
                )
    return issues


def validate_paths(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    for group, names in (
        ("skills", plugin.components.skills),
        ("roles", plugin.components.roles),
        ("workflows", plugin.components.workflows),
        ("policies", plugin.components.policies),
    ):
        for name in names:
            if _is_escaping(name):
                issues.append(
                    ValidationIssue("path-outside-plugin", manifest, f"components.{group}: {name}")
                )
    for workflow in plugin.workflows:
        for reference in (workflow.entrypoint, *workflow.contract.schemas):
            if _is_escaping(reference.as_posix()):
                issues.append(
                    ValidationIssue("path-outside-plugin", workflow.entrypoint, reference.as_posix())
                )
        for phase in workflow.phases:
            for reference in phase.fanout:
                _, name = _split_reference(reference)
                if _is_escaping(name):
                    issues.append(
                        ValidationIssue("path-outside-plugin", workflow.entrypoint, reference)
                    )
    return issues


def validate_components(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    seen: set[str] = set()
    for names in (
        plugin.components.skills,
        plugin.components.roles,
        plugin.components.workflows,
        plugin.components.policies,
    ):
        for name in names:
            if name in seen:
                issues.append(ValidationIssue("duplicate-component", manifest, name))
            seen.add(name)

    for name in plugin.components.roles:
        if _is_escaping(name):
            continue
        if not (plugin.root / "roles" / f"{name}.md").is_file():
            issues.append(
                ValidationIssue("missing-component-file", manifest, f"roles/{name}.md")
            )
    for name in plugin.components.skills:
        if _is_escaping(name):
            continue
        if not (plugin.root / "skills" / name / "SKILL.md").is_file():
            issues.append(
                ValidationIssue("missing-component-file", manifest, f"skills/{name}/SKILL.md")
            )
    for workflow in plugin.workflows:
        if not (plugin.root / workflow.entrypoint).is_file():
            issues.append(
                ValidationIssue(
                    "missing-component-file", manifest, workflow.entrypoint.as_posix()
                )
            )
        for schema in workflow.contract.schemas:
            if not (plugin.root / schema).is_file():
                issues.append(
                    ValidationIssue("missing-component-file", manifest, schema.as_posix())
                )
    return issues


def validate_dependencies(plugin: PluginSpec) -> list[ValidationIssue]:
    """Static fan-out roles must resolve inside this plugin or a required dependency.

    There is no optional local dependency by policy, so a role that resolves
    nowhere is a broken package rather than a degraded one.
    """
    issues: list[ValidationIssue] = []
    roles = set(plugin.components.roles)
    dependencies = set(plugin.required_dependencies)
    for workflow in plugin.workflows:
        for phase in workflow.phases:
            references = list(phase.fanout)
            if phase.role is not None:
                references.append(f"role:{phase.role}")
            for reference in references:
                kind, name = _split_reference(reference)
                if kind != "role":
                    continue
                owner, separator, role = name.partition("/")
                if separator:
                    if owner not in dependencies:
                        issues.append(
                            ValidationIssue(
                                "undeclared-dependency", workflow.entrypoint, reference
                            )
                        )
                elif name not in roles:
                    issues.append(
                        ValidationIssue("unknown-role", workflow.entrypoint, reference)
                    )
    return issues


def validate_capabilities(
    plugin: PluginSpec, capabilities: AbstractSet[str]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = plugin.root / "plugin.toml"
    declared = list(plugin.capabilities.required) + list(plugin.capabilities.optional)
    for capability in declared:
        if capability not in capabilities:
            issues.append(ValidationIssue("unknown-capability", manifest, capability))
    overlap = sorted(set(plugin.capabilities.required) & set(plugin.capabilities.optional))
    for capability in overlap:
        issues.append(ValidationIssue("capability-declared-twice", manifest, capability))
    return issues


def validate_workflow_graph(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for workflow in plugin.workflows:
        phases = {phase.id: phase for phase in workflow.phases}
        colors = {phase_id: "white" for phase_id in phases}

        def visit(phase_id: str) -> None:
            if colors[phase_id] == "gray":
                issues.append(ValidationIssue("workflow-cycle", workflow.entrypoint, phase_id))
                return
            if colors[phase_id] == "black":
                return
            colors[phase_id] = "gray"
            for dependency in phases[phase_id].needs:
                if dependency not in phases:
                    issues.append(
                        ValidationIssue("unknown-phase", workflow.entrypoint, dependency)
                    )
                else:
                    visit(dependency)
            colors[phase_id] = "black"

        for phase_id in phases:
            visit(phase_id)
    return issues


def validate_execution_contracts(plugin: PluginSpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for workflow in plugin.workflows:
        produced = {item for phase in workflow.phases for item in phase.produces}
        independent = INDEPENDENT_REVIEW_OUTCOME in workflow.contract.outcomes
        for phase in workflow.phases:
            has_fanout = bool(phase.fanout or phase.fanout_from)
            if phase.fanout and phase.fanout_from:
                issues.append(ValidationIssue("ambiguous-fanout", workflow.entrypoint, phase.id))
            if has_fanout and phase.join is None:
                issues.append(ValidationIssue("fanout-needs-join", workflow.entrypoint, phase.id))
            if phase.fanout_from and phase.fanout_from not in produced:
                issues.append(
                    ValidationIssue(
                        "unknown-fanout-selection", workflow.entrypoint, phase.fanout_from
                    )
                )
            if independent and has_fanout and phase.isolation != "required":
                issues.append(
                    ValidationIssue(
                        "independent-fanout-needs-isolation", workflow.entrypoint, phase.id
                    )
                )
            for item in phase.consumes:
                if item not in produced:
                    issues.append(
                        ValidationIssue("unproduced-artifact", workflow.entrypoint, item)
                    )
        for artifact in workflow.contract.artifacts:
            if f"artifact:{artifact}" not in produced:
                issues.append(
                    ValidationIssue("unproduced-artifact", workflow.entrypoint, artifact)
                )
    return issues


def validate_plugins(
    plugins: Sequence[PluginSpec], capabilities: AbstractSet[str]
) -> list[ValidationIssue]:
    """Run every pass over every plugin, in a fixed order."""
    issues: list[ValidationIssue] = []
    for plugin in plugins:
        issues.extend(validate_identity(plugin))
        issues.extend(validate_paths(plugin))
        issues.extend(validate_components(plugin))
        issues.extend(validate_dependencies(plugin))
        issues.extend(validate_capabilities(plugin, capabilities))
        issues.extend(validate_workflow_graph(plugin))
        issues.extend(validate_execution_contracts(plugin))
    return issues
