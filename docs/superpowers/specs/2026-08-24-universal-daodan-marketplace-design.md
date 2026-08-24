# Daodan universal marketplace: neutral core and three native ports

**Date**: 2026-08-24
**Repository**: `acaprino/claude-code-daodan`, renamed to `acaprino/daodan` at cutover
**Status**: design approved in session, spec pending user review

## 1. Goal

Turn this repository into one marketplace that Claude Code, GitHub Copilot and Codex each recognize natively from the repository root. The repository will hold one host-neutral definition of every plugin, three peer adapters, and three generated installable catalogs. No host is the source for another host.

The target is not a lowest-common-denominator bundle. Every published plugin must preserve one observable behavioral contract on all three hosts. A host may use a different mechanism, but a missing required capability blocks the release.

The current repository is the migration source:

- `.claude-plugin/marketplace.json` registers 40 Claude Code plugins;
- `plugins/` currently contains Claude-specific agents, skills and commands;
- `exports/vscode/` contains the adapted Copilot bundles and the VS Code extension layer;
- Codex currently consumes selected plugins through compatibility conversion rather than a native repository catalog.

The final repository is named `daodan`. Its marketplace identity is also `daodan` on all three hosts.

## 2. Success criteria

The design is complete when all of the following hold:

1. The same Git repository can be registered by repository shorthand on Claude Code, Copilot and Codex.
2. The root contains all three native marketplace entry points at the same commit.
3. Every core plugin produces one native installable package per host.
4. Plugin names and versions are identical across the three catalogs.
5. Every required behavioral contract passes on all three hosts.
6. All generated output is reproducible from `plugins/` and `adapters/`.
7. No file under `exports/` is a hand-maintained source of truth.
8. A failed host build publishes nothing for any host.
9. Copilot distribution uses native agent plugins only. The VSIX and its release workflow are removed.
10. Existing historical VSIX releases remain available as unsupported historical artifacts; they are not deleted.

## 3. Non-goals

- One physical plugin directory shared unchanged by all hosts.
- Limiting every plugin to the intersection of the three host feature sets.
- A general-purpose agent programming language.
- Automatic publication into Anthropic, GitHub or OpenAI curated public directories. Those remain separate reviewed channels.
- Plugin support inside a host surface that does not support that host's plugin system.
- Preserving the old marketplace identifier `claude-code-daodan` after the cutover.
- Automatically uninstalling the historical VSIX from user machines.

## 4. Architectural principles

### 4.1 Meaning, translation, product

The repository has three ownership layers:

```text
plugins/   = host-neutral meaning and behavioral contracts
adapters/  = host-specific translation and explicit semantic overrides
exports/   = generated installable products
```

Only `plugins/` and `adapters/` are edited by maintainers. `exports/` and the three root marketplace manifests are generated, committed artifacts.

### 4.2 Peer hosts

Claude, Copilot and Codex are peers. The compiler does not convert Claude content to the other formats. It compiles the neutral core independently through each host adapter.

### 4.3 Readable core

Host-neutral prose uses natural instructions such as "search the repository". It does not contain template expressions such as `{{SEARCH_TOOL}}`. Abstract capabilities occur in TOML control-plane files, not throughout Markdown bodies.

### 4.4 Explicit divergence

Mechanical differences belong in shared host mappings and templates. Behavioral differences belong in named overrides with a reason, a strategy, preserved contracts and a fingerprint of the neutral source reviewed by the override author.

### 4.5 No silent degradation

An adapter either preserves the required contract or fails. Optional behavior must be declared optional in the core. A missing plugin, agent, tool or workflow phase cannot be converted into an undocumented skip.

## 5. Target repository structure

