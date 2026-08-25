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
| claude | TODO | TODO | TODO | TODO | TODO |
| copilot | TODO | TODO | TODO | TODO | TODO |
| codex | TODO | TODO | TODO | TODO | TODO |

**Not yet measured.** Like the host protocol probes and the two canary evals, this half needs real
host sessions. Until it is filled in, the parity claim above is a claim about what the compiler
produces, not about what each host does with it.
