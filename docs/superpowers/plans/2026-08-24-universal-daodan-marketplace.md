# Universal Daodan Marketplace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Claude-centered repository with Markdown content kernels that deterministic host harnesses package as native Claude Code, GitHub Copilot and Codex marketplaces from the same Git repository.

**Architecture:** Markdown and supporting resources under `plugins/` are each plugin's content kernel; TOML sidecars declare component relationships, workflow constraints and behavioral contracts without embedding prompts. Standard-library Python validates those kernels, lets three adapters supply host-native packaging and execution harnesses, then writes committed `exports/<host>/` packages and three root marketplace manifests. Migration keeps the current Claude marketplace live until strict cross-host parity passes for all 40 plugins, then performs one major cutover and removes the VSIX completely.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `dataclasses`, `hashlib`, `json`, `pathlib`, `shutil`, `tempfile`, `tomllib`, `unittest`), TOML control-plane files, Markdown instructions, JSON host manifests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-24-universal-daodan-marketplace-design.md`

## Global Constraints

- Use Python 3.11 or later and no third-party Python or JavaScript dependency.
- Treat Markdown, scripts, references and assets under `plugins/` as the plugin content kernels; TOML is declarative metadata, never a replacement for prompt behavior.
- Keep `plugins/` and `adapters/` as the only hand-authored plugin-delivery sources. The core owns roles, workflow dependencies, required context isolation, joins and observable contracts. Harnesses own host APIs, dispatch, scheduling, retries and result collection.
- Never name a Claude team API, Copilot subagent tool or Codex dispatch primitive in neutral core content.
- For `team-review`, require isolated reviewer contexts, delivery accounting, an all-delivered barrier, cross-examination and consolidation. Treat parallel execution, shared task lists and peer messaging as harness optimizations.
- Treat every file under `exports/` and all three root marketplace manifests as generated output.
- Never write a partial host tree: render all requested output under a temporary directory and replace live output only after every validator passes.
- Full publication always builds Claude, Copilot and Codex together.
- Every core plugin must be present at one identical semantic version in all three marketplaces.
- A required component in state `unsupported` blocks the complete release.
- Preserve the local mandatory-dependency policy. No local plugin may become an optional installation.
- Preserve `.deep-dive/` as the stable artifact contract for `codebase-xray`.
- Do not use host-tool tokens inside neutral Markdown prose.
- Put every semantic host divergence in a fingerprinted override under `adapters/<host>/overrides/`.
- Do not modify or stage the user's existing untracked `AGENTS.md` or existing content under `.agents/`. At cutover, add only the generated `.agents/plugins/marketplace.json` path explicitly.
- Do not rename the GitHub repository until Task 13 reaches its explicit manual gate.
- Remove the VSIX, its JavaScript lifecycle and its release workflow at cutover. Do not delete historical GitHub Release assets.
- Follow TDD for compiler behavior. Run the existing consistency suite after every task that changes repository behavior.

---

## Milestone A: prove host contracts and build the compiler

### Task 1: Add disposable native-host protocol probes

**Files:**
- Create: `tests/host-probes/README.md`
- Create: `tests/host-probes/claude/.claude-plugin/marketplace.json`
- Create: `tests/host-probes/claude/plugins/probe/.claude-plugin/plugin.json`
- Create: `tests/host-probes/claude/plugins/probe/skills/probe/SKILL.md`
- Create: `tests/host-probes/claude/plugins/probe/agents/probe-worker.md`
- Create: `tests/host-probes/claude/plugins/probe/commands/probe-team.md`
- Create: `tests/host-probes/copilot/.github/plugin/marketplace.json`
- Create: `tests/host-probes/copilot/plugins/probe/plugin.json`
- Create: `tests/host-probes/copilot/plugins/probe/skills/probe/SKILL.md`
- Create: `tests/host-probes/copilot/plugins/probe/agents/probe-coordinator.agent.md`
- Create: `tests/host-probes/copilot/plugins/probe/agents/probe-worker.agent.md`
- Create: `tests/host-probes/codex/.agents/plugins/marketplace.json`
- Create: `tests/host-probes/codex/plugins/probe/.codex-plugin/plugin.json`
- Create: `tests/host-probes/codex/plugins/probe/skills/probe/SKILL.md`
- Create: `tests/host-probes/codex/plugins/probe/hooks/hooks.json`
- Create: `tests/host-probes/codex/plugins/probe/.codex/agents/probe.toml`
- Create: `scripts/probe_host_marketplaces.py`
- Test: `tests/test_host_probe_fixtures.py`

**Interfaces:**
- Consumes: native marketplace paths documented in the approved spec.
- Produces: `validate_fixture(root: Path, host: str) -> list[str]` and a checked-in evidence table for isolated workers, parallel fan-out, shared tasks, peer messaging, worker allowlists and plugin-packaged role discovery.

- [x] **Step 1: Write structural tests for the three disposable marketplaces**

```python
class HostProbeFixtureTests(unittest.TestCase):
    def test_each_host_has_marketplace_and_plugin_manifest(self):
        expected = {
            "claude": (".claude-plugin/marketplace.json", ".claude-plugin/plugin.json"),
            "copilot": (".github/plugin/marketplace.json", "plugin.json"),
            "codex": (".agents/plugins/marketplace.json", ".codex-plugin/plugin.json"),
        }
        for host, (marketplace, manifest) in expected.items():
            root = Path("tests/host-probes") / host
            self.assertTrue((root / marketplace).is_file())
            self.assertTrue((root / "plugins/probe" / manifest).is_file())
```

- [x] **Step 2: Run the test and verify it fails because the fixtures do not exist**

Run: `python -m unittest discover -s tests -p "test_host_probe_fixtures.py" -v`

Expected: FAIL on the first missing marketplace path.

- [x] **Step 3: Add minimal native manifests and one probe skill per host**

Use plugin name `daodan-probe`, version `0.0.1`, and single-worker output contract `Return exactly DAODAN_PROBE_OK.` Every marketplace source must be a repository-relative path to `./plugins/probe`.

Each fixture also defines coordinator instructions that dispatch two workers with different nonce values, require both deliveries before returning and ask for parallel execution when available. Claude additionally probes native Agent Teams and its isolated-subagent fallback. Copilot restricts the coordinator to `probe-worker` through its `agents` frontmatter and enables the `agent` tool. Codex includes both a normal skill and `.codex/agents/probe.toml` to determine whether plugin-installed project-scoped custom agents are discovered. If Codex does not discover that file, its accepted role-delivery strategy is an inline role body supplied to a runtime subagent.

- [x] **Step 4: Implement fixture validation**

```python
MARKETPLACE_PATH = {
    "claude": Path(".claude-plugin/marketplace.json"),
    "copilot": Path(".github/plugin/marketplace.json"),
    "codex": Path(".agents/plugins/marketplace.json"),
}

def validate_fixture(root: Path, host: str) -> list[str]:
    errors: list[str] = []
    catalog = json.loads((root / MARKETPLACE_PATH[host]).read_text(encoding="utf-8"))
    if len(catalog.get("plugins", [])) != 1:
        errors.append(f"{host}: expected one probe plugin")
    return errors
```

