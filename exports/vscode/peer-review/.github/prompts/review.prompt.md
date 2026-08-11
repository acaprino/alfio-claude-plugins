---
description: Cross-model peer review of a plan, a spec, or the decisions this session has just made. Builds a challenge packet, sends it to a challenger model on an OpenAI-compatible endpoint after explicit consent, runs an evidence-backed multi-round dialectic with a verbatim ledger, and computes a verdict of accepted edits, refutations, and standoffs. With no path, materializes the session's context and decisions into a frozen brief and challenges that
agent: peer-review-orchestrator
argument-hint: [<path-to-plan-or-spec> | <topic>] [--challenger=<profile>] [--rounds=N] [--dry-run] [--apply]
---

<!-- Vendored from plugins/peer-review/commands/review.md in acaprino/claude-code-daodan,
     MIT, with the dispatch mechanics adapted for VS Code (see peer-review-orchestrator.agent.md
     for why an orchestrator is needed) and MCP tool calls renamed to their bare tool names,
     since an MCP server's tool ids depend on the name the user gave that server. -->

# Cross-Model Peer Review

`$SKILLS` is the installed skills directory: the first of `.github/skills/`,
`.agents/skills/`, `.claude/skills/`, `~/.copilot/skills/` that exists.

Orchestrates one deliberation run against `$SKILLS/cross-model-peer-review/protocol/PROTOCOL.md`:
builds an immutable packet, gets explicit consent, sends it to an external challenger model,
runs an evidence-backed multi-round dialectic between the challenger and a
repository-grounded respondent, and computes a verdict from a ledger that is never
hand-edited.

## Critical rules

1. **Execute phases in order**: 0, 1, 1b, 2, 2b, 3, 4, 5, 6, then `--apply`. Do not skip
   or reorder them.
2. **The consent gate (Phase 1b) is absolute.** No call to the `peer_ask` tool may be
   reachable before it. Calling `peer_profiles` before the gate is fine: it is a local
   capability check, never network egress.
3. **`--dry-run` stops at the consent gate**, before it asks for a decision.
4. **The verdict (Phase 6) is computed from `03-ledger.md` only.** Prose in the verdict
   may explain a state; it must never assign or change one outside the ledger.
5. **A run with findings never terminates after round 1.** `--rounds` below 2 is
   rejected per R11.
6. **Never hardcode a filesystem path to this bundle.** Self-references use
   `$SKILLS/cross-model-peer-review/...`.
7. **Every `peer_ask` call can return `{"error": "..."}` instead of a reply.** Follow
   "Transport error handling" below at every call site; never treat an error payload as
   a challenger reply.
8. **If `peer_profiles` or `peer_ask` is not reachable**, the `peer-review` MCP server
   is not configured. Stop at Phase 0 step 5 and point at the bundle README's setup
   section rather than attempting the run without it.

## Files this run writes

All paths are relative to the run directory `.peer-review/YYYY-MM-DD-HHMM-<slug>/`.

| File | Written by | Phase |
|---|---|---|
| `00-brief.md` | `brief-builder`, brief mode only | 0b |
| `00-packet.md` | `packet-builder` | 1 |
| `01-challenge-r1.md` | the orchestrator, from the challenger's transport reply | 2 |
| `01b-amendment.md` | the orchestrator | 2b |
| `02-response.md` | `respondent` | 3 |
| `03-ledger.md` | the orchestrator, updated every phase, history appended per finding | 2, 3, 4, 5 |
| `05-challenge-r2.md`, `07-challenge-r3.md` | the orchestrator, from the challenger's transport reply | 4 |
| `06-response-r2.md`, `08-response-r3.md` | `respondent` | 4 |
| `09-certification.md` | the orchestrator, from the challenger's transport reply | 5 |
| `10-corrective.md` | the orchestrator (challenger section) plus `respondent` (respondent section), only if a MISREPRESENTED flag is substantiated | 5 |
| `04-verdict.md` | the orchestrator, computed from the ledger | 6 |

## Transport error handling

Applies to every `peer_ask` call in Phases 2, 4, 5, and the corrective round of Phase 5.

If the tool returns `{"error": "<message>"}` instead of `{text, usage, model, latency_ms}`:

1. Do not write a challenge or response file from it, and do not touch the ledger for
   this call.
2. Record the phase and the verbatim error message in a running "Transport failures"
   note kept in memory for Phase 6.
3. Stop issuing further `peer_ask` calls for the rest of the run.
4. If this happened on the very first call (Phase 2, round 1), there is no ledger yet:
   report the failure to the operator and stop. Do not write `04-verdict.md`.
5. Otherwise, skip straight to Phase 6. Every finding still `OPEN` or `CHALLENGED` at
   that point is reported in its own "Interrupted by transport failure" verdict
   subsection, not folded into `STANDOFF`: an unanswered call is not the same claim as
   a saturated one.

