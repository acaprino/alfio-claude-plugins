# research eval harness

Measures whether `/research:team-research` still behaves the way it is designed to behave. The plugin has no bug ground truth to recall: its value is a set of **behavioral invariants** (a plan before any search, no citation outside the sources table, every cited page actually read, the backend stated, effort scaled to the question), and the failure mode is drift, where a later edit quietly removes one and nothing notices.

Each case states a question, the flags, and assertions that either hold or do not. Assertions target the philosophy, never the wording. This directory is a development asset of the marketplace repository: not part of the `research` plugin, not registered in `marketplace.json`, never shipped.

## Protocol

0. **Establish which version is under test, and prove it.** Check `~/.claude/plugins/cache/<marketplace>/research/` against `marketplace.json`; if they differ, update the marketplace and start a new session, or run against the working-tree files and say so in the scorecard. A run whose scorecard does not name the version it exercised is not a result.
1. **Run in a scratch directory**, never in this repository: the report file lands in `research/` under the working directory.
2. **Run the case's command in a FRESH session.** Answer the clarification or plan gate as the case says (usually `Approve`).
3. **Keep the transcript.** Several assertions read it: whether a search happened before the plan, how many researchers were spawned, what each returned.
4. **Score each assertion** `pass`, `fail`, or `n/a` (only when the case makes it conditional).
5. **Record the run** in a copy of `scorecard-template.md` inside the case directory (`scorecard-<date>.md`), and add one row to `RESULTS.md`.

MUST assertions are the invariant. A single MUST failure fails the case. SHOULD assertions describe quality and do not fail the case alone.

## Rules

- Never tell the session under test what the assertions are. Never let it read this directory.
- Whoever wrote the change should not score it; score with a reader holding only the assertions, the transcript and the files.
- Cost (wall-clock, researchers spawned, pages read from the run header) is recorded for every case; in the tier cases it IS the assertion.
- Network results vary; an assertion about content quality is SHOULD, an assertion about pipeline behaviour is MUST.

## Cases

| Case | Invariant under test |
|---|---|
| `plan-before-search` | Without `--auto`, the plan is shown and approved before the first search |
| `clarify-only-when-ambiguous` | A clear question gets no clarifying questions; an ambiguous one gets at most four, in one call |
| `citations-resolve` | No claim in the report cites a source absent from the sources table |
| `sources-were-read` | Every source in the table appears in some researcher's "Sources read" in the companion file |
| `backend-stated` | The backend is in the header; `--backend serper` without a key stops with the setup line |
| `tier-bands` | Researcher counts stay inside the tier band; `deep` runs at most two waves |
| `one-fact-routes-to-quick` | A one-fact question goes to quick-searcher with no research run |
| `majority-failure-stops` | A wave where more than half the researchers fail stops the run instead of synthesizing |