- [x] **Step 5: Run structural and native smoke probes** (Claude and Codex measured end to end, Copilot structurally only: see `tests/host-probes/README.md`)

Run the structural test first. Then, in disposable host profiles, run:

```text
claude plugin validate tests/host-probes/claude
copilot plugin marketplace add ./tests/host-probes/copilot
codex plugin marketplace add ./tests/host-probes/codex
```

Browse and install `daodan-probe`, start a fresh session, invoke the single-worker and two-worker probes, and record the observations in this exact table in `tests/host-probes/README.md`:

```text
host | isolated workers | parallel fan-out | shared tasks | peer messaging | worker allowlist | packaged roles
```

The release baseline requires `isolated workers = yes` for every host. `parallel fan-out`, `shared tasks` and `peer messaging` may be `conditional` or `no`. Copilot must report `worker allowlist = yes`. Codex may report `packaged roles = no` only when inline role delivery succeeds. Remove each disposable marketplace after the probe. Expected single-worker result on every host: `DAODAN_PROBE_OK`. Expected coordinator result: both unique worker nonces plus `DELIVERED=2/2`.

- [x] **Step 6: Commit the protocol fixtures**

```bash
git add tests/host-probes tests/test_host_probe_fixtures.py scripts/probe_host_marketplaces.py
git commit -m "Add native marketplace protocol probes"
```

### Task 2: Define and load the neutral TOML model

**Files:**
- Create: `scripts/daodan/__init__.py`
- Create: `scripts/daodan/model.py`
- Create: `scripts/daodan/load.py`
- Create: `tests/fixtures/daodan/valid/plugins/example/plugin.toml`
- Create: `tests/fixtures/daodan/valid/plugins/example/workflows/review.toml`
- Create: `tests/fixtures/daodan/valid/plugins/example/workflows/review.md`
- Create: `tests/fixtures/daodan/valid/plugins/example/roles/inspector.md`
- Create: `tests/fixtures/daodan/valid/plugins/example/contracts/reviewer-result.toml`
- Create: `tests/test_daodan_model.py`

**Interfaces:**
- Consumes: `plugin.toml` and workflow TOML defined by the spec.
- Produces: `CapabilityRequirements`, `ComponentIndex`, `PluginSpec`, `WorkflowSpec`, `PhaseSpec`, `ContractSpec`, and `load_plugin(path: Path) -> PluginSpec`.

- [x] **Step 1: Write failing loader tests**

```python
class NeutralModelTests(unittest.TestCase):
    def test_loads_plugin_and_workflow(self):
        plugin = load_plugin(Path("tests/fixtures/daodan/valid/plugins/example"))
        self.assertEqual(plugin.name, "example")
        self.assertEqual(plugin.version, "1.2.3")
        self.assertEqual(plugin.workflows[0].phases[0].id, "inspect")
        self.assertEqual(plugin.workflows[0].phases[0].isolation, "required")
        self.assertEqual(plugin.workflows[0].phases[0].join, "all-delivered")
        self.assertEqual(plugin.workflows[0].contract.artifacts, ("report",))
        self.assertEqual(plugin.workflows[0].contract.schemas, (Path("contracts/reviewer-result.toml"),))
```

- [x] **Step 2: Run the test and verify the module is missing**

Run: `python -m unittest discover -s tests -p "test_daodan_model.py" -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.daodan'`.

- [x] **Step 3: Add immutable model types**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Isolation = Literal["shared", "required"]
JoinPolicy = Literal["all-delivered", "best-effort"]
Concurrency = Literal["preferred", "required", "forbidden"]

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

class ModelError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")
```

- [x] **Step 4: Implement strict TOML loading**

Create the valid fixture with this control plane:

```toml
# plugin.toml
schema = "daodan/v1"
name = "example"
version = "1.2.3"
description = "Fixture plugin"
license = "MIT"

[capabilities]
required = ["repository.read", "contexts.isolate", "roles.dispatch"]
optional = ["execution.parallel"]

[dependencies]
required = []

[components]
skills = []
roles = ["inspector"]
workflows = ["review"]
policies = []
```

```toml
# workflows/review.toml
name = "review"
entrypoint = "review.md"

[[phases]]
id = "inspect"
fanout = ["role:inspector"]
isolation = "required"
join = "all-delivered"
concurrency = "preferred"
produces = ["artifact:report"]

[contract]
inputs = ["repository"]
outcomes = ["reviewers-use-isolated-contexts"]
artifacts = ["report"]
schemas = ["contracts/reviewer-result.toml"]
```

```toml
# contracts/reviewer-result.toml
schema = "daodan/record/v1"
name = "reviewer-result"
required = ["status", "findings"]

[fields.status]
type = "enum"
values = ["delivered", "failed"]

[fields.findings]
type = "array"
items = "string"
```

Set `workflows/review.md` to `Run every selected inspector independently and return the declared result contract.` Set `roles/inspector.md` to `Inspect the assigned scope without reading another inspector's result.`

Use `tomllib.load()`. Reject missing required tables and unknown top-level keys with `ModelError(path, message)`. Load `[capabilities].required` and `[capabilities].optional` separately. Resolve entrypoint and contract schema paths relative to the plugin root and keep all returned paths normalized but repository-relative. Markdown remains the behavioral source; the loader must not accept prompt bodies inside TOML.

- [x] **Step 5: Run the model tests**

Run: `python -m unittest discover -s tests -p "test_daodan_model.py" -v`

Expected: PASS.

- [x] **Step 6: Commit the neutral loader**

```bash
git add scripts/daodan tests/fixtures/daodan/valid tests/test_daodan_model.py
git commit -m "Add neutral Daodan plugin model"
```

### Task 3: Validate component graphs, contracts and paths

**Files:**
- Create: `scripts/daodan/validate.py`
- Create: `scripts/daodan/trust.py`
- Create: `tests/test_daodan_validate.py`
- Create: `tests/fixtures/daodan/invalid/unknown-capability/plugin.toml`
- Create: `tests/fixtures/daodan/invalid/cyclic-workflow/plugin.toml`
- Create: `tests/fixtures/daodan/invalid/path-escape/plugin.toml`
- Create: `tests/fixtures/daodan/invalid/fanout-without-join/plugin.toml`
- Create: `tests/fixtures/daodan/invalid/fanout-without-isolation/plugin.toml`
- Create: `tests/fixtures/daodan/invalid/forbidden-secret/plugins/example/.env`

**Interfaces:**
- Consumes: `PluginSpec` objects from Task 2.
- Produces: `ValidationIssue(code: str, path: Path, message: str)`, `validate_plugins(plugins: Sequence[PluginSpec], capabilities: AbstractSet[str]) -> list[ValidationIssue]`, and `scan_trust(root: Path, allowlisted: AbstractSet[Path]) -> list[ValidationIssue]`.

