# Native host protocol probes

Three disposable single-plugin marketplaces, one per host, that establish what each native harness
actually supports. They exist so that the adapter capability and coordination bindings in
`adapters/<host>/` encode measured behaviour instead of assumptions. They are fixtures: nothing here
ships, and every disposable marketplace is removed from the host profile after the probe.

Each fixture packages the same probe plugin (`daodan-probe`, version `0.0.1`, source `./plugins/probe`):

- a **single-worker** skill whose entire output contract is `Return exactly DAODAN_PROBE_OK.`
- a **two-worker coordination** entry point that dispatches two workers with nonces `alpha` and `beta`,
  requires isolated worker contexts, asks for parallel execution when available, waits for both
  deliveries and returns `DELIVERED=2/2`.

Per-host specifics:

| host | coordination entry point | role delivery under test |
|---|---|---|
| claude | `commands/probe-team.md` | packaged agent, plus native Agent Teams versus plain isolated subagents |
| copilot | `agents/probe-coordinator.agent.md` | named custom agent, restricted by the `agents` frontmatter allowlist |
| codex | `skills/probe/SKILL.md` | packaged `.codex/agents/probe.toml` role, with inline role body as the fallback |

## Structural check

```bash
python scripts/probe_host_marketplaces.py
python -m unittest discover -s tests -p "test_host_probe_fixtures.py" -v
```

## Native smoke probes

Run these in disposable host profiles, browse and install `daodan-probe`, start a fresh session, then
invoke the single-worker and two-worker probes:

```text
claude plugin validate tests/host-probes/claude
copilot plugin marketplace add ./tests/host-probes/copilot
codex plugin marketplace add ./tests/host-probes/codex
```

Expected single-worker result on every host: `DAODAN_PROBE_OK`.
Expected coordinator result: both unique worker nonces plus `DELIVERED=2/2`.

Remove each disposable marketplace after the probe.

## Evidence

```text
host | isolated workers | parallel fan-out | shared tasks | peer messaging | worker allowlist | packaged roles
```

| host | isolated workers | parallel fan-out | shared tasks | peer messaging | worker allowlist | packaged roles |
|---|---|---|---|---|---|---|
| claude | TODO | TODO | TODO | TODO | n/a | TODO |
| copilot | TODO | TODO | TODO | TODO | TODO | TODO |
| codex | TODO | TODO | TODO | TODO | n/a | TODO |

**The table above is not yet measured.** The native smoke probes require driving real Claude Code,
Copilot and Codex sessions by hand, which is the one step of this task that cannot be automated from
the repository. Until it is filled in, `adapters/<host>/coordination.toml` carries the spec's
documented assumptions and every strategy row there is provisional.

Release baseline, applied when the table is filled in:

- `isolated workers = yes` is required for every host.
- `parallel fan-out`, `shared tasks` and `peer messaging` may be `conditional` or `no`.
- Copilot must report `worker allowlist = yes`.
- Codex may report `packaged roles = no` only when inline role delivery succeeds.