```text
daodan/
├── .claude-plugin/
│   └── marketplace.json
├── .github/
│   ├── plugin/
│   │   └── marketplace.json
│   └── workflows/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── plugins/
│   └── senior-review/
│       ├── plugin.toml
│       ├── skills/
│       ├── roles/
│       ├── workflows/
│       ├── policies/
│       ├── references/
│       ├── scripts/
│       ├── assets/
│       └── evals/
├── adapters/
│   ├── claude/
│   │   ├── capabilities.toml
│   │   ├── layout.toml
│   │   ├── templates/
│   │   └── overrides/
│   ├── copilot/
│   │   ├── capabilities.toml
│   │   ├── layout.toml
│   │   ├── templates/
│   │   └── overrides/
│   └── codex/
│       ├── capabilities.toml
│       ├── layout.toml
│       ├── templates/
│       └── overrides/
├── exports/
│   ├── claude/plugins/
│   ├── copilot/plugins/
│   └── codex/plugins/
└── scripts/
    └── daodan_build.py
```

TOML is the machine-readable source format because Python 3.11 and later provide `tomllib` in the standard library. Templates use a repository-owned, deliberately small substitution layer built on the Python standard library. They do not require Jinja or another template package.

## 6. Neutral plugin model

The core has four primitives.

| Primitive | Purpose | Typical Claude output | Typical Copilot output | Typical Codex output |
|---|---|---|---|---|
| `skill` | Method, knowledge and supporting resources | skill | skill | skill |
| `role` | A specialized responsibility | agent | custom agent | subagent or specialized skill |
| `workflow` | Ordered or concurrent coordination | command plus agents | prompt plus orchestrator | skill plus subagent workflow |
| `policy` | Deterministic rule or lifecycle gate | hook | hook | hook or runtime rule |

### 6.1 Plugin manifest

`plugins/senior-review/plugin.toml` illustrates the neutral manifest:

```toml
schema = "daodan/v1"
name = "senior-review"
version = "12.0.0"
description = "Multi-dimensional evidence-first code review"
license = "MIT"

capabilities = [
  "repository.read",
  "repository.search",
  "repository.history",
  "shell.execute",
  "agents.dispatch",
]

[dependencies]
required = ["codebase-xray", "abstraction-architect", "testing"]
optional = []

[components]
skills = ["defect-taxonomy", "review-quality-gates"]
roles = ["code-auditor", "security-auditor", "premise-auditor"]
workflows = ["code-review", "team-review"]
policies = ["review-write-boundary"]
```

The neutral dependency policy remains strict. Dependencies on plugins in this marketplace are required. A genuinely optional component is modeled as an optional capability or workflow dimension, not as an optional local installation.

### 6.2 Workflow control plane

Workflow TOML describes only orchestration. Rich instructions remain in Markdown.

```toml
name = "team-review"
entrypoint = "team-review.md"

[[phases]]
id = "context"
invoke = "workflow:codebase-xray"
produces = ["artifact:interconnect-map"]

[[phases]]
id = "review"
needs = ["context"]
parallel = [
  "role:code-auditor",
  "role:security-auditor",
  "role:premise-auditor",
]
consumes = ["artifact:interconnect-map"]

[[phases]]
id = "consolidation"
needs = ["review"]
role = "review-consolidator"
produces = ["artifact:review-report"]
```

The control plane can express:

- inputs and flags;
- phase dependencies;
- required and optional concurrency;
- invoked roles and workflows;
- artifacts produced and consumed;
- gates and policies;
- handoffs;
- the completion contract.

It does not contain arbitrary expressions, embedded programs or long prompts.

### 6.3 Capability registry

The initial closed vocabulary is:

```text
repository.read
repository.search
repository.edit
repository.history
shell.execute
web.fetch
web.search
user.ask
agents.dispatch
tasks.track
```

Adding a capability changes the neutral schema and requires a mapping or an explicit unsupported result in every adapter. The compiler rejects unknown capabilities.

### 6.4 Behavioral contracts

Each workflow declares observable outcomes and artifacts. For example:

```toml
[contract]
inputs = ["repository", "review-target"]
outcomes = [
  "findings-have-file-line-evidence",
  "findings-are-deduplicated",
  "every-review-dimension-is-accounted-for",
  "final-report-is-written",
]
artifacts = ["team-review-report"]
```