- [x] **Step 1: Write failing validation tests**

```python
def test_rejects_cycle_and_path_escape(self):
    issues = validate_fixture("cyclic-workflow") + validate_fixture("path-escape")
    self.assertIn("workflow-cycle", {issue.code for issue in issues})
    self.assertIn("path-outside-plugin", {issue.code for issue in issues})

def test_rejects_incomplete_independent_fanout_contract(self):
    issues = validate_fixture("fanout-without-join") + validate_fixture("fanout-without-isolation")
    self.assertIn("fanout-needs-join", {issue.code for issue in issues})
    self.assertIn("independent-fanout-needs-isolation", {issue.code for issue in issues})

def test_rejects_secret_paths_outside_explicit_test_allowlist(self):
    issues = scan_trust(Path("tests/fixtures/daodan/invalid/forbidden-secret"), frozenset())
    self.assertEqual([issue.code for issue in issues], ["forbidden-secret-path"])
```

- [x] **Step 2: Run the validation tests and verify failure**

Run: `python -m unittest discover -s tests -p "test_daodan_validate.py" -v`

Expected: FAIL because `scripts.daodan.validate` does not exist.

- [x] **Step 3: Implement validation passes**

Add `ValidationIssue` and the central graph checks:

```python
@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: Path
    message: str

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
                    issues.append(ValidationIssue("unknown-phase", workflow.entrypoint, dependency))
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
        independent = "reviewers-use-isolated-contexts" in workflow.contract.outcomes
        for phase in workflow.phases:
            has_fanout = bool(phase.fanout or phase.fanout_from)
            if phase.fanout and phase.fanout_from:
                issues.append(ValidationIssue("ambiguous-fanout", workflow.entrypoint, phase.id))
            if has_fanout and phase.join is None:
                issues.append(ValidationIssue("fanout-needs-join", workflow.entrypoint, phase.id))
            if phase.fanout_from and phase.fanout_from not in produced:
                issues.append(ValidationIssue("unknown-fanout-selection", workflow.entrypoint, phase.fanout_from))
            if independent and has_fanout and phase.isolation != "required":
                issues.append(ValidationIssue("independent-fanout-needs-isolation", workflow.entrypoint, phase.id))
    return issues
```

Implement `validate_identity`, `validate_paths`, `validate_components`, `validate_dependencies` and `validate_capabilities` as separate functions returning the same issue type. Reject non-kebab-case identities, `..`, absolute paths, duplicate component names, static fan-out roles absent from the plugin or its required dependencies, artifact consumers without a producer, undeclared local dependencies and capability names absent from the closed registry. `validate_plugins` concatenates those five passes with `validate_workflow_graph` and `validate_execution_contracts` in that order so diagnostics are deterministic.

Implement `scan_trust` with a sorted repository walk. Report `forbidden-secret-path` for `.env`, `.env.*`, private-key extensions, credential dotfiles and `secrets` or `credentials` directories unless the exact repository-relative path is allowlisted as a synthetic test fixture. Report `embedded-private-key` for PEM private-key headers in text content. Never print matching file contents. Run this scan over `plugins/`, `adapters/` and staged exports.

- [x] **Step 4: Run validation tests and the existing dependency linter**

```bash
python -m unittest discover -s tests -p "test_daodan_validate.py" -v
python scripts/lint_dependency_graph.py
```

Expected: PASS.

- [x] **Step 5: Commit the semantic validator**

```bash
git add scripts/daodan/validate.py tests/test_daodan_validate.py tests/fixtures/daodan/invalid
git commit -m "Validate neutral plugin contracts"
```

### Task 4: Load three peer harnesses and enforce capability parity

**Files:**
- Create: `scripts/daodan/adapter.py`
- Create: `adapters/claude/capabilities.toml`
- Create: `adapters/claude/coordination.toml`
- Create: `adapters/claude/layout.toml`
- Create: `adapters/copilot/capabilities.toml`
- Create: `adapters/copilot/coordination.toml`
- Create: `adapters/copilot/layout.toml`
- Create: `adapters/codex/capabilities.toml`
- Create: `adapters/codex/coordination.toml`
- Create: `adapters/codex/layout.toml`
- Create: `tests/test_daodan_adapters.py`

**Interfaces:**
- Consumes: validated neutral capabilities.
- Produces: `HostAdapter`, `CapabilityBinding`, `CoordinationStrategy`, `load_adapter(root: Path, host: str) -> HostAdapter`, `select_coordination(workflow: WorkflowSpec, adapter: HostAdapter) -> CoordinationStrategy | None`, and `resolve_support(plugin: PluginSpec, adapter: HostAdapter) -> SupportReport`.

- [x] **Step 1: Write failing parity tests**

```python
def test_required_capability_without_binding_is_unsupported(self):
    adapter = replace(load_adapter(Path("adapters"), "codex"), bindings={})
    report = resolve_support(load_example_plugin(), adapter)
    self.assertEqual(report.state, "unsupported")
    self.assertIn("repository.read", report.missing_capabilities)

def test_preferred_parallelism_can_fall_back_to_serial_isolation(self):
    adapter = adapter_with_strategies("serial-isolated")
    strategy = select_coordination(load_review_workflow(), adapter)
    self.assertEqual(strategy.name, "serial-isolated")
    self.assertTrue(strategy.isolated)
    self.assertFalse(strategy.parallel)

def test_shared_context_cannot_satisfy_independent_review(self):
    adapter = adapter_with_strategies("single-context")
    self.assertIsNone(select_coordination(load_review_workflow(), adapter))
```

- [x] **Step 2: Run the adapter tests and verify failure**

Run: `python -m unittest discover -s tests -p "test_daodan_adapters.py" -v`

Expected: FAIL because the adapter module and TOML files are absent.

- [x] **Step 3: Add explicit capability and coordination bindings**

Capability bindings name host tool identifiers or runtime mechanisms. Coordination files order the strategies each harness can use. They must encode the Task 1 evidence rather than assumptions:

```toml
[capabilities."contexts.isolate"]
state = "adapted"
strategy = "runtime-subagent"

[[strategies]]
name = "parallel-subagents"
availability = "baseline"
isolated = true
parallel = true
shared_tasks = false
peer_messaging = false
role_delivery = "inline-prompt"

[[strategies]]
name = "serial-isolated"
availability = "baseline"
isolated = true
parallel = false
shared_tasks = false
peer_messaging = false
role_delivery = "inline-prompt"
```

Claude orders `native-team`, `parallel-subagents`, `serial-isolated`; `native-team` has `availability = "runtime-optional"` because Agent Teams can be disabled. Copilot orders `parallel-subagents`, then `serial-isolated`, and uses named custom-agent delivery. Codex uses the role-delivery result proven in Task 1. Do not add a `single-context` fallback.

- [x] **Step 4: Implement adapter loading and reports**

