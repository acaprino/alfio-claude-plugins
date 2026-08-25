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
| claude | yes | yes | conditional | conditional | n/a | yes |
| copilot | TODO | TODO | TODO | TODO | TODO | TODO |
| codex | yes | yes | no | no | n/a | no (inline succeeded) |

**Claude and Codex are measured; Copilot is not.** The Claude row comes from two headless runs
against the fixture package, loaded with `--plugin-dir` so nothing was registered in a real profile:

```bash
cd <scratch> && claude -p "Use the daodan-probe 'probe' skill and follow it exactly."   --plugin-dir tests/host-probes/claude/plugins/probe --permission-mode bypassPermissions
# -> DAODAN_PROBE_OK

cd <scratch> && claude -p "<two-worker coordination probe>"   --plugin-dir tests/host-probes/claude/plugins/probe --permission-mode bypassPermissions
# -> NONCE=alpha / NONCE=beta / DELIVERED=2/2 / ISOLATED=yes PARALLEL=yes
```

`shared tasks` and `peer messaging` read `conditional` because they belong to the native team layer,
which is off by default; the probe satisfied the contract without them, which is the point of the
`parallel-subagents` baseline. `packaged roles = yes`: the coordinator dispatched the packaged
`probe-worker` by name.

Two defects came out of running this rather than assuming it, both now fixed:

1. **`strict: false` alongside component arrays is rejected by the host.** The install failed with
   "conflicting manifests: both plugin.json and marketplace entry specify components". The fixtures now
   declare `strict: true`. The generated catalogs never carried the key, so they were unaffected.
2. **Generated `plugin.json` files had no `author`.** `claude plugin validate .` warned on all 40.
   The manifest templates now emit the marketplace owner, and validation is clean.

The Codex row comes from `codex plugin marketplace add ./tests/host-probes/codex`, `codex plugin add
daodan-probe@daodan-probe-codex`, then two `codex exec` runs; the disposable marketplace and plugin
were removed afterwards and `~/.codex/config.toml` was byte-identical to its pre-probe backup.

```text
# single worker -> DAODAN_PROBE_OK
# coordinator   -> NONCE=alpha / NONCE=beta / DELIVERED=2/2
#                  ROLE_DELIVERY=inline ISOLATED=yes PARALLEL=yes
```

`packaged roles = no` for Codex, and inline delivery succeeded, which is exactly the condition the
release baseline allows. It confirms `adapters/codex/coordination.toml`, which already declared
`role_delivery = "inline-prompt"`: the assumption was right, and is now evidence. Codex reads
`.agents/plugins/marketplace.json` and lists the plugin from it, so the generated Codex catalog shape
is confirmed too.

Copilot is **not** measured, and the obstacle is this machine rather than the plan: the Copilot CLI
extracts its platform package into `%LOCALAPPDATA%\copilot\pkg` on `C:`, which has 253 MB free of
238 GB, and every launch fails with `ENOSPC` before it reaches argument parsing. Installing the npm
package under a `D:` prefix does not help, because that extraction path is not configurable. Until
that is resolved, `adapters/copilot/` carries the spec's documented assumptions and its strategy rows
are provisional.

Release baseline, applied when the table is filled in:

- `isolated workers = yes` is required for every host.
- `parallel fan-out`, `shared tasks` and `peer messaging` may be `conditional` or `no`.
- Copilot must report `worker allowlist = yes`.
- Codex may report `packaged roles = no` only when inline role delivery succeeds.