Adapters may change the mechanism only when these contracts remain true.

## 7. Host adapters

Each adapter owns four concerns:

1. capability mapping;
2. filesystem layout;
3. manifest and frontmatter rendering;
4. semantic overrides.

Mechanical mappings cover tool identifiers, path variables, namespaces, manifest fields, component locations and host invocation syntax.

### 7.1 Overrides

An override is a source artifact, not an edit to generated output:

```toml
source = "workflows/team-review"
reason = "Copilot prompts cannot declare a subagent allowlist"
strategy = "export-specific-orchestrator"
reviewed_against = "sha256:<digest>"
contracts_preserved = [
  "every-review-dimension-is-accounted-for",
  "final-report-is-written",
]
replacement = "orchestrator.agent.md"
```

If any neutral input covered by the fingerprint changes, `--check` reports the override as stale. Updating the digest without reviewing the replacement is a process violation. Contract evals provide the mechanical backstop.

### 7.2 Portability states

Every component receives one state per host:

| State | Meaning | Publishable |
|---|---|---|
| `native` | The host directly supplies the required mechanism | yes |
| `adapted` | A different mechanism preserves the observable contract | yes |
| `unsupported` | The required contract cannot be preserved | no |

Sequential execution can replace parallel execution only when parallelism and context isolation are not contract requirements. A workflow that promises epistemically independent reviewers cannot collapse them into one context.

## 8. Compiler

`scripts/daodan_build.py` is a standard-library Python compiler with these interfaces:

```text
python scripts/daodan_build.py
python scripts/daodan_build.py --host claude
python scripts/daodan_build.py --host copilot
python scripts/daodan_build.py --host codex
python scripts/daodan_build.py --check
```

### 8.1 Build pipeline

1. Parse all core TOML.
2. Validate schemas, component references and the dependency graph.
3. Resolve capability requirements.
4. Load the selected host adapter.
5. Validate and apply semantic overrides.
6. Render into a temporary directory outside the live export tree.
7. Run native structural validation on every selected host output.
8. Generate provenance manifests and marketplace catalogs.
9. Compare the complete staging tree with committed output in check mode.
10. Replace the live export tree only after every selected host passes.

A full build is the release operation. Host-specific builds exist for development speed and cannot publish a release.

### 8.2 Reproducibility

Generated output has:

- stable ordering;
- canonical JSON formatting;
- normalized line endings;
- no timestamps or machine-specific paths;
- no environment-dependent content;
- one provenance manifest per plugin and host.

The provenance manifest records plugin, host, plugin version, core digest, adapter version and applied overrides. Equal inputs must produce byte-identical output.

### 8.3 Failure behavior

- Parse or schema error: stop before rendering.
- Missing capability mapping: mark the component unsupported and fail the full build.
- Stale override: fail before output replacement.
- Host validator failure: retain the prior committed exports unchanged.
- More than one plugin with the same name: fail the catalog build.
- Name or version mismatch between a package and its catalog entry: fail.
- Partial filesystem replacement: use a staging directory and rename operation so it cannot expose a half-written host tree.

The compiler never repairs hand-authored core or adapter inputs silently.

## 9. Three native marketplace identities

All three manifests are present and committed at the repository root.

| Host | Repository manifest | Per-plugin manifest | Plugin source |
|---|---|---|---|
| Claude Code | `.claude-plugin/marketplace.json` | `.claude-plugin/plugin.json` | `./exports/claude/plugins/<name>` |
| GitHub Copilot | `.github/plugin/marketplace.json` | `plugin.json` | `./exports/copilot/plugins/<name>` |
| Codex | `.agents/plugins/marketplace.json` | `.codex-plugin/plugin.json` | `./exports/codex/plugins/<name>` |

Each catalog declares marketplace name `daodan`, owner `Alfio`, the same marketplace version and a host-appropriate description. Each catalog entry points only at its host's export.

Users register the same repository:

```text
claude plugin marketplace add acaprino/daodan
copilot plugin marketplace add acaprino/daodan
codex plugin marketplace add acaprino/daodan
```