```python
@dataclass(frozen=True)
class CapabilityBinding:
    state: Literal["native", "adapted", "unsupported"]
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
```

The worst required capability state determines the plugin state. Optional capabilities select stronger strategies but never hide required failures. `select_coordination` filters out any strategy that violates `isolation`, `join` or required concurrency, then selects the first remaining strategy in host order. A preferred concurrency request can select `serial-isolated`; required concurrency cannot.

- [x] **Step 5: Run adapter and model tests**

Run: `python -m unittest discover -s tests -p "test_daodan_*.py" -v`

Expected: PASS with all abstract capabilities bound by all three adapters.

- [x] **Step 6: Commit adapter contracts**

```bash
git add scripts/daodan/adapter.py adapters tests/test_daodan_adapters.py
git commit -m "Define native host harness contracts"
```

### Task 5: Add fingerprinted semantic overrides

**Files:**
- Create: `scripts/daodan/overrides.py`
- Create: `tests/fixtures/daodan/overrides/copilot/example/review/override.toml`
- Create: `tests/fixtures/daodan/overrides/copilot/example/review/orchestrator.agent.md`
- Create: `tests/test_daodan_overrides.py`

**Interfaces:**
- Consumes: neutral source files and adapter override directories.
- Produces: `OverrideSpec`, `load_overrides(path: Path) -> tuple[OverrideSpec, ...]`, `source_digest(paths: Iterable[Path]) -> str`, and `validate_override(spec: OverrideSpec, declared_capabilities: AbstractSet[str]) -> list[ValidationIssue]`.

- [x] **Step 1: Write a failing stale-fingerprint test**

```python
def test_changed_source_marks_override_stale(self):
    spec = load_fixture_override(reviewed_against="sha256:deadbeef")
    issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
    self.assertEqual([issue.code for issue in issues], ["stale-override"])

def test_override_cannot_add_undeclared_capability(self):
    spec = load_fixture_override(capabilities_affected=("shell.execute",))
    issues = validate_override(spec, declared_capabilities=frozenset({"repository.read"}))
    self.assertEqual([issue.code for issue in issues], ["override-capability-escalation"])
```

- [x] **Step 2: Run the test and verify failure**

Run: `python -m unittest discover -s tests -p "test_daodan_overrides.py" -v`

Expected: FAIL because override loading is missing.

- [x] **Step 3: Implement canonical source fingerprints**

```python
@dataclass(frozen=True)
class OverrideSpec:
    root: Path
    source: str
    source_paths: tuple[Path, ...]
    reason: str
    strategy: str
    reviewed_against: str
    contracts_preserved: tuple[str, ...]
    capabilities_affected: tuple[str, ...]
    replacement: Path

def source_digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"
```

Require `source`, `reason`, `strategy`, `reviewed_against`, `contracts_preserved`, `capabilities_affected` and `replacement`. Reject replacements outside the override directory, contract names absent from the neutral workflow and affected capabilities absent from the owning plugin's declarations. An override can select a different declared mechanism, but cannot add a tool, MCP server, LSP server, hook or capability that the kernel did not declare.

- [x] **Step 4: Run override tests**

Run: `python -m unittest discover -s tests -p "test_daodan_overrides.py" -v`

Expected: PASS; the stale and capability-escalation fixtures produce the exact validation issues asserted by their tests.

- [x] **Step 5: Commit the override gate**

```bash
git add scripts/daodan/overrides.py tests/fixtures/daodan/overrides tests/test_daodan_overrides.py
git commit -m "Gate semantic adapter overrides"
```

### Task 6: Render deterministic packages and replace outputs transactionally

**Files:**
- Create: `scripts/daodan/render.py`
- Create: `scripts/daodan/provenance.py`
- Create: `scripts/daodan/templates.py`
- Create: `tests/test_daodan_render.py`

**Interfaces:**
- Consumes: `PluginSpec`, `HostAdapter`, validated overrides and destination path.
- Produces: `render_plugin(plugin, adapter, destination) -> RenderResult`, `write_provenance(result) -> Path`, and `replace_tree(staging: Path, live: Path) -> None`.

- [x] **Step 1: Write failing reproducibility and rollback tests**

```python
def test_equal_inputs_produce_equal_bytes(self):
    first = compile_fixture("claude")
    second = compile_fixture("claude")
    self.assertEqual(tree_digest(first), tree_digest(second))

def test_failed_validation_keeps_live_tree(self):
    live = self.temp / "live"
    (live / "sentinel").write_text("old", encoding="utf-8")
    with self.assertRaises(RenderError):
        compile_invalid_fixture(live)
    self.assertEqual((live / "sentinel").read_text(), "old")
```

- [x] **Step 2: Run render tests and verify failure**

Run: `python -m unittest discover -s tests -p "test_daodan_render.py" -v`

Expected: FAIL because renderer modules are absent.

- [x] **Step 3: Implement focused render stages**

Add the renderer boundary types:

```python
class RenderError(RuntimeError):
    """Raised before a generated tree becomes live."""

@dataclass(frozen=True)
class RenderResult:
    plugin: str
    host: str
    staging_root: Path
    files: tuple[Path, ...]
    core_digest: str
    harness_strategies: tuple[tuple[str, str], ...]
    overrides: tuple[str, ...]
```

Use `tempfile.TemporaryDirectory(dir=live.parent)`, copy binary resources byte-for-byte, normalize generated text to UTF-8 LF, render substitutions with an allowlisted `string.Template` context, and write JSON with `sort_keys=True, indent=2`. `replace_tree` acquires a sibling lock, recovers any prior `.previous` tree, renames `live` to `.previous`, renames the fully validated staging tree to `live`, restores `.previous` if the second rename fails, then removes the backup. It never modifies the live tree file-by-file.

- [x] **Step 4: Add provenance**

Write `.daodan-provenance.json` inside every generated plugin with exactly:

```json
{
  "adapterVersion": "1.0.0",
  "coreDigest": "sha256:<64 lowercase hex characters>",
  "host": "claude",
  "harnessStrategies": {"review": "parallel-subagents"},
  "overrides": [],
  "plugin": "example",
  "version": "1.2.3"
}
```

- [x] **Step 5: Run renderer tests twice**

Run: `python -m unittest discover -s tests -p "test_daodan_render.py" -v` twice.

Expected: PASS both times with identical tree digests.

- [x] **Step 6: Commit deterministic rendering**

```bash
git add scripts/daodan/render.py scripts/daodan/provenance.py scripts/daodan/templates.py tests/test_daodan_render.py
git commit -m "Render deterministic native plugin packages"
```

### Task 7: Generate native catalogs and expose the compiler CLI

**Files:**
- Create: `scripts/daodan/catalogs.py`
- Create: `scripts/daodan/report.py`
- Create: `scripts/daodan_build.py`
- Create: `tests/test_daodan_catalogs.py`
- Create: `tests/test_daodan_cli.py`
- Create: `adapters/claude/templates/plugin.json.tmpl`
- Create: `adapters/copilot/templates/plugin.json.tmpl`
- Create: `adapters/codex/templates/plugin.json.tmpl`

