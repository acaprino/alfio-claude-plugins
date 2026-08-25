# Catalog parity: 40 plugins, three hosts

Every plugin under `plugins/` is a neutral content kernel, and every host catalog lists all 40 at the
same version. This file records the compiler's parity table and the host smoke results.

## Compiler parity

Produced by `python scripts/daodan_build.py --check --support`. `native` means the host binds every
required capability directly; `adapted` means at least one is satisfied through a host mechanism the
adapter names. No plugin is `unsupported` on any host, which is the release gate.

| plugin | version | claude | copilot | codex |
|---|---|---|---|---|
| `abstraction-architect` | 2.0.2 | native | native | adapted |
| `ai-tooling` | 5.0.2 | native | native | adapted |
| `app-analyzer` | 1.1.2 | native | native | adapted |
| `browser-extensions` | 1.7.5 | native | native | adapted |
| `business` | 1.10.2 | native | native | adapted |
| `clean-code` | 1.2.0 | native | native | adapted |
| `codebase-mapper` | 3.0.0 | native | native | adapted |
| `codebase-xray` | 2.2.1 | native | native | adapted |
| `csp` | 1.3.4 | native | native | adapted |
| `dependency-audit` | 1.0.2 | native | native | native |
| `digital-marketing` | 2.0.2 | native | native | adapted |
| `docker` | 1.3.2 | native | native | native |
| `docs` | 1.1.4 | native | native | native |
| `frontend-review` | 2.0.0 | native | native | native |
| `grabber-development` | 1.4.2 | native | native | adapted |
| `kotlin-development` | 1.0.3 | native | native | native |
| `learning` | 1.6.4 | native | native | native |
| `libgdx-development` | 1.0.6 | native | native | adapted |
| `marketplace-ops` | 2.2.0 | native | native | adapted |
| `messaging` | 2.0.1 | native | native | adapted |
| `obsidian-development` | 1.4.2 | native | native | native |
| `opentelemetry` | 1.3.5 | native | native | adapted |
| `peer-review` | 2.1.0 | native | native | adapted |
| `platform-engineering` | 1.2.9 | native | native | adapted |
| `project-setup` | 1.19.0 | native | native | adapted |
| `pwa-expert` | 1.1.2 | native | native | adapted |
| `python-development` | 1.21.8 | native | native | adapted |
| `rag-development` | 1.5.5 | native | native | adapted |
| `react-development` | 1.10.1 | native | native | adapted |
| `repo-hygiene` | 1.0.0 | native | native | adapted |
| `research` | 6.1.0 | native | native | adapted |
| `senior-review` | 11.0.0 | native | native | adapted |
| `stripe` | 2.4.5 | native | native | adapted |
| `system-utils` | 2.0.2 | native | native | native |
| `tauri-development` | 2.7.5 | native | native | adapted |
| `testing` | 2.2.1 | native | native | adapted |
| `text-humanizer` | 1.0.1 | native | native | adapted |
| `trading-broker-integration` | 2.0.0 | native | native | adapted |
| `typescript-development` | 2.2.2 | native | native | adapted |
| `xterm` | 1.1.2 | native | native | native |

Codex reads `adapted` for 31 plugins because its context isolation, role delivery and parallel
dispatch are runtime-subagent mechanisms rather than packaged primitives. That is a binding
difference, not a capability gap: the contract assertions in `tests/test_review_pipeline_ports.py`
and `tests/test_dependency_audit_ports.py` hold identically on all three hosts.

## Gates that must stay green

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_plugin_registration.py
python scripts/lint_fact_anchors.py
```

Result at the completed migration: 40 kernels, 40 Claude packages, 40 Copilot packages, 40 Codex
packages, zero unsupported required components, zero stale overrides, and in fact zero overrides at
all. Every host divergence so far was expressible through the generic harness templates, which is the
outcome the override gate exists to make visible rather than to encourage.

## Host smoke results

| host | catalog adds | plugin installs | workflow invocable | skill loads | role dispatch |
|---|---|---|---|---|---|
| claude | yes | yes | yes | yes | yes (isolated, parallel) |
| copilot | not run | structural: 40/40 recognized | not run | not run | not run |
| codex | yes | yes | yes | yes | yes (isolated, parallel, inline delivery) |

Claude and Codex are measured end to end; see `tests/host-probes/README.md` for the commands and the
raw results. `claude plugin marketplace add ./` then `claude plugin install clean-code@daodan`
installs and enables; `codex plugin marketplace add` lists the plugin from the generated
`.agents/plugins/marketplace.json` and `codex plugin add` installs it. `claude plugin validate .`
passes with zero warnings.

Copilot is measured structurally only: all 40 generated packages are recognized by
`copilot plugin list --plugin-dir`, but the behavioural half needs an OAuth token or a fine-grained
PAT that the classic `gh` token cannot stand in for.

## Release evidence

- Repository renamed to `acaprino/daodan`; the old name redirects.
- Marketplace identity `daodan` at version 26.0.0, 40 plugins, identical across all three catalogs.
- `consistency` and `publish-marketplaces` both green on the cutover head, and the publication job
  reported no drift, so the bot loop converged instead of republishing.

Three defects were found by running the hosts and CI rather than by reasoning about them, all fixed:

1. `strict: false` beside component arrays makes a plugin fail to load ("conflicting manifests").
2. Generated `plugin.json` files carried no `author`, which `claude plugin validate .` warned about
   40 times.
3. The kernel digest hashed absolute paths and raw bytes, so the same source hashed differently on a
   Windows checkout and a Linux runner, and CI reported drift against an identical tree. Deciding
   text by file extension then left four plugins still drifting, because the helper scripts they ship
   fell outside the whitelist. The renderer now asks the content whether it is text.