Codex users install from the plugin browser after registration. The exact installation UI can differ by supported Codex surface; the repository identity and catalog remain the same.

## 10. Versioning and parity

### 10.1 One plugin version

A plugin has one version across all hosts. An adapter-only change that affects a plugin bumps that plugin's neutral version and therefore all three packages. This avoids host-specific version matrices.

### 10.2 One marketplace version

The three catalogs share one marketplace version. Any release that changes at least one plugin, one catalog or one adapter increments it. The universal cutover uses the next unused major marketplace version at the time it is released.

### 10.3 Strict release parity

Every core plugin must compile for every host. Each required component must be `native` or `adapted`. One `unsupported` result blocks the complete repository release. Catalogs cannot omit a failing plugin to make a release pass.

Host-specific enhancements are allowed when they do not alter the common contract or become hidden prerequisites.

## 11. CI and publication

### 11.1 Pull requests

CI builds all three hosts in a temporary directory, validates them, compares them with committed generated artifacts, runs contract evals and fails on drift. A correct pull request includes relevant core or adapter sources plus regenerated outputs.

### 11.2 Direct pushes to `master`

The publication workflow performs a clean full build. If outputs are already current, it is a no-op. If a permitted direct push left generated drift, the workflow validates the complete staged result and creates one bot commit containing all three host exports and all three catalogs. It never commits one host independently.

The bot-identity recursion guard remains identity-based. Generated bot commits are validated inside the publication workflow before push because a `GITHUB_TOKEN` push may not start the ordinary consistency workflow.

### 11.3 Repository store versus curated directories

The Git repository is the canonical, immediately installable store. Submission to Anthropic's official marketplace, GitHub's curated marketplaces or OpenAI's universal public Plugins Directory is a separate release lane with external review. Those listings reference approved immutable releases and may lag the repository store.

## 12. Migration

Migration is additive on `master` until the final cutover.

### 12.1 Phase 1: free the core path

Copy the current Claude packages faithfully to `exports/claude/plugins/`, validate installation, then point the existing Claude marketplace at those exports without changing marketplace identity. This makes root `plugins/` available for neutralization while current users continue to receive the existing Claude behavior.

### 12.2 Phase 2: compiler canaries

Migrate two canaries before designing for the remaining catalog:

1. one simple plugin with a skill and one entry workflow;
2. `senior-review` and its pipeline dependencies, exercising roles, artifacts, concurrency, policies, handoffs and semantic overrides.

The compiler architecture is accepted only when both extremes compile and pass their host contract evals.

### 12.3 Phase 3: plugin families

Migrate the remaining plugins by behavior:

1. knowledge-only;
2. single-role;
3. language and tooling;
4. browser and MCP;
5. multi-role;
6. pipeline.

Until every core plugin reaches parity, the Copilot and Codex catalogs are generated only into CI staging artifacts outside `.github/plugin/` and `.agents/plugins/`. Their native root entry points are created only by the universal cutover commit.

### 12.4 Phase 4: universal cutover

When all plugins pass all host gates:

1. rename the GitHub repository to `acaprino/daodan`;
2. change the marketplace identity to `daodan` in all three catalogs;
3. publish the three root entry points together;
4. publish migration instructions for existing `claude-code-daodan` users;
5. remove all VSIX-specific files and workflows;
6. mark historical VSIX releases unsupported without deleting them.

Changing the marketplace `name` means existing installations do not migrate merely because GitHub redirects the renamed repository. Users must remove the old marketplace, add `acaprino/daodan`, reinstall selected plugins and remove duplicates.

### 12.5 No VSIX compatibility channel

The final architecture removes:

- `exports/vscode/package.json`;
- `extension.js` and `uninstall.js`;
- `.vscodeignore` and VSIX packaging;
- the generated `chatAgents` and `chatPromptFiles` extension manifest;
- `release-vscode.yml`;
- the skill-copy layer under `~/.copilot/skills/`;
- extension-specific versioning and changelog obligations.