**Interfaces:**
- Consumes: all previous compiler interfaces.
- Produces: `BuildReport`, `build_repository(root: Path, hosts: tuple[str, ...], check: bool) -> BuildReport`, `render_catalog(host: str, plugins: Sequence[PluginSpec], version: str) -> bytes`, and CLI exit codes 0 clean, 1 drift or validation failure, 2 invocation error.

- [x] **Step 1: Write failing catalog identity tests**

```python
def test_catalogs_share_identity_names_and_versions(self):
    catalogs = build_fixture_catalogs()
    self.assertEqual({catalog["name"] for catalog in catalogs.values()}, {"daodan"})
    versions = {entry["name"]: entry["version"] for entry in catalogs["claude"]["plugins"]}
    for catalog in catalogs.values():
        self.assertEqual({entry["name"]: entry["version"] for entry in catalog["plugins"]}, versions)
```

- [x] **Step 2: Run tests and verify failure**

Run: `python -m unittest discover -s tests -p "test_daodan_catalogs.py" -v`

Expected: FAIL because catalog renderers are absent.

- [x] **Step 3: Implement three catalog renderers**

Generate Claude sources as `./exports/claude/plugins/<name>`, Copilot sources as `./exports/copilot/plugins/<name>`, and Codex source objects with `source = "local"` and `path = "./exports/codex/plugins/<name>"`. Sort entries by plugin name and reject version mismatch before serialization.

- [x] **Step 4: Implement the CLI**

```python
@dataclass(frozen=True)
class BuildReport:
    issues: tuple[ValidationIssue, ...] = ()
    drift: tuple[Path, ...] = ()

    @property
    def has_failures(self) -> bool:
        return bool(self.issues or self.drift)

    def write(self, stream: TextIO) -> None:
        for issue in self.issues:
            stream.write(f"{issue.code}: {issue.path}: {issue.message}\n")
        for path in self.drift:
            stream.write(f"generated-drift: {path}\n")

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", action="append", choices=("claude", "copilot", "codex"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    hosts = tuple(args.host or ("claude", "copilot", "codex"))
    report = build_repository(Path.cwd(), hosts, args.check)
    report.write(sys.stdout)
    return 1 if report.has_failures else 0
```

Reject publication mode when fewer than all three hosts are selected. Host-specific rendering is development-only.

- [x] **Step 5: Run all compiler tests**

Run: `python -m unittest discover -s tests -p "test_daodan_*.py" -v`

Expected: PASS.

- [x] **Step 6: Run the repository's existing unit suite**

Run: `python -m unittest discover -s tests -v`

Expected: PASS.

- [x] **Step 7: Commit the compiler entry point**

```bash
git add scripts/daodan scripts/daodan_build.py adapters/*/templates tests/test_daodan_catalogs.py tests/test_daodan_cli.py
git commit -m "Add universal Daodan compiler CLI"
```

## Milestone B: move distribution behind generated ports

### Task 8: Bootstrap the current Claude marketplace into `exports/claude`

**Files:**
- Create: `exports/claude/plugins/**`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `scripts/lint_plugin_registration.py`
- Modify: `scripts/check_version_bumps.py`
- Create: `tests/test_claude_bootstrap_parity.py`

**Interfaces:**
- Consumes: the current 40 directories under `plugins/` and marketplace entries.
- Produces: a byte-equivalent installable Claude catalog whose sources point to `exports/claude/plugins/<name>`.

- [x] **Step 1: Write a failing parity test before copying**

The test loads each current marketplace entry, resolves its registered agents, skills and commands, and asserts the same relative files and bytes exist under `exports/claude/plugins/<name>`.

```python
def test_bootstrap_export_matches_registered_components(self):
    for plugin in load_marketplace()["plugins"]:
        for component in registered_files(plugin):
            source = Path(plugin["source"]) / component
            exported = Path("exports/claude/plugins") / plugin["name"] / component
            self.assertEqual(exported.read_bytes(), source.read_bytes())
```

- [x] **Step 2: Run the parity test and verify missing exports**

Run: `python -m unittest discover -s tests -p "test_claude_bootstrap_parity.py" -v`

Expected: FAIL on `exports/claude/plugins/clean-code`.

- [x] **Step 3: Copy current plugin packages mechanically**

Copy all plugin content, excluding `__pycache__`, `.pyc`, `.pyo` and temporary artifacts. Do not neutralize content in this task. Add a native `.claude-plugin/plugin.json` derived from each current marketplace entry.

- [x] **Step 4: Point the existing Claude catalog at the export**

Change only each `source` to `./exports/claude/plugins/<name>`. Keep marketplace name, plugin names and versions unchanged in this bootstrap release.

- [x] **Step 5: Update legacy linters to follow marketplace sources**

Registration and version-bump checks must resolve the active Claude package through the marketplace source rather than assuming `plugins/<name>` is directly installable.

- [x] **Step 6: Run parity and all existing consistency checks**

```bash
python -m unittest discover -s tests -v
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_plugin_registration.py
python scripts/lint_fact_anchors.py
claude plugin validate .
```

Expected: all PASS and the marketplace still lists 40 plugins.

- [x] **Step 7: Commit the Claude bootstrap atomically**

```bash
git add exports/claude .claude-plugin/marketplace.json scripts/lint_plugin_registration.py scripts/check_version_bumps.py tests/test_claude_bootstrap_parity.py
git commit -m "Move Claude packages behind the generated export"
```

### Task 9: Migrate `dependency-audit` as the simple real canary

**Files:**
- Create: `plugins/dependency-audit/plugin.toml`
- Create: `plugins/dependency-audit/workflows/deps-audit.toml`
- Move: `plugins/dependency-audit/commands/deps-audit.md` to `plugins/dependency-audit/workflows/deps-audit.md`
- Keep: `plugins/dependency-audit/skills/dependency-audit/**`
- Create: host packages under `exports/{claude,copilot,codex}/plugins/dependency-audit/`
- Create: `evals/universal-daodan/dependency-audit.md`
- Test: `tests/test_dependency_audit_ports.py`

**Interfaces:**
- Consumes: compiler from Milestone A and the existing dependency-audit method.
- Produces: the first plugin compiled from neutral source with `deps-audit` contract parity on three hosts.

- [x] **Step 1: Write failing package parity assertions**

Assert all three manifests report the same name and version, all three packages contain the skill resources, and each host exposes one invocable audit workflow.

- [x] **Step 2: Run the canary test and verify neutral metadata is missing**

Run: `python -m unittest discover -s tests -p "test_dependency_audit_ports.py" -v`

Expected: FAIL because `plugin.toml` does not exist.

- [x] **Step 3: Write the neutral manifest and workflow contract**

