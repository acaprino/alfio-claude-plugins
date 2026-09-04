# Canary eval: the `team-review` contract on three hosts

`team-review` is the complex canary. It fans out over dimensions chosen at runtime, requires every
reviewer to work in its own context, holds an all-delivered barrier before anything is consolidated,
cross-examines the consolidated set in fresh contexts, and lets exactly one phase write the report.

Each host picks a different topology to do that. The topology may differ; the contract may not.

## What is asserted mechanically

`tests/test_review_pipeline_ports.py` runs in the normal suite and asserts, for every host:

- the fan-out phase declares `isolation = "required"`, `join = "all-delivered"`,
  `concurrency = "preferred"` and `fanout_from = "selection:reviewers"`
- the phase order is scope, context-building, dimension-detection, independent-review,
  delivery-accounting, initial-consolidation, cross-examination, consolidation, report-delivery
- `initial-consolidation` needs `delivery-accounting`, `cross-examination` needs
  `initial-consolidation`, `consolidation` needs `cross-examination`
- only `consolidation` produces `artifact:final-report`
- all seven record contracts exist and travel with every package
- `codebase-xray` keeps `.codebase-xray` as its artifact root, through the neutral write-confinement
  policy
- `senior-review` declares no external team runtime, and every dimension plugin stays a hard
  dependency

Rebuild and verify with:

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests -p "test_review_pipeline_ports.py" -v
python adapters/copilot/policies/xray-guard/test_xray_guard.py
```

The guard suite reports `36/36 passed`.

## Selected topology per host

Recorded in each package's `.daodan-provenance.json` under `harnessStrategies`:

| host | strategy | role delivery | isolated | parallel |
|---|---|---|---|---|
| claude | `native-team` (runtime-optional, falls back to `parallel-subagents`) | named agent | yes | yes |
| copilot | `parallel-subagents` | named custom agent, restricted by the coordinator's `agents` allowlist | yes | yes |
| codex | `parallel-subagents` | inline prompt | yes | yes |

**These rows are provisional.** They come from the adapter coordination files, which still carry the
spec's documented assumptions rather than measured evidence: the host protocol probes in
`tests/host-probes/README.md` have not been run. Re-derive this table from that one.

## Contract results

The behavioural half needs one fixture review run per host.

| host | isolated worker contexts | every expected reviewer delivered or failed | cross-examination after the barrier | every retained finding carries evidence | final report artifact written | single writer respected |
|---|---|---|---|---|---|---|
| claude | TODO | TODO | TODO | TODO | TODO | TODO |
| copilot | TODO | TODO | TODO | TODO | TODO | TODO |
| codex | TODO | TODO | TODO | TODO | TODO | TODO |

**Not yet measured.** The eval passes only when every column is `yes` on every host. A `no` anywhere
blocks the complete release, because a review with a hole in it is the exact failure the mandatory
dependency policy exists to prevent.
