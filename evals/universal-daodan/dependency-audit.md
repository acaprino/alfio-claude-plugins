# Canary eval: `dependency-audit` on three hosts

`dependency-audit` is the simple canary of the universal marketplace: one skill, one workflow, one
context, no fan-out and no semantic override. It is what proves the compiler produces three
installable packages with one identity and one observable contract, before the review pipeline is
attempted.

## What is asserted mechanically

`tests/test_dependency_audit_ports.py` runs in the normal suite and asserts:

- all three manifests report `dependency-audit` at the same version as the kernel
- all three packages carry the four skill resources byte-for-byte
- each host exposes exactly one invocable audit workflow, at its native path:
  `commands/deps-audit.md` (Claude), `prompts/deps-audit.prompt.md` (Copilot),
  `skills/deps-audit/SKILL.md` (Codex)
- the kernel declares the audit contract outcomes and the single report artifact
- no host needed a semantic override (`overrides: []` in every provenance file)

Rebuild and verify with:

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests -p "test_dependency_audit_ports.py" -v
```

## Contract results

The behavioural half requires installing the package from each disposable marketplace and running the
audit against a fixture project. That means driving real Claude Code, Copilot and Codex sessions,
which is the same manual step the host protocol probes need.

| host | package installs | workflow invocable | dependencies discovered | direct/transitive classified | licenses analyzed | supply-chain evidenced | report written | remediation non-destructive |
|---|---|---|---|---|---|---|---|---|
| claude | yes | yes | 5 | yes | yes | yes | yes | yes |
| copilot | recognized | not run | - | - | - | - | - | - |
| codex | yes | yes | 5 | yes | yes | yes | yes | yes |

Both measured hosts ran against `tests/fixtures/daodan/dependency-project`, a two-ecosystem fixture
(npm and pip) pinned to deliberately old versions and never installed, and both closed with

```text
CONTRACT: discovered=5 classified=yes licenses=yes supplychain=yes report=yes destructive=no
```

Claude ran the package with `--plugin-dir`; Codex installed it from the generated catalog
(`codex plugin marketplace add ./`, `codex plugin add dependency-audit@daodan`) and the disposable
registration was removed afterwards. Both honoured the plugin's own directives: evidence tiers on
every claim, coverage gaps stated rather than papered over, and no manifest or lockfile touched.

Copilot is recognized by `copilot plugin list --plugin-dir` but not run, for the token reason
recorded in `tests/host-probes/README.md`.

**Running this found a defect the design had specified wrongly.** The Codex catalog entry was
specified as `{"source": "local", "path": "./exports/codex/plugins/<name>"}`. Codex registers such a
marketplace and then reports every plugin in it as `not found`; it takes a repository-relative path
string in `source`, exactly like the other two hosts. `catalogs.py` now emits that, and the catalog
test pins it with the reason.