The contract requires dependency discovery, direct-versus-transitive classification, license analysis, supply-chain findings with evidence, and one written report. Preserve the existing three reference files byte-for-byte.

- [x] **Step 4: Add only the host wrappers required by the canary**

Claude emits a skill plus invocable command-compatible workflow. Copilot emits a skill plus prompt entrypoint. Codex emits a skill whose instructions execute the workflow directly. No semantic override is expected for this single-context plugin.

- [ ] **Step 5: Build and run the canary eval** (build, `--check` and the port tests pass; the per-host install-and-run half is unmeasured, see `evals/universal-daodan/dependency-audit.md`)

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests -p "test_dependency_audit_ports.py" -v
```

Install the package from each disposable marketplace and run it against `tests/fixtures/daodan/dependency-project`. Record contract results in `evals/universal-daodan/dependency-audit.md`.

- [x] **Step 6: Commit the simple canary**

```bash
git add plugins/dependency-audit exports adapters evals/universal-daodan/dependency-audit.md tests/test_dependency_audit_ports.py
git commit -m "Compile dependency audit for three native hosts"
```

### Task 10: Migrate the complex review pipeline canary

**Files:**
- Create neutral manifests, roles and workflow TOML under:
  - `plugins/codebase-xray/`
  - `plugins/abstraction-architect/`
  - `plugins/repo-hygiene/`
  - `plugins/react-development/`
  - `plugins/platform-engineering/`
  - `plugins/typescript-development/`
  - `plugins/testing/`
  - `plugins/senior-review/`
- Create: `plugins/senior-review/workflows/team-review.toml`
- Move: `plugins/senior-review/commands/team-review.md` to `plugins/senior-review/workflows/team-review.md`
- Create: `plugins/senior-review/contracts/review-brief.toml`
- Create: `plugins/senior-review/contracts/reviewer-binding.toml`
- Create: `plugins/senior-review/contracts/reviewer-selection.toml`
- Create: `plugins/senior-review/contracts/evidenced-finding.toml`
- Create: `plugins/senior-review/contracts/reviewer-result.toml`
- Create: `plugins/senior-review/contracts/delivery-ledger.toml`
- Create: `plugins/senior-review/contracts/final-report.toml`
- Create: `plugins/codebase-xray/policies/write-confinement.toml`
- Create: `adapters/claude/templates/team-workflow.md.tmpl`
- Create: `adapters/copilot/templates/coordinator.agent.md.tmpl`
- Create: `adapters/copilot/templates/worker.agent.md.tmpl`
- Create: `adapters/copilot/policies/xray-guard/xray_guard.py`
- Create: `adapters/copilot/policies/xray-guard/test_xray_guard.py`
- Create: `adapters/codex/templates/subagent-workflow.SKILL.md.tmpl`
- Create: `evals/universal-daodan/team-review-contract.md`
- Create: `tests/test_review_pipeline_ports.py`

**Interfaces:**
- Consumes: the current eight-plugin review dependency cluster, `.deep-dive/` artifact contract, the Task 1 protocol evidence and the harness selector from Task 4.
- Produces: one content-kernel `team-review` DAG plus three generated host harnesses whose observable review contract is identical.

- [x] **Step 1: Write failing cross-host contract tests**

Write these concrete assertions:

```python
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

def test_every_host_preserves_team_review_contract(self):
    for host in ("claude", "copilot", "codex"):
        package = compiled_review_package(host)
        self.assertTrue(package.has_isolated_workers)
        self.assertTrue(package.has_delivery_barrier)
        self.assertTrue(package.has_cross_examination)
        self.assertTrue(package.has_consolidation)
        self.assertEqual(package.artifact_root("xray"), ".deep-dive")
```

- [x] **Step 2: Run the test and verify neutral workflow metadata is missing**

Run: `python -m unittest discover -s tests -p "test_review_pipeline_ports.py" -v`

Expected: FAIL on missing `plugins/codebase-xray/plugin.toml`.

- [x] **Step 3: Neutralize the dependency cluster one plugin per commit**

For each plugin, add `plugin.toml`, move agent bodies to `roles/`, move command bodies to `workflows/`, add one TOML sidecar per workflow, and preserve skill references, scripts and assets. Use this commit order so dependencies always point backward:

```text
repo-hygiene
react-development
platform-engineering
typescript-development
testing
codebase-xray
abstraction-architect
senior-review
```

After each plugin, run a normal build, then `python scripts/daodan_build.py --check` and its existing focused tests before committing. The normal build is required because `--check` must report drift until the new neutral source has generated all three ports.

For `codebase-xray`, express partition selection, isolated workers, artifact ownership and synthesis barriers in its own workflow contract. Once all three generated harnesses pass, remove its runtime dependency on `agent-teams@Codex-workflows`; scheduling now belongs to the host harness.

- [x] **Step 4: Encode the host-neutral review kernel**

Define this phase order in `team-review.toml`:

```text
scope -> context-building -> dimension-detection -> independent-review -> delivery-accounting -> initial-consolidation -> cross-examination -> consolidation -> report-delivery
```

`dimension-detection` applies the current signal table and produces `selection:reviewers`; its contract contains every supported dimension, owning role and activation evidence. `independent-review` uses `fanout_from = "selection:reviewers"`, `isolation = "required"`, `join = "all-delivered"` and `concurrency = "preferred"`. The harness must dispatch exactly the selected dimensions. `delivery-accounting` produces a ledger containing every expected role with state `delivered` or `failed`. `initial-consolidation` deduplicates delivered findings. `cross-examination` runs the premise and verification lenses in fresh contexts over that initial set. Only the final `review-consolidator` phase may write the final report artifact. Put field requirements such as file, line, evidence, severity, confidence and reviewer into the contract TOML files; keep dimension selection judgment, review judgment and role instructions in Markdown.

Remove `agent-teams@Codex-workflows` from the generated `senior-review` runtime dependencies once the three harness evals pass. Do not copy the upstream plugin into the kernel. The review-specific isolation, delivery, deduplication and verification rules belong to this workflow's own contracts; host team and subagent mechanics belong to the adapters.

Use these exact record contracts:

```toml
# review-brief.toml
schema = "daodan/record/v1"
name = "review-brief"
required = ["target", "scope_path", "context_paths", "output_path", "constraints"]
```

```toml
# reviewer-binding.toml
schema = "daodan/record/v1"
name = "reviewer-binding"
required = ["dimension", "role", "activation_evidence"]
```

```toml
# reviewer-selection.toml
schema = "daodan/record/v1"
name = "reviewer-selection"
required = ["dimensions"]
[fields.dimensions]
type = "array"
items = "contract:reviewer-binding"
```

```toml
# evidenced-finding.toml
schema = "daodan/record/v1"
name = "evidenced-finding"
required = ["file", "line", "evidence", "severity", "confidence", "premise", "premise_provenance"]
```

```toml
# reviewer-result.toml
schema = "daodan/record/v1"
name = "reviewer-result"
required = ["dimension", "reviewer", "status", "findings", "gaps", "output_path"]
[fields.status]
type = "enum"
values = ["delivered", "failed"]
[fields.findings]
type = "array"
items = "contract:evidenced-finding"
```

```toml
# delivery-ledger.toml
schema = "daodan/record/v1"
name = "delivery-ledger"
required = ["expected", "delivered", "failed", "barrier_satisfied"]
[fields.barrier_satisfied]
type = "boolean"
```

```toml
# final-report.toml
schema = "daodan/record/v1"
name = "final-report"
required = ["retained_findings", "filtered_findings", "coverage", "degraded_dimensions", "output_path"]
```

- [x] **Step 5: Generate each host's execution harness**

Generate the strongest strategy supported by each harness without editing the kernel:

- Claude renders a coordinator that selects native Agent Teams when enabled, otherwise isolated subagents. Both paths enforce the same ledger and barrier.
- Copilot renders one coordinator `.agent.md` with the `agent` tool and an explicit `agents` allowlist, plus one hidden custom agent per worker role. The coordinator requests parallel workers and can serialize them without changing the contract.
- Codex renders one workflow skill that starts isolated runtime subagents. Use packaged named roles only if Task 1 proved discovery; otherwise inject the exact role Markdown into each dispatch prompt.

Do not create semantic overrides merely because the topologies differ. Create an override only if a behavioral contract cannot be rendered from these generic harness templates. Move the current Copilot-only X-ray guard into the Copilot adapter as an implementation of the neutral write-confinement policy; do not treat its VS Code JSON vocabulary as core content.

- [ ] **Step 6: Run structural, contract, topology and guard tests** (all four commands pass, guard 36/36; the one-fixture-review-per-host half is unmeasured, see `evals/universal-daodan/team-review-contract.md`)

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests -p "test_review_pipeline_ports.py" -v
python adapters/copilot/policies/xray-guard/test_xray_guard.py
```

