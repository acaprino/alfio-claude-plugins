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
| claude | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| copilot | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| codex | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

**Not yet measured.** Fill this in alongside the evidence table in `tests/host-probes/README.md`. A
row that fails any contract column blocks the complete release for that host, since the release
baseline requires one identical semantic version everywhere.