## Phase 0: Setup

This prompt has **two modes**, decided in step 1 and differing only in where the
artifact comes from. **Artifact mode** judges a plan or spec already on disk. **Brief
mode** materializes the session's context and decisions into `00-brief.md` first, then
judges that. From Phase 1 onward the two are the same run: every later phase reads
`<artifact path>`, and Phase 0b is what sets it in brief mode.

1. Parse `$ARGUMENTS`. Flags: `--challenger=<profile>` (optional), `--rounds=N`
   (default `3`), `--dry-run`, `--apply`. The first non-flag token, if any, selects the
   mode:
   - **Resolves to an existing readable file**: artifact mode, that file is the
     artifact path.
   - **Looks like a path but does not exist** (contains `/` or `\`, or ends in `.md` or
     `.markdown`): stop with a not-found error naming the path, and print the usage
     from `argument-hint`. Never fall through to brief mode here: a mistyped path must
     not silently become a topic.
   - **Anything else**: brief mode, and the token is the topic hint that scopes which
     decisions the brief covers.
   - **No non-flag token at all**: brief mode with no topic hint, covering the
     session's decisions as a whole.
2. **Validate `--rounds`.** Valid range is `2` to `3`: round 1 always runs in Phase 2,
   and the canonical file layout only names challenge/response files through round 3
   (`05-challenge-r2.md`/`06-response-r2.md`, `07-challenge-r3.md`/`08-response-r3.md`).
   A value below `2` is rejected outright, citing R11 (a run with findings may never
   terminate after round 1). A value above `3` is clamped to `3` with a printed note,
   since no canonical file names exist beyond it. Default `3`.
3. **Validate the artifact** (artifact mode only; brief mode has no file yet and skips
   this step). Read the file at the given path with `#read/readFile`.
   - Refuse if it does not exist, or is not readable as text.
   - Refuse anything that looks like a unified diff (starts with `diff --git`, or
     contains `--- a/` / `+++ b/` header pairs) or a source file (extension outside
     `.md`/`.markdown`), with a message pointing at `/team-review` in the `_pipelines`
     bundle for that kind of target instead (install it if it is not already present).
   - This prompt reviews intent artifacts, never code changes. The diff refusal holds
     in both modes: a brief describes decisions, and a request to challenge a diff is
     redirected the same way.
4. **Compute the run directory.** Slug: in artifact mode, the artifact's basename
   without extension; in brief mode, the topic hint, or `session-brief` when there is
   none. Either way
   lowercased, non-alphanumeric runs collapsed to a single hyphen. Timestamp: local
   `YYYY-MM-DD-HHMM`. Directory: `.peer-review/<timestamp>-<slug>/`. On a name collision
   (a concurrent invocation in the same minute), append `-2`, `-3`, ... Create the
   directory before any write, with `#edit/createDirectory`.
5. **Resolve the challenger profile.** Call the `peer_profiles` tool with no arguments.
   It returns `{default, profiles: [{name, base_url, model, api_key_env, available}], source}`.
   - Chosen name: `--challenger` value if given, else `default`.
   - If `default` is null and no `--challenger` was given: stop. No profile is
     configured (`peer_profiles`'s `source` field is `null` when no profiles file was
     found at all). Point at `$SKILLS/cross-model-peer-review/mcp/profiles.example.json`,
     the `.peer-review/profiles.json` / `~/.peer-review/profiles.json` locations it can
     be placed at, and the `PEER_REVIEW_PROFILES` environment variable, which names
     any other path to check first, ahead of both defaults.
   - If the chosen name does not appear in `profiles`: stop, listing the configured
     profile names, the `source` path `peer_profiles` reported (which file was
     actually loaded), and pointing at
     `$SKILLS/cross-model-peer-review/mcp/profiles.example.json` and
     `PEER_REVIEW_PROFILES` for placing or relocating a profiles file.
   - If the chosen profile's `available` is `false`: stop, naming its `api_key_env`
     value as the environment variable that must be set, pointing at
     `$SKILLS/cross-model-peer-review/mcp/profiles.example.json`.
   - Otherwise record the resolved profile's `name`, `base_url`, and `model` for later
     phases.
6. Initialize an empty transport-failures list and an empty token-accounting list, both
   held in memory for Phase 6.

## Phase 0b: Brief

**Brief mode only.** In artifact mode, skip this phase entirely and go to Phase 1.

This phase runs after profile resolution, not before it, so an unconfigured or
unavailable profile stops the run before an agent is spent building a brief.

1. Dispatch `brief-builder` with `#agent/runSubagent`, giving it:
   - Run directory: `<run directory>`
   - Topic hint: `<topic hint, or "none: cover the session's decisions as a whole">`
   - The instruction to materialize this session's context and decisions into
     `00-brief.md` per its protocol, and to report back the brief's byte size, the
     count of taken decisions, the count of open decisions, and the "could not be
     sharpened" list verbatim.
2. On return, confirm `00-brief.md` exists in the run directory with
   `#search/fileSearch`. If it does not, report the agent's failure and stop; nothing
   was sent, nothing to clean up.
3. **Freeze.** From this point the brief is the artifact, and `<artifact path>` in every
   later phase means `<run directory>/00-brief.md`. It is never edited again for the
   rest of the run: that is what makes R2 hold for a materialized artifact, and what
   lets Phase 1's independent digest recheck compare three values that were never
   supposed to diverge. Wanting a different brief means a new run, not an edit.
4. **Vagueness stop (doctrine).** If the brief carries no taken decision and no open
   decision that passed the builder's decidability self-check, stop here and say so.
   A packet built from that brief would produce findings standing on air, which is the
   one case the doctrine says not to spend a run on. Report the "could not be
   sharpened" list so the user can see exactly what was too vague.
5. Print the brief's path, its byte size, and the two decision counts, followed by the
   "could not be sharpened" list when it is non-empty. The full brief text is disclosed
   inside the packet at the Phase 1b consent gate, which is where a look before egress
   belongs; this line is a pointer, not a substitute for reading it.

## Phase 1: Packet

1. Compose the mandate text. Use the template for the mode this run is in.

   **Artifact mode**: "Judge whether `<artifact path>`'s decisions, its plan of action,
   and each rejected alternative's rationale hold up under scrutiny. Prose style,
   formatting, and any file the artifact merely mentions without proposing a change to
   it are out of scope."

   **Brief mode**: "Judge whether the situation as described is the right framing of
   what is being decided, whether each taken decision's rationale holds, and whether
   each open decision's option set is complete. The taken decisions themselves are
   settled and are not to be relitigated: their reasoning is what is on trial. Prose
   style and formatting are out of scope."
2. Dispatch `packet-builder` with `#agent/runSubagent`, giving it:
   - Artifact path: `<artifact path>`
   - Run directory: `<run directory>`
   - Mandate: `<mandate text from step 1>`

   Instruct it to build `00-packet.md` in the run directory per its protocol, and to
   report back the byte size of `00-packet.md` and its section list.
3. On return, confirm `00-packet.md` exists in the run directory with
   `#search/fileSearch`. If it does not, report the agent's failure and stop; nothing
   was sent, nothing to clean up.
4. **Independent digest recheck (R15).** Before trusting anything the agent reported,
   verify three values agree, not two:

   1. Recompute the artifact's own byte length and sha256 directly from the source
      file on disk with `#execute/runInTerminal`:

      ```bash
      wc -c <artifact path>
      python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <artifact path>
      ```

   2. Read the `bytes:` and `sha256:` lines `00-packet.md` records immediately above
      the embedded artifact: the packet's own claim about the source.
   3. Extract the embedded artifact block itself from `00-packet.md` (the text between
      those `bytes:`/`sha256:` lines and the start of the next section, `## Ground truth`),
      and hash and measure that extracted text the same way. This is the
      text the outgoing request will actually carry. Checking only the recorded digest
      line (step 2) proves nothing about whether the embedding below it was truncated
      or altered after that line was written; R15 requires source, packet embedding,
      and outgoing request to be byte-identical, and the embedding is what step 3
      checks.

   All three byte-length and sha256 values (source recompute, packet's recorded
   digest, packet's embedded-text digest) must match exactly. If any pair disagrees:
   abort the run before any transport call. Report which values disagreed and leave
   the run directory in place for inspection. This is the run-invalidating defect R15
   exists to catch; a mismatch is never a warning.

## Phase 1b: Consent gate

No transport call of any kind precedes this phase.

1. **Byte cap pre-flight.** Compare `00-packet.md`'s byte size (`<N>` below) against
   the transport's payload cap, 400000 bytes (the `peer_ask` tool refuses anything
   larger outright, per `server.py`). If `<N>` exceeds the cap, do not present the
   gate below: report the packet's size against the cap and stop. Approving a packet
   the transport will refuse is not a real consent decision; the artifact or the
   material it names must be reduced and the run repeated.
2. Present verbatim, with the actual values substituted for the placeholders:

```
About to send this packet to an external service:
  destination: <base_url>  model: <model>
  size: <N> bytes (transport cap: 400000 bytes)
  sections: Mandate, Artifact, Ground truth, Constraints, Considered and rejected,
            Known weaknesses, Open questions, Out of scope, Response contract
Nothing else leaves this machine. Send it? (yes / no)
```

Where `<base_url>` and `<model>` come from the profile resolved in Phase 0, and `<N>`
is the byte size of `00-packet.md`.

- **`--dry-run`**: stop here. Report the packet path (`<run directory>/00-packet.md`)
  and that nothing was sent. End the run.
- **Otherwise**: wait for the operator's explicit reply. Only a literal `yes` proceeds
  to Phase 2. Any other reply (`no`, empty, anything ambiguous) aborts the run: report
  that consent was withheld, leave the run directory in place, end the run.

## Phase 2: Round 1

1. Load the Round 1 prompt: read `$SKILLS/cross-model-peer-review/protocol/round-prompts.md`
   and extract the fenced block under `## Round 1 (critique)`.
2. Call the `peer_ask` tool: `profile` is the resolved profile name, `system` is the
   Round 1 prompt text, `messages` is `[{"role": "user", "content": "<the full text of 00-packet.md>"}]`.
3. Handle the error shape per "Transport error handling" above.
4. On success, write the `text` field verbatim to `01-challenge-r1.md` with
   `#edit/createFile`. Note the `usage`, `model`, and `latency_ms` fields in the
   token-accounting list under round 1.
5. **Initialize `03-ledger.md`.** Parse the `## Findings` section of
   `01-challenge-r1.md`. For each finding `F<NN>`, create one entry using the template
   from `$SKILLS/cross-model-peer-review/protocol/finding-lifecycle.md`:

   ```
   Finding F<NN>
     claim (verbatim): <copied exactly from the reply>
     falsifier (verbatim): <copied exactly from the reply> | admissibility: (pending)
     challenger evidence: <the failure scenario / section attacked, as given>
     respondent position: (pending)
     respondent evidence: (pending)
     restatements: none
     state: OPEN
     new evidence since previous round: n/a (round 1)
     history:
       - R1: raised (severity <severity>)
   ```

6. **Transmission-artifact check (R15), applied before any finding is left OPEN.** Key
   this on substance, not on the free-text `section attacked` label the challenger
   wrote in its own words. For each finding, locate the specific material its claim
   and failure scenario actually reference (a quoted phrase, a named decision, a
   specific fact) inside `00-packet.md`: the embedded Artifact text, Ground truth,
   Constraints, Considered and rejected, Known weaknesses, Open questions, or Out of
   scope. Phase 1's digest check already proved the packet is byte-identical to the
   source, so material that genuinely cannot be located anywhere in the packet cannot
   be a live claim about the artifact; it is noise the challenger introduced.
   - **Substance absent everywhere in the packet**: set that entry's `state` directly
     to `TRANSMISSION_ARTIFACT`, skipping `OPEN`, and record what was actually
     searched for and not found in place of `respondent evidence`. Do not send these
     findings to the respondent in Phase 3.
   - **Substance present, but the `section attacked` label names the wrong section or
     only paraphrases it**: this is a labeling mismatch, not a transmission artifact.
     Leave `state = OPEN`, add a soft `section-label mismatch` note to the entry's
     history (naming the section the substance was actually found at), and send the
     finding to the respondent in Phase 3 as normal. The respondent has full
     repository access (R8) and judges the substance on its merits regardless of
     which section the challenger thought it lived in.
7. Findings capped at 12 are the challenger prompt's responsibility, not this
   orchestrator's. If a reply carries more than 12, record every one of them anyway
   and note the overrun in the ledger's history for round 1.

## Phase 2b: Context amendment

1. Parse the `## Context requests` section of `01-challenge-r1.md`. Each line names a
   locator.
2. For each locator, in order, with running totals starting at 0 files / 0 bytes:
   - **Refuse** if the locator resolves outside this repository (an external URL, an
     absolute path outside the repo root, a `..` traversal), or does not resolve to an
     existing file at all. Refuse reason: "outside the repository" or "not found".
   - **Refuse** if granting it would push the running totals past 10 files or 200 KB
     total. Refuse reason: "context amendment cap reached (10 files / 200 KB)".
   - **Refuse** if the locator names material already present in `00-packet.md` (the
     challenger already has it). Refuse reason: "already in the packet".
   - **Otherwise grant it**: read the file with `#read/readFile`, add its byte size to
     the running total, increment the file count.
3. Write `01b-amendment.md` with `#edit/createFile`:

   ```
   # Context Amendment, Round 1

   ## Granted
   | Locator | Bytes | Note |
   |---|---|---|

   ## Refused
   | Locator | Reason |
   |---|---|

   Running totals: <N> files / 10, <K> KB / 200 KB.
   ```

4. Granted material is not sent to the respondent (which already has full repository
   access per R8 and does not need packet-supplied facts). It is prepended to the
   round 2 challenger payload in Phase 4, each fact tagged `GIVEN`, with its locator.

## Phase 3: Response (round 1)

1. Dispatch `respondent` with `#agent/runSubagent`, giving it:
   - Challenge file: `<run directory>/01-challenge-r1.md`
   - Ledger: `<run directory>/03-ledger.md`
   - Response file to write: `<run directory>/02-response.md`

   Instruct it to answer every finding in the challenge file whose ledger state is
   OPEN, and that findings already `TRANSMISSION_ARTIFACT` are closed and must not be
   re-opened.
2. On return, for each answered finding, update only the fields the respondent role
   owns (`falsifier admissibility`, `respondent position`, `respondent evidence`,
   `restatements`, `new evidence since previous round`). Never let the agent's report
   change `claim`, `falsifier` text, or `state` directly; those stay under this
   orchestrator's control.
3. **Apply state transitions**, per finding:
   - `admissibility: INADMISSIBLE` (the one restatement request already exhausted):
     `state = UNTESTABLE`, regardless of the respondent's position. This is the
     "falsifier fails admissibility twice" transition from `finding-lifecycle.md`.
   - `admissibility: RESTATED` (pending the challenger's confirmation, not yet given):
     the finding is held open. Leave `state = OPEN`; per R10, a restatement cannot
     support a verdict until the challenger confirms it, so no position-based
     transition applies yet. Carry it into Phase 4 for confirmation.
   - `admissibility: OK`, position `ACCEPT`: `state = RESOLVED_ACCEPT`.
   - `admissibility: OK`, position `REFUTE`: `state = CHALLENGED`. The challenger has
     not yet seen this refutation; it is not resolved until certified.
   - `admissibility: OK`, position `NEEDS-EVIDENCE` or `DISAGREE`: `state = CHALLENGED`.
4. Append one history line per finding: `R1: respondent <position>, admissibility <outcome> -> <new state>`.

## Phase 4: Challenge rounds (2..N)

Runs for round 2, and round 3 if `--rounds` is 3. Each round processes only the
**still-open set**: findings whose `state` is `OPEN` or `CHALLENGED` after the
previous round, minus anything terminal (`RESOLVED_*`, `STANDOFF`, `UNTESTABLE`,
`TRANSMISSION_ARTIFACT`), minus any `CHALLENGED` finding flagged `saturated: no further rounds`
by step 7 below. A saturated `REFUTE` finding is not terminal, but it
is also not resent: its outcome is already settled pending certification. Every step
below that says "still-open finding" or "still-open subset" means exactly this set;
this is where that exclusion is enforced.

For round `r` (2 or 3), files `05-challenge-r2.md`/`07-challenge-r3.md` and
`06-response-r2.md`/`08-response-r3.md`:

1. Load the Challenge round prompt: read
   `$SKILLS/cross-model-peer-review/protocol/round-prompts.md`, extract the fenced
   block under `## Challenge round (2..N)`.
2. Build the round payload: for each still-open finding, its `claim` and `falsifier`
   verbatim, the respondent's current `position` and `evidence`, and (round 2 only) any
   material granted in Phase 2b, each fact tagged `GIVEN` with its locator. If a
   finding's ledger entry carries a pending proposed restatement
   (`restatements: RESTATED AS "<wording>"`, not yet confirmed), include that wording
   too, labeled plainly as the respondent's proposed restatement awaiting the
   challenger's confirmation, so there is something for the challenger's
   `CONFIRM-RESTATEMENT` or `REJECT-RESTATEMENT` reply to answer.
3. Call the `peer_ask` tool with this prompt as `system` and the payload as the user
   message. Handle the error shape per "Transport error handling" above.
4. On success, write the reply to the round's challenge file with `#edit/createFile`.
   Note `usage`, `model`, `latency_ms` under this round in the token-accounting list.
5. **Per finding, apply the reply** (`WITHDRAW`, `MAINTAIN`, `REFINE`,
   `CONFIRM-RESTATEMENT`, or `REJECT-RESTATEMENT`):
   - `WITHDRAW` naming specific falsifying evidence: `state = RESOLVED_WITHDRAWN`.
     Append history: `R<r>: withdrawn, evidence <cited>`.
   - `WITHDRAW` naming no evidence: the finding does not close. `state` stays
     `CHALLENGED`. Flag the entry `unexplained withdrawal` (a dedicated field or a
     history tag); the verdict reports this as a run weakness regardless of what
     eventually happens to the finding.
   - `MAINTAIN` with new evidence or a new argument stated: record `new evidence since previous round: YES` on the challenger side, `state` stays `CHALLENGED`.
   - `MAINTAIN` with an explicit "no new evidence": record `new evidence since previous round: NO` on the challenger side.
   - `REFINE`: record `restatements: RESTATED AS "<the new wording>"`, pending. The
     original claim and falsifier are never overwritten (R10); the restatement travels
     alongside them. `state` stays `CHALLENGED`; the restated wording is what the
     respondent answers in this round's response step, and confirmation of the
     restatement is implicit in the respondent's willingness to answer it (there is no
     separate confirmation step defined beyond the respondent's next reply).
   - `CONFIRM-RESTATEMENT`, answering a proposed falsifier restatement shown in this
     round's payload (step 2): set the falsifier's admissibility to `OK` using the
     restated wording, and record
     `restatements: RESTATED AS "<wording>" confirmed by challenger in R<r>`.
     `state` stays `OPEN`; the finding rejoins the still-open set for this round's
     response step (step 6) so the respondent can investigate the now-admissible
     falsifier for the first time.
   - `REJECT-RESTATEMENT`, answering the same proposal: the one restatement request R9
     allows is now spent and refused. The original falsifier was already inadmissible
     as stated (that is why a restatement was proposed at all), so
     `state = UNTESTABLE` now.
   - If a `RESTATED` (pending) admissibility finding was carried in from Phase 3 and
     this round's challenger reply does not use `CONFIRM-RESTATEMENT` or
     `REJECT-RESTATEMENT` for it, it remains `OPEN` and is carried forward again; do
     not force a transition on an unconfirmed restatement.
6. Dispatch `respondent` for the still-open subset, same shape as Phase 3, targeting
   this round's response file (`06-response-r2.md` or `08-response-r3.md`). Handle its
   reply with the same transition table as Phase 3 step 3, plus: the respondent also
   reports `new evidence since previous round: YES | NO` for its own side (did it
   change position or cite new material this round).
7. **Saturation test**, per still-open finding, per `finding-lifecycle.md`: if the
   challenger side's `new evidence since previous round` is `NO` and the respondent
   side's is also `NO`, and neither side's position changed from the previous round,
   saturation has occurred. What happens next depends on the respondent's current
   position, mirroring step 8's `REFUTE` branch below rather than treating every
   saturated finding alike:
   - **Position `REFUTE`**: do not set `STANDOFF`. Leave `state = CHALLENGED` and add
     `saturated: no further rounds` to the entry (a dedicated field or a history tag).
     This excludes the finding from every later round's payload (enforced by the
     still-open set definition in this phase's intro, which steps 2 and 6 both draw
     from) without finalizing it, so it falls through unresolved into Phase 5 step 1's
     existing collection clause, which already treats a `CHALLENGED` finding whose
     current position is `REFUTE` as a proposed `RESOLVED_REFUTE` and sends it to
     certification. Certification is the point where R12 actually applies: the
     challenger compares its own verbatim original words against the respondent's
     one-line closing rendering, a comparison a mid-debate `MAINTAIN` reply never
     shows it, so saturating early does not substitute for that check. Append history:
     `R<r>: saturation, both sides NO new evidence, positions unchanged, REFUTE carried to certification (not STANDOFF)`.
   - **Position `NEEDS-EVIDENCE`, `DISAGREE`, or no position recorded**: set `state = STANDOFF` immediately (not cap-terminated: this is evidence saturation). No further rounds process this finding. Append history: `R<r>: saturation, both sides NO new evidence, positions unchanged -> STANDOFF`.
8. **Round cap.** After the last round this invocation runs (round 3, or round 2 if
   `--rounds` was clamped or given as 2), findings still open are resolved by their
   most recent respondent position, never swept as one block:
   - **`CHALLENGED` with the respondent's current position `REFUTE`**: not swept. It
     carries forward as a proposed `RESOLVED_REFUTE` into Phase 5.
     `finding-lifecycle.md`'s own transition table has a "proposed RESOLVED_REFUTE ->
     CHALLENGED" line, which presupposes exactly this proposed state as certification's
     input; sweeping it to `STANDOFF` here would make that transition, and certification
     itself, unreachable. Any `unexplained withdrawal` flag on the finding still carries
     into the verdict regardless of this promotion.
   - **`CHALLENGED` with position `NEEDS-EVIDENCE`, `DISAGREE`, or no respondent
     position recorded**: becomes `STANDOFF`, labeled `cap-terminated` in its history
     line, distinct from the saturation label in step 7. Any `unexplained withdrawal`
     flag still carries into the verdict.
   - **`OPEN`** (a `RESTATED` admissibility outcome the challenger never confirmed):
     terminates `UNTESTABLE`, not `STANDOFF`. It never received a substantive
     respondent position and its falsifier was never admissible as stated (R9, R10);
     `finding-lifecycle.md` routes procedural failures to `UNTESTABLE`,
     `TRANSMISSION_ARTIFACT`, or `CERTIFICATION_FAILED`, never to `STANDOFF`, and an
     unconfirmed restatement is exactly such a procedural failure, not a substantive
     contest that survived the evidence.

## Phase 5: Certification

1. Collect every finding whose `state` is `RESOLVED_ACCEPT`, `RESOLVED_WITHDRAWN`,
   `STANDOFF`, or `UNTESTABLE`, plus every `CHALLENGED` finding whose most recent
   respondent position was `REFUTE` (see the note below on why `RESOLVED_REFUTE` only
   exists starting in this phase). For each, attach a one-line rendering of how it
   closed, in the respondent's own words where the respondent produced one.

   Note on `RESOLVED_REFUTE`: nothing in Phases 2 to 4 ever assigns this state directly
   (a `REFUTE` position only ever produces `CHALLENGED`, per R12 and R13's requirement
   that the challenger certify a refutation before it is final). Certification is the
   only place a finding can reach `RESOLVED_REFUTE`: a `CHALLENGED` finding whose most
   recent respondent position was `REFUTE` and which the challenger certifies (does not
   flag, or flags unsubstantiated) in this phase becomes `RESOLVED_REFUTE` here. Fold
   this promotion into step 3 below.

   `TRANSMISSION_ARTIFACT` findings are excluded: they closed before the respondent
   ever answered them, so there is no respondent rendering to certify against, and no
   claim of the challenger's own words to defend.
2. Load the Certification prompt: read
   `$SKILLS/cross-model-peer-review/protocol/round-prompts.md` under `## Certification`.
   Call the `peer_ask` tool with this as `system` and the collected findings plus
   renderings as the user message. Handle the error shape per "Transport error
   handling" above.
3. On success, write the reply to `09-certification.md`. For each finding:
   - `CERTIFIED`: finalize its state. If the finding entered this phase `CHALLENGED`
     with a `REFUTE` respondent position, set `state = RESOLVED_REFUTE` now. Anything
     already terminal stays as it was, now certified.
   - `MISREPRESENTED`, substantiated (the quoted original words genuinely contradict
     the rendering, checked against the ledger's verbatim `claim` field, which never
     changed): this is a procedural failure of the refutation (R12), so it applies to
     findings the certification step was about to finalize as `RESOLVED_REFUTE`. Revert
     `state = CHALLENGED`, strike any restatement (`restatements: none`), and continue
     to step 4.
   - `MISREPRESENTED`, unsubstantiated (no real contradiction, or no quote given):
     discard the flag, note it in history, finalize the state as `CERTIFIED` would.
   - `MISREPRESENTED`, substantiated, flagged against a finding that did **not** enter
     this phase as `CHALLENGED` with a `REFUTE` position (a `RESOLVED_WITHDRAWN`,
     `STANDOFF`, or `UNTESTABLE` closure): R12 ties this mechanism to a procedural
     failure of the refutation, and none of these closures was produced by the
     respondent's rendering, so there is nothing to invalidate. `state` does not
     change. Record the flag and the challenger's quote in `09-certification.md` and
     carry it as a rendering dispute alongside that finding's normal reporting in
     Phase 6, distinct from a certified refutation's substantiated misrepresentation.
4. **Corrective round, at most once for the whole run**, only for findings reverted in
   step 3. If a corrective round has not already run in this invocation:
   - Call the `peer_ask` tool once more, `system` built from the same Challenge round
     prompt semantics but scoped to "answer against your original claim, this is a
     corrective round, not a debate" framing, `messages` carrying only the reverted
     findings' original verbatim claims and falsifiers. Handle the error shape: on
     failure here, treat every reverted finding as `CERTIFICATION_FAILED` (no budget
     left to retry) and record the transport error as the reason instead of budget
     exhaustion.
   - On success, write the challenger's part under a `## Challenger` heading in
     `10-corrective.md`.
   - Dispatch `respondent` targeting `10-corrective.md`, instructed to append its
     answer under a `## Respondent` heading in that same file (this is the one file
     the canonical layout attributes to "both" roles) without disturbing the
     challenger section already written.
   - This is the last exchange for these findings: there is no second certification
     pass (that would make the one-corrective-round cap meaningless). Finalize directly
     from the respondent's corrective answer: `ACCEPT -> RESOLVED_ACCEPT`, `REFUTE -> RESOLVED_REFUTE`, `NEEDS-EVIDENCE` or `DISAGREE -> CERTIFICATION_FAILED`. This is
     a procedural failure, not a standoff: R12 states outright that a misrepresentation
     never manufactures a standoff, and `finding-lifecycle.md` routes procedural
     failures to `UNTESTABLE`, `TRANSMISSION_ARTIFACT`, or `CERTIFICATION_FAILED`,
     never `STANDOFF`. No round cap is involved here either: the corrective round is a
     fixed one-shot outside `--rounds`, so a `cap-terminated` label never applies to it.
   - If a corrective round already ran earlier in this same invocation (should not
     normally occur, since certification runs once per run), any further reverted
     finding goes straight to `CERTIFICATION_FAILED` instead.
   - If no findings were reverted in step 3, skip this step entirely; no
     `10-corrective.md` is written.

## Phase 6: Verdict

Compute `04-verdict.md` from `03-ledger.md` alone. Never introduce a fact here that is
not already a ledger field. Write it with `#edit/createFile`. Sections, in order:

1. **Accepted changes**, as concrete edits. One entry per `RESOLVED_ACCEPT` finding:
   the finding id, the claim in one line, and a concrete edit action against the
   artifact (what text or section changes, and how) specific enough for `--apply` to
   execute it with `#edit/editFiles`.
2. **Refutations with evidence.** One entry per `RESOLVED_REFUTE` finding: the claim,
   the respondent's locator and evidence that satisfied the falsifier as stated.
3. **Standoffs.** One entry per `STANDOFF` finding: the challenger's position, the
   respondent's position, which label applies (saturation or cap-terminated), and what
   additional evidence or action would settle it.
4. **Untestable.** One entry per `UNTESTABLE` finding: the falsifier as given, and
   which failure produced it, distinguishing the two routes R9's one-restatement cap
   allows: a restated falsifier the respondent checked a second time and still could
   not admit, versus a proposed restatement the challenger explicitly rejected or
   never confirmed before the run moved on.
5. **Certification failures.** One entry per `CERTIFICATION_FAILED` finding: the
   original claim, the substantiated misrepresentation that reverted it, and why no
   corrective round resolved it (budget already spent, or the corrective round itself
   failed to transmit).
6. **Transmission artifacts**, with the digest check that caught them. One entry per
   `TRANSMISSION_ARTIFACT` finding: what material it claimed to attack, and a reminder
   that Phase 1 already verified the packet byte-identical to the source (R15), so the
   absence is in the challenger's reply, not in what was sent. Recommend the run be
   repeated rather than the finding trusted, per R15.
7. **Unexplained withdrawals**, reported as a weakness of the run per R13. One entry
   per finding ever flagged `unexplained withdrawal` in Phase 4, regardless of its
   final state.
8. **Refused context requests.** Pulled directly from `01b-amendment.md`'s Refused
   table, with reasons.
9. **Provenance**, four axes per role (model, runtime, context, human), never
   collapsed or scored (R4). Three rows: packet builder, challenger, respondent. The
   artifact's proposer is out of scope per R1 and gets no row.
   - **Packet builder**: model, the orchestrating session's own model; runtime, the
     `packet-builder` Copilot agent; context, full repository access; human, none.
   - **Challenger**: model and runtime filled directly from the resolved profile
     (`<model>` at `<base_url>`); context, packet-only plus any Phase 2b grants,
     tagged GIVEN; human, none. If a future run fills this role with a human
     reviewer instead, mark the model axis absent per R4 and fill the human axis
     instead.
   - **Respondent**: model, the orchestrating session's own model; runtime, the
     `respondent` Copilot agent with full repository access (R8); context, the full
     repository; human, none.
   - **Artifact origin** (R13), one line: `pre-existing` in artifact mode, naming the
     path, or `materialized for this run by the brief-builder agent` in brief mode.
     A materialized artifact shares its author's context with the side being judged,
     which a reader must weigh and no requirement can remove. State it plainly rather
     than leaving it to be inferred from the run directory's contents.
10. **Promotions.** Every `GIVEN -> DERIVED` line recorded in the ledger's respondent
    evidence fields, with the deriving role and locator (R14).
11. **Token accounting**, from every `peer_ask` call's `usage`, `model`, and
    `latency_ms` fields, tabulated by round (1, 2, 3, certification, corrective).
12. Close with: finding count is never the quality measure. A run whose findings all
    end in refutation, withdrawal, standoff, or untestable, with none surviving as an
    accepted change, is still a success if every one of those deaths is evidenced: the
    deliverable is a reduction in decisional uncertainty, not a review.

If Phase 2, 4, or 5 recorded a transport failure and stopped early, open `04-verdict.md`
with an "Interrupted by transport failure" section naming the phase and the verbatim
error, before the twelve sections above (populated only from whatever ledger state
exists).

## `--apply`

Only after `04-verdict.md` is written.

**Artifact mode only.** In brief mode `--apply` is refused, with the reason: the
artifact is `00-brief.md`, a frozen record of what the session had decided at the
moment the run started, and editing it changes nothing downstream because nothing
downstream reads it. The deliverable is the verdict's Accepted changes list, which
names decisions to revisit rather than text to rewrite. Print that list and stop, the
same as a run without the flag. Say plainly that the flag was refused and why, rather
than silently ignoring it.

- **Without `--apply`**: print the Accepted changes edit list from the verdict and
  stop. Nothing is modified.
- **With `--apply`**: for each Accepted changes entry, apply the described edit to the
  artifact with `#edit/editFiles`. After all edits, append a changelog section to the
  artifact:

  ```markdown
  ## Peer review <date>

  Reviewed via /review. Full run: `<run directory>/`.
  Accepted: <N>. Refuted: <N>. Standoffs: <N>. See 04-verdict.md for detail.
  ```

  Report the applied edits and the changelog addition. The artifact is never modified
  before this step (R2): a changed artifact is a new run, not a resumed one.