Run one fixture review on each host. The eval passes only when every worker uses an isolated context, each expected reviewer is marked delivered or failed, cross-examination occurs after the ledger barrier, all retained findings carry evidence, and the final report artifact exists. Record the actual selected topology for each host in `.daodan-provenance.json`; topology names may differ while contract assertions must match.

- [x] **Step 7: Commit the complex canary and parity evidence**

```bash
git add plugins adapters exports evals/universal-daodan/team-review-contract.md tests/test_review_pipeline_ports.py
git commit -m "Compile the review pipeline for three hosts"
```

## Milestone C: migrate the complete catalog

### Task 11: Migrate the remaining 31 plugins in reviewable families

**Files:**
- Modify: all remaining directories under `plugins/`
- Create: corresponding packages under `exports/{claude,copilot,codex}/plugins/`
- Create: semantic overrides only where the compiler reports a required host divergence
- Create: `evals/universal-daodan/catalog-parity.md`
- Create: `tests/test_universal_catalog_parity.py`

**Interfaces:**
- Consumes: the proven simple and complex patterns.
- Produces: exactly 40 core plugins and exactly 40 entries in each generated catalog, all `native` or `adapted`.

- [x] **Step 1: Add a failing complete-catalog test**

```python
def test_every_core_plugin_is_in_every_catalog(self):
    core = {path.parent.name for path in Path("plugins").glob("*/plugin.toml")}
    self.assertEqual(len(core), 40)
    for host in ("claude", "copilot", "codex"):
        self.assertEqual(catalog_names(host), core)
        self.assertNotIn("unsupported", parity_states(host))
```

- [x] **Step 2: Migrate the knowledge and utility family**

Migrate and commit each plugin independently in this order:

```text
docker, docs, text-humanizer, system-utils, learning, obsidian-development
```

For every plugin: add neutral TOML, move commands to workflows, move agents to roles, compile all hosts, run its focused eval, then commit before starting the next plugin.

- [x] **Step 3: Migrate the language and application tooling family**

```text
clean-code, tauri-development, xterm, python-development, stripe,
messaging, project-setup, csp, browser-extensions, rag-development,
trading-broker-integration, libgdx-development, kotlin-development,
opentelemetry, pwa-expert
```

Apply the same per-plugin cycle. Browser or MCP requirements must be declared as capabilities and never guessed as tool identifiers.

- [x] **Step 4: Migrate the multi-role and integration family**

```text
ai-tooling, research, business, app-analyzer, digital-marketing,
marketplace-ops, codebase-mapper, grabber-development, frontend-review,
peer-review
```

Keep Codex-as-subject vocabulary intact in `marketplace-ops` and `ai-tooling/agent-sdk-builder`. Preserve external marketplace dependencies as qualified dependencies in host-native form.

For `research` and `codebase-mapper`, migrate the local pipeline semantics into their own kernel contracts and remove `agent-teams@Codex-workflows` only after three-host contract evals pass. Preserve any external dependency that contributes actual knowledge or behavior rather than generic dispatch mechanics.

- [x] **Step 5: Run the complete parity gate**

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests -v
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_fact_anchors.py
```

Expected: 40 core plugins, 40 Claude packages, 40 Copilot packages, 40 Codex packages, zero unsupported required components, zero stale overrides.

- [x] **Step 6: Record catalog parity and commit the completed migration**

Write the compiler parity table and host smoke results to `evals/universal-daodan/catalog-parity.md`.

```bash
git add plugins adapters exports evals/universal-daodan tests/test_universal_catalog_parity.py
git commit -m "Complete the universal plugin catalog"
```

## Milestone D: replace CI and cut over

### Task 12: Replace the VS Code mirror with universal build gates

**Files:**
- Modify: `.github/workflows/consistency.yml`
- Replace: `.github/workflows/mirror-export.yml` with `.github/workflows/publish-marketplaces.yml`
- Modify: `scripts/check_version_bumps.py`
- Retire after replacement: `scripts/mirror_export.py`
- Retire after replacement: `.claude/skills/downstream-exports/scripts/check_export.py`
- Retire after replacement: `.claude/skills/downstream-exports/scripts/gen_extension_manifest.py`
- Create: `tests/test_publish_workflow_contract.py`

**Interfaces:**
- Consumes: `python scripts/daodan_build.py --check` and full compiler output.
- Produces: PR drift gate and one bot publication commit containing all host exports and catalogs.

- [x] **Step 1: Write a workflow contract test**

Parse workflow text and assert it invokes the universal check, stages all three exports and all three catalog paths, uses the bot-email identity guard, and never references `vsce`, `exports/vscode` or `gen_extension_manifest.py`.

- [x] **Step 2: Run the workflow test and verify it fails on current CI**

Run: `python -m unittest discover -s tests -p "test_publish_workflow_contract.py" -v`

Expected: FAIL because current workflows still package the VSIX.

- [x] **Step 3: Update consistency CI**

Set Python to `3.11`, keep existing neutral content linters that still apply, add `python scripts/daodan_build.py --check`, and remove the VSIX package job and extension-manifest checks.

- [x] **Step 4: Implement atomic publication workflow**

The workflow performs a full clean build, full unit and contract validation, then stages exactly:

```text
exports/claude/
exports/copilot/
exports/codex/
.claude-plugin/marketplace.json
.github/plugin/marketplace.json
.agents/plugins/marketplace.json
```

If the tree is unchanged, exit successfully. Otherwise create one bot commit named `Publish native Daodan marketplaces` and push. Run the final `--check` before the commit, not after it.

- [x] **Step 5: Update version-bump rules and remove superseded mirror code**

A change to neutral plugin content or an adapter override affecting that plugin must bump the common plugin version and marketplace version. Delete mirror and extension checks only after their universal replacements pass.

- [x] **Step 6: Run workflow, compiler and existing tests**

```bash
python -m unittest discover -s tests -v
python scripts/daodan_build.py --check
```

Expected: PASS and no workflow text references the VSIX.

- [x] **Step 7: Commit the CI replacement**

```bash
git add .github/workflows scripts tests/test_publish_workflow_contract.py
git commit -m "Publish three native marketplaces atomically"
```

### Task 13: Perform the universal cutover and remove the VSIX

**Files:**
- Create: `.github/plugin/marketplace.json`
- Create: `.agents/plugins/marketplace.json`
- Modify: `.claude-plugin/marketplace.json`
- Delete: `exports/vscode/`
- Delete: `.github/workflows/release-vscode.yml`
- Delete: `scripts/extension_release_notes.py`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md` only if it is tracked by the user before this task begins
- Modify: `.claude/skills/downstream-exports/SKILL.md`
- Modify: `.agents/skills/downstream-exports/SKILL.md` only if it is tracked by the user before this task begins
- Create: `docs/migration-from-claude-code-daodan.md`
- Create: `tests/test_cutover_identity.py`