Useful adapted bundle content moves into `exports/copilot/plugins/`. Copilot CLI and VS Code consume the native marketplace. Existing VSIX users receive manual uninstall and migration instructions; the repository performs no remote or automatic uninstall.

## 13. Verification

### 13.1 Neutral checks

- TOML parses with `tomllib`.
- Names are stable kebab-case identifiers.
- Component references resolve.
- Artifact producers and consumers match.
- Phase graphs are acyclic.
- Required local dependencies are used and declared.
- Capability names exist in the closed registry.
- Every required capability has three mappings.

### 13.2 Host checks

Claude:

- run the native marketplace validator;
- validate every package manifest, frontmatter, hook and source path;
- install a simple canary and the complex pipeline canary.

Copilot:

- validate `.github/plugin/marketplace.json` and every root `plugin.json`;
- validate agent, skill, hook, MCP and LSP layouts where present;
- browse and install from the repository in Copilot CLI;
- discover and run the same installed plugin in VS Code;
- install the two canaries without any VSIX.

Codex:

- validate `.agents/plugins/marketplace.json` and every `.codex-plugin/plugin.json`;
- browse the repository marketplace in a supported Codex surface;
- install the two canaries;
- verify skills, hooks, MCP connections and subagent behavior used by their contracts.

### 13.3 Cross-host contract evals

Every workflow contract has host-independent assertions and host fixtures. Assertions target outcomes, artifacts and safety properties, not exact wording or exact internal tool order. The compiler emits a parity report that lists `native`, `adapted` or `unsupported` for each component.

### 13.4 Catalog identity gate

From a clean clone, CI checks:

- all three root marketplace paths exist;
- all three declare marketplace name `daodan` after cutover;
- names and versions match across catalogs;
- every source path stays within the repository and exists;
- every listed package has its host-native manifest;
- every core plugin appears exactly once in every catalog;
- no generated artifact contains an absolute local path.

## 14. Security and trust

- Generated hooks preserve the host's trust and approval model.
- A plugin cannot add an undeclared tool, MCP server, LSP server or hook through an override.
- Override metadata lists the contracts and capabilities it affects.
- Source paths cannot escape the repository root.
- Git-backed public submissions reference immutable tags or SHAs where the target directory requires them.
- Install documentation warns that marketplace plugins can execute code and should be reviewed before trust is granted.
- Secret scanning and forbidden-path checks run over core, adapters and generated packages.

## 15. Rollback

Before cutover, rollback means restoring the prior generated export commit; the existing Claude marketplace remains the public channel. After cutover, a failed release is rolled back by reverting the single generated release commit and publishing the next patch version. Published semantic versions are never reused.

The repository rename does not serve as the rollback mechanism. Once the `daodan` marketplace identity is public, it remains stable.

## 16. Decisions fixed by this design

1. One repository, one neutral core, three native peer ports.
2. `plugins/` means behavior; `adapters/` means translation; `exports/` means installable output.
3. Neutral control-plane files use TOML.
4. Markdown remains the source for rich instructions and knowledge.
5. Four primitives: skill, role, workflow and policy.
6. Workflow TOML is limited to orchestration and contracts.
7. Generated exports are committed but never hand-edited.
8. Semantic differences live in fingerprinted adapter overrides.
9. Marketplace and plugin versions remain synchronized across hosts.
10. Strict parity blocks every release that cannot preserve a required contract on all hosts.
11. The repository root always carries all three native marketplace manifests after cutover.
12. Marketplace identity is `daodan` on all three hosts.
13. Publication of all repository catalogs is atomic.
14. Curated public directories remain separate reviewed channels.
15. The VSIX is removed completely at cutover, with no compatibility release.

## 17. Implementation boundary

This specification defines the target architecture and migration invariants. The implementation plan must decompose the work into independently verifiable stages. It must not begin by moving all 40 plugins. The first executable milestone is the neutral schema, compiler skeleton and the two canaries while the current Claude marketplace remains operational.