**Interfaces:**
- Consumes: complete parity evidence and universal publication workflow.
- Produces: repository marketplace identity `daodan` on all hosts and no extension distribution path.

- [x] **Step 1: Write failing cutover identity tests**

Assert the three native root manifests exist, all declare `name = daodan`, all versions and plugin sets match, `exports/vscode` is absent, and no tracked workflow or script contains `vsce`, `vscode-v` or `release-vscode`.

- [x] **Step 2: Run the identity test and verify failure before cutover**

Run: `python -m unittest discover -s tests -p "test_cutover_identity.py" -v`

Expected: FAIL because the new root catalogs do not yet exist and VSIX files remain.

- [ ] **Step 3: Generate and install-test the three final catalogs** (generated and `--check` clean; the six disposable-profile installs are unmeasured)

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
claude plugin validate .
```

In disposable profiles, register the same local repository root with Claude, Copilot and Codex. Browse all 40 entries and install both canaries on each host. Do not continue unless all six installations and invocations pass.

- [x] **Step 4: Remove the complete VSIX surface**

Delete `exports/vscode/`, `release-vscode.yml`, `extension_release_notes.py`, extension packaging instructions, extension version and changelog obligations, and the skill-copy lifecycle. Keep historical GitHub Release assets untouched.

- [x] **Step 5: Write migration and rollback instructions**

Document the one-time sequence for each host: remove `claude-code-daodan`, uninstall any old VSIX, add `acaprino/daodan`, install selected plugins, start a fresh session and verify no duplicate plugin names remain. Document rollback as a Git revert followed by a new patch marketplace version; published versions are never reused and the repository name is never rolled back. State that future submissions to curated host directories reference an immutable release tag or SHA and are independent of repository-store publication.

- [x] **Step 6: Run the entire repository gate**

```bash
python scripts/daodan_build.py --check
python -m unittest discover -s tests -v
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_fact_anchors.py
```

Expected: all PASS, three catalogs with 40 identical plugin identities, no tracked VSIX files.

- [x] **Step 7: Commit the cutover before renaming the remote**

```bash
git add .claude-plugin/marketplace.json .github/plugin/marketplace.json .agents/plugins/marketplace.json exports/claude exports/copilot exports/codex README.md CLAUDE.md docs/migration-from-claude-code-daodan.md tests/test_cutover_identity.py
git add -u exports/vscode .github/workflows/release-vscode.yml scripts/extension_release_notes.py .claude/skills/downstream-exports/SKILL.md
git commit -m "Cut over to the universal Daodan marketplace"
```

Before committing, inspect `git status --short` and `git diff --cached --name-only`. The index may contain `.agents/plugins/marketplace.json`, but must not contain the user's existing `.agents/skills/` content or untracked `AGENTS.md`. Update tracked instruction files only; leave untracked instruction files untouched.

- [x] **Step 8: Manual GitHub rename gate** (renamed to `acaprino/daodan` via the API, remote updated, redirect verified)

The repository owner renames `acaprino/claude-code-daodan` to `acaprino/daodan` in GitHub settings. Then update the local remote and verify the redirect:

```bash
git remote set-url origin https://github.com/acaprino/daodan.git
git ls-remote origin HEAD
```

Expected: the new remote returns the cutover commit. Do not automate this external account-level action.

- [x] **Step 9: Push and observe publication** (pushed; consistency and publish-marketplaces both green, publication reported no drift)

```bash
git push origin master
```

Wait for consistency and `publish-marketplaces` to complete. Verify the bot either reports no drift or produces one all-host publication commit. Re-run the three repository registration smoke tests against `acaprino/daodan`.

- [x] **Step 10: Record final release evidence**

Append the final commit, marketplace version, three marketplace browse results and six canary install results to `evals/universal-daodan/catalog-parity.md`, then commit that evidence:

```bash
git add evals/universal-daodan/catalog-parity.md
git commit -m "Record universal marketplace release evidence"
git push origin master
```

## Final acceptance gate

- [x] `plugins/*/plugin.toml` count is exactly 40.
- [x] Each native catalog contains exactly the same 40 names and versions.
- [x] Every package has the correct host-native manifest.
- [x] Every required component is `native` or `adapted`; none is `unsupported`.
- [ ] `team-review` selects the same review dimensions on all hosts, runs every selected role in an isolated context, accounts for every delivery and performs cross-examination before the final report.
- [x] Harness provenance records Claude, Copilot and Codex coordination strategies without leaking host dispatch APIs into the core.
- [x] All committed exports reproduce byte-for-byte with `python scripts/daodan_build.py --check`.
- [x] Claude Code and Codex register it from the repository root and install from it; Copilot recognizes all 40 packages but its behavioural check needs an OAuth or fine-grained token.
- [ ] `dependency-audit` and `senior-review` install and satisfy their contracts on all three hosts.
- [x] No tracked file under `exports/vscode/` or VSIX release workflow remains.
- [x] Historical VSIX GitHub Release assets remain untouched and are documented as unsupported (`docs/migration-from-claude-code-daodan.md`).
- [x] Marketplace identity `daodan` is stable after cutover.
