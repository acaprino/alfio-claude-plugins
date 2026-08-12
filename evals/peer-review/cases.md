# peer-review behavioral-invariant eval

Measures whether the `peer-review` plugin still behaves the way the protocol
designs it to behave. There is no bug ground truth to recall here, the same
shape as `evals/ai-tooling/`, not the defect-recall shape of
`evals/senior-review/`: the plugin's value is a set of behavioral invariants,
and the failure mode is drift, where a later edit quietly removes one and
nothing notices.

Each case states an **Invariant** (the property, worded so a harmless rewrite
of the prose still satisfies it), a **Probe** (exactly where in the shipped
content to look, or what scripted scenario to run), and a **Pass** (what must
hold, structurally, for the invariant to survive). Assertions target the
philosophy, never the wording: "no path skips certification" is an invariant,
"the word certification appears in Phase 5" is not. A case that greps for one
exact sentence is a bad case: it breaks on harmless rewording and passes on a
semantic gutting. A rewrite of any agent, the command, or the protocol text
that keeps the philosophy must still pass every case below.

This directory is a development asset of the marketplace repository. It is
not part of the `peer-review` plugin, is not registered in `marketplace.json`,
and is never shipped. It complements, and does not duplicate,
`evals/peer-review/check_protocol_ontology.py` (Case 11 below runs it as-is).

## Rules

- A case that fails once keeps its case forever, even after the failure is
  fixed. Cases are not sacred; invariants are: an assertion that turns out to
  encode a preference rather than a genuine invariant gets deleted, with a
  note in this file saying why.
- A case that finds a real gap is reported as a finding in the results table
  below, not smoothed over. Fixing a found gap is a separate decision for
  whoever controls the plugin, not for this file.
- Grep-and-read probes cite requirement numbers (`R1`..`R15`) and section
  names rather than raw line numbers where the protocol gives a stable
  identifier to cite, per its own convention ("Requirement numbers are stable
  identifiers; binding documents cite them."). Raw line numbers, where used,
  are a snapshot at the time this file was run, not a promise the probe stays
  at that exact line.

## Cases

### Case 1: GIVEN agreement is never corroboration

**Invariant.** A challenger or respondent restating a fact the packet already
supplied never counts as support for anything, in any shipped file's scoring
language or template. Only a participant's own, independent reach into the
authoritative source can turn a GIVEN fact into evidence, and the run has to
say so when it happens.

**Probe.** `protocol/PROTOCOL.md` R14; `agents/respondent.md` Evidence Rules
(the R14 sub-bullets); `commands/review.md` Phase 6 (the fixed list of verdict
sections, items 1 through 12); `skills/cross-model-peer-review/SKILL.md` the
doctrine quote and the "Premature convergence" row of the hardening-rules
table.

**Pass.** R14 states repetition of a GIVEN fact corroborates nothing, in any
participant's own contribution, including its own repetition. The verdict's
fixed section list (Phase 6, items 1-12: accepted changes, refutations,
standoffs, untestable, certification failures, transmission artifacts,
unexplained withdrawals, refused context requests, provenance, promotions,
token accounting, closing note) contains no section that scores, counts, or
praises agreement on a GIVEN fact. No shipped file frames challenger agreement
with a GIVEN fact as strengthening a finding.

---

### Case 2: A refutation without a locator is rejected

**Invariant.** The respondent cannot close a finding against the challenger
by argument alone. Every non-ACCEPT verdict must point at a specific place in
the authoritative source, and a refutation must answer the falsifier as
stated, not an easier restatement of it.

**Probe.** `protocol/PROTOCOL.md` R7; `agents/respondent.md` "Evidence Rules"
and "Verdict Vocabulary"; `protocol/finding-lifecycle.md` ledger entry
template (`respondent evidence: <locator>`).

**Pass.** R7 requires positive evidence at a stable locator for a refutation,
and states absence of evidence is not a refutation. `respondent.md` repeats
this as a binding rule for the agent that actually writes verdicts
(`REFUTE`/`DISAGREE` both "carry a file:line locator"), and separately bans
answering an easier question than the falsifier asks. The ledger template has
a dedicated `respondent evidence` field, not a free-text justification field.
A version of this content that let REFUTE close on argument or plausibility
alone, with no locator field enforced, fails this case.

---

### Case 3: An unexplained withdrawal does not close a finding

**Invariant.** The challenger cannot make a finding disappear by simply
dropping it. A withdrawal only closes the finding when it names the specific
evidence that changed the challenger's mind; a withdrawal with no named
evidence leaves the finding open and is logged as a weakness of the run.

**Probe.** `protocol/finding-lifecycle.md` "Transitions" (the withdrawal
bullet); `protocol/round-prompts.md` "Challenge round (2..N)" (the WITHDRAW
line); `commands/review.md` Phase 4 step 5, the `WITHDRAW naming no evidence`
branch.

**Pass.** All three files agree: a withdrawal naming no falsifying evidence
does not close the finding, `state` stays `CHALLENGED`, and the verdict
reports it as a run weakness (`commands/review.md` Phase 6 item 7,
"Unexplained withdrawals ... regardless of its final state"). A version that
let any WITHDRAW reply close the finding, or that dropped the
unexplained-withdrawal verdict section, fails this case.

---

### Case 4: Saturation is detected and disposed of mechanically, never by discretion

**Invariant.** When a round produces no new evidence on either side and
neither side's position has changed, the finding's fate is decided by a fixed
test applied to those two facts, never by a fresh, subjective read of who is
more convincing. Saturation always removes the finding from further open
rounds immediately, without waiting for the round cap.

**Probe.** `protocol/PROTOCOL.md` R11 (the saturation clause and the
STANDOFF definition: "both substantive positions survive"); Requirement
R11's clarification that "STANDOFF is reserved for substantive survival ...
Procedural failures never produce it" (also restated in
`protocol/finding-lifecycle.md`); `protocol/finding-lifecycle.md` "Saturation
test (mechanical, run per finding per round)"; `commands/review.md` Phase 4
step 7.

**Pass.** `finding-lifecycle.md`'s saturation test is a two-input boolean
check (`new evidence since previous round = NO on both sides AND both
positions unchanged`), not a judgment call, and it fires immediately, no
waiting for the round cap. `commands/review.md` Phase 4 step 7 disposes of a
saturated finding purely by its already-recorded respondent position, with no
new evaluative step: a `NEEDS-EVIDENCE`/`DISAGREE`/no-position finding
becomes `STANDOFF` immediately; a `REFUTE` finding is instead carried forward
(marked `saturated: no further rounds`, not swept to `STANDOFF`) into
certification, because a `REFUTE` position surviving unchallenged is not
"both positions surviving" under R11's own definition of STANDOFF, and
because sweeping it to `STANDOFF` here would make the certification
transition in `finding-lifecycle.md` ("proposed RESOLVED_REFUTE ->
CHALLENGED") unreachable. **Note for the results table:** an earlier version
of this note flagged that the literal phrase "forces STANDOFF" did not hold
for every saturated finding, only for the non-REFUTE branch, because R11 and
`finding-lifecycle.md` still described saturation as producing STANDOFF
unconditionally at the time, even though `commands/review.md` Phase 4 step 7
already implemented the position-aware behavior described above. That
wording was corrected on 2026-08-11: R11 and `finding-lifecycle.md` now state
the position-aware rule directly, so the protocol text and the command's
behavior agree, and the gap this note used to document is closed. The deeper
invariant, that the disposition is fully determined by recorded flags and
never left to discretion, held for both branches throughout and is what this
case has always graded. A version that decided the REFUTE-saturation branch
by asking "does this refutation seem solid" instead of routing it
unconditionally to certification would fail this case even though it might
still literally set `STANDOFF` somewhere.

---

### Case 5: Certification is never skipped

**Invariant.** No finding that has actually been answered by the respondent
reaches the verdict without first passing through the certification step,
where the challenger checks the respondent's rendering of its own claim
against its original words.

**Probe.** `protocol/PROTOCOL.md` R12, R13; `commands/review.md` Phase 5 step
1 (the collection clause and its `RESOLVED_REFUTE` note); Phase 6's opening
line ("Compute `04-verdict.md` from `03-ledger.md` alone").

**Pass.** Phase 5 step 1 collects every `RESOLVED_ACCEPT`,
`RESOLVED_WITHDRAWN`, `STANDOFF`, and `UNTESTABLE` finding, plus every
`CHALLENGED` finding whose respondent position is `REFUTE`, before Phase 6
runs. The command states outright that nothing before Phase 5 ever assigns
`RESOLVED_REFUTE` directly, making certification the only path to that state.
The one documented exception is `TRANSMISSION_ARTIFACT`: it is excluded from
Phase 5 by name, with a stated reason (it closed in Phase 2 before the
respondent ever answered it, so there is no respondent rendering to certify
against). That is a reasoned, explicit exception for findings that never
entered the challenge/response cycle Phase 5 exists to check, not a silent
bypass of certification for findings that did. A version that let a
`CHALLENGED`/`REFUTE` finding flow straight into Phase 6 without appearing in
Phase 5's collection, or that dropped the `TRANSMISSION_ARTIFACT` exclusion's
stated rationale, fails this case.

---

### Case 6: The consent gate precedes all egress

**Invariant.** Nothing that leaves the local machine can happen before the
operator has explicitly agreed to send the packet. A capability check that
touches no network is fine before that point; a transport call is not.

**Probe.** `commands/review.md` Critical rule 2; Phase 0 step 5 (the
`peer_profiles` call); Phase 1b ("Consent gate"); every call site of
`peer_ask`/`mcp__peer-review__peer_ask` in the file.

**Pass.** The command states the rule explicitly ("No call to the `peer_ask`
transport tool may be reachable before [the consent gate]. Calling
`peer_profiles` before the gate is fine: it is a local capability check,
never network egress.") and the document's own structure matches it: `grep
-n "peer_ask" commands/review.md` finds every call site inside `## Phase 2`
or later, none inside `## Phase 0`, `## Phase 1`, or `## Phase 1b`, which
appear earlier in the file in that order. A version that moved a `peer_ask`
call site into Phase 0 or Phase 1, or that treated `peer_profiles` as
requiring consent too, fails this case (the second failure mode is a false
positive for stringency, not a stricter pass: R5 only gates the packet
transmission, not a zero-argument local file read).

---

### Case 7: `--dry-run` opens no socket

**Invariant.** Choosing `--dry-run` means the run builds the packet, shows
what would be sent, and stops, without ever making an outbound request.

**Probe.** `commands/review.md` Phase 1b ("`--dry-run`: stop here ... End the
command."); `mcp/server.py`, every use of `urllib.request`/`urlopen`.

**Pass, as executed.** NOT FULLY EXECUTED. A complete proof requires an
actual orchestrating session following `commands/review.md`'s phases with the
`peer-review` MCP server connected and observing that a `--dry-run` invocation
never calls `peer_ask`; that requires a live run this harness's environment
cannot produce (the `peer-review` MCP server is not connected in this
session, so `mcp__peer-review__peer_ask` is not even a callable tool here).
What was executed instead, cheaply, reusing the Task 6 stub-server approach:
a local HTTP stub stood up on `127.0.0.1`, `server.py` loaded as a module
against it, and `peer_profiles()` called (the one tool Phase 0 calls before
the consent gate). Result: zero requests reached the stub, both after import
and after the `peer_profiles()` call. Static support: `grep -n
"urlopen\|urllib.request" mcp/server.py` shows every network call site inside
the body of `peer_ask`, none at import time and none inside `peer_profiles`.
Together this shows the transport layer has no way to leak a request except
through an explicit `peer_ask` call, which is the precondition Case 6's
textual ordering result depends on, but it does not itself prove an
orchestrating session honors that ordering under `--dry-run`. Treat this case
as **NOT EXECUTED** for the full claim; the supporting checks are reported
separately in the results table and should not be read as a pass.

---

### Case 8: The GIVEN -> DERIVED promotion path survives

**Invariant.** A fact the packet supplied as GIVEN is not stuck there forever.
When a participant independently reaches the authoritative source and
verifies it there, the ledger has to record that as a promotion, distinct
from mere repetition, naming who derived it and where. A future
simplification that deletes this path (for example, while "cleaning up" R14
into a flat "no corroboration" rule) fails this case.

**Probe.** `protocol/PROTOCOL.md` R14; `agents/respondent.md` "Evidence
Rules" (the R14 sub-bullets); `commands/review.md` Phase 6 item 10
("Promotions"); `skills/cross-model-peer-review/SKILL.md` doctrine quote and
glossary paragraph.

**Pass.** All four files carry the literal promotion shape `GIVEN ->
DERIVED (re-derived by <role> from <locator>)` or its ledger-recording
equivalent, not just the negative rule ("repetition doesn't count"). R14
states the promotion is recorded "with the deriving role and locator, after
which it counts." `respondent.md` gives the concrete instruction to write
`GIVEN -> DERIVED (re-derived by respondent from <locator>)` into the ledger
entry, and distinguishes it from citing the packet's own citation. Phase 6
item 10 pulls every such line into the verdict. A version that kept only the
negative half of R14 (repetition never corroborates) and dropped the
promotion path would leave a real, independently-verified fact
indistinguishable from a repeated one, and fails this case.

---

### Case 9: A digest mismatch blocks, and absent material terminates as TRANSMISSION_ARTIFACT

**Invariant.** Before anything is sent, the bytes about to leave the machine
must provably be the same bytes as the source artifact, at every hop (source
file, packet's recorded digest, packet's embedded text). Any disagreement
stops the run before transmission, not after, and is never downgraded to a
warning. Separately, once a challenge exists, a finding that attacks material
that genuinely is not in the packet cannot be treated as a normal finding: it
terminates its own way and is called out for the run to be repeated.

**Probe.** `protocol/PROTOCOL.md` R15; `commands/review.md` Phase 1 step 4
("Independent digest recheck"); Phase 2 step 6 ("Transmission-artifact
check"); Phase 6 item 6.

**Pass.** Phase 1 step 4 checks three independent recomputations (source file
on disk, the packet's recorded `bytes`/`sha256` lines, and the packet's
actually-embedded text) and states plainly: "If any pair disagrees: abort the
run before any transport call ... a mismatch is never a warning." Phase 2
step 6 sets a finding's state directly to `TRANSMISSION_ARTIFACT`, skipping
`OPEN`, when its claimed substance cannot be located anywhere in the packet,
and withholds it from the respondent in Phase 3. Phase 6 item 6 requires the
verdict to recommend the run be repeated, not trusted, for any such finding.
A version that treated a digest mismatch as advisory, or that let a
transmission-artifact finding proceed to the respondent as an ordinary
finding, fails this case.

---

### Case 10: A substantiated MISREPRESENTED reverts the finding, never converts it to STANDOFF or leaves it refuted

**Invariant.** If the challenger proves, at certification, that the
respondent's rendering of its claim does not match what it actually said,
that is treated as the respondent's procedural failure, not as new grounds
for a draw and not as grounds to let the refutation stand anyway. The finding
goes back to open debate (one corrective round if the budget allows, else a
dedicated failure state), and a misrepresentation can never manufacture a
standoff.

**Probe.** `protocol/PROTOCOL.md` R12 (the substantiated-flag sentence, and
"A misrepresentation never manufactures a standoff"); `protocol/finding-lifecycle.md`
"Transitions" (the `proposed RESOLVED_REFUTE -> CHALLENGED` line) and the
"STANDOFF is reserved for substantive survival ... never to STANDOFF" line;
`commands/review.md` Phase 5 step 3 (`MISREPRESENTED, substantiated` branch)
and step 4 (corrective round finalization).

**Pass.** R12 states a substantiated flag "invalidates the proposed closure,
strikes the restatement, and reverts the finding to CHALLENGED", and states
outright that it "never manufactures a standoff." `finding-lifecycle.md`'s
transition table has the reversion as its own named edge
(`proposed RESOLVED_REFUTE -> CHALLENGED`) and separately states procedural
failures never route to `STANDOFF`. `commands/review.md` Phase 5 step 3
implements exactly this reversion (`state = CHALLENGED`, restatement struck),
and step 4's corrective-round finalization explicitly rules out `STANDOFF` as
an outcome, routing an unresolved corrective answer to
`CERTIFICATION_FAILED` instead, citing the same "never manufactures a
standoff" language. This is the invariant with prior history: the coordinator
reports the first implementation converted a substantiated MISREPRESENTED
straight to `STANDOFF`, caught by review and a later re-review. A version
that reintroduces that shortcut, or that lets the original `RESOLVED_REFUTE`
stand despite a substantiated flag, fails this case.

---

### Case 11: The protocol layer holds no harness or vendor vocabulary

**Invariant.** `protocol/` describes a harness-independent, provider-independent
protocol. It never names a specific tool, vendor, model family, or transport;
that is a binding concern for the plugin layer around it, not for the
protocol itself.

**Probe.** `python evals/peer-review/check_protocol_ontology.py`, run from the
repository root.

**Pass.** Exit code `0`.

---

### Case 12: The consent gate is a question, and consent is intent

**Invariant.** The gate is a dialogue turn, not a form field. It asks visibly,
so an operator can tell the run is waiting for them; and it reads the answer
for what it means, so a plain yes in any wording or language proceeds and a
plain no stops. Ambiguity is re-asked, never resolved by the implementation.

This case exists because the opposite shipped. Through peer-review 2.0.0 the
binding required a literal `yes`, and a run in another repository stalled for
hours: the operator answered `ok`, the run declined to read it as consent, and
because the gate had only printed text and ended its turn, the display was
indistinguishable from a finished run. Neither half is a wording preference.
A gate that ends the turn silently converts every slow answer into a hang, and
a gate that matches tokens converts a granted consent into a withheld one,
which is the failure mode that looks like caution and is not.

**Probe.** `commands/review.md` Critical rule 8 and Phase 1b step 3 onward;
`protocol/PROTOCOL.md` R5, third paragraph.

**Pass.** All four hold. (a) Phase 1b asks through the harness's own question
mechanism after presenting the disclosure block, rather than ending the turn on
printed text. (b) The command states that consent is read as intent and lists
affirmatives beyond `yes`, in more than one language. (c) An unclear reply is
re-asked exactly once before the run ends with consent withheld, and silence is
named as never consent. (d) R5 carries the rule in harness-independent terms,
so a second binding inherits it. A version that reintroduces a required token,
or that presents the gate as output without asking, fails. Note the two halves
are separable: making consent lenient while still ending the turn silently
still hangs, and asking visibly while still matching a token still refuses a
granted consent.

---

## Results

Run: 2026-08-11, against the working tree at commit `d9f7fc0` (branch
`master`, no relevant uncommitted changes to `plugins/peer-review/` at
probe time).

| Case | Invariant | Outcome | Notes |
|---|---|---|---|
| 1 | GIVEN agreement is never corroboration | PASS | No corroboration/agreement-scoring section anywhere in the verdict template or any shipped file |
| 2 | Refutation needs a locator | PASS | R7 plus `respondent.md` plus the ledger template all require a locator; no argument-only closure path exists |
| 3 | Unexplained withdrawal never closes | PASS | Consistent across `finding-lifecycle.md`, `round-prompts.md`, and `commands/review.md` Phase 4 step 5 |
| 4 | Saturation is mechanical, not discretionary | PASS | Disposition is fully determined by recorded flags in both branches; the literal word "STANDOFF" applies only to the non-REFUTE branch, by design (see Case 4's Pass note). R11 and `finding-lifecycle.md` were corrected 2026-08-11 to state the REFUTE branch directly, closing the wording/behavior gap this note used to flag |
| 5 | Certification is never skipped | PASS | One documented, reasoned exception (`TRANSMISSION_ARTIFACT`, which never reaches a respondent verdict); no undocumented bypass found |
| 6 | Consent gate precedes all egress | PASS | Textual ordering confirmed: every `peer_ask` call site is at or after `## Phase 2`, none in Phase 0/1/1b |
| 7 | `--dry-run` opens no socket | NOT EXECUTED (full claim) | Full claim needs a live orchestrating run with the MCP server connected, unavailable in this environment. Supporting check executed and passed: importing `server.py` and calling `peer_profiles()` against a local stub server produced zero requests; every network call site in `server.py` is inside `peer_ask`'s body |
| 8 | GIVEN -> DERIVED promotion path survives | PASS | Promotion shape and its ledger-recording instruction present in protocol, agent, and command layers, not just the negative half of R14 |
| 9 | Digest mismatch blocks; absent material terminates TRANSMISSION_ARTIFACT | PASS | Phase 1 step 4's three-way digest check aborts before transport; Phase 2 step 6 routes unlocatable substance straight to `TRANSMISSION_ARTIFACT` before the respondent sees it |
| 10 | Substantiated MISREPRESENTED reverts, never STANDOFF | PASS | Reversion path and the STANDOFF exclusion both explicit at the protocol, lifecycle, and command layers |
| 11 | Protocol layer ontology clean | PASS | `python evals/peer-review/check_protocol_ontology.py` exits 0: "protocol layer clean (4 files)" |

**Summary: 10 pass, 0 fail, 1 not executed (Case 7, full claim; its cheap
supporting check passed).**

No case found a real gap in the shipped plugin. Case 4 and Case 5 both
surfaced a documented, reasoned exception to the invariant's literal wording
(the REFUTE-saturation branch, and the `TRANSMISSION_ARTIFACT` certification
exclusion); both are treated as passes because the underlying philosophy the
invariant protects (no discretionary shortcut, no undocumented bypass) holds
in each case, and both exceptions are stated in the shipped content with a
reason rather than silently present. Case 7 is the one open item: it needs an
actual `/peer-review:review --dry-run` run, with the MCP server connected and
a real challenger profile configured, to close out as a full pass rather than
a supported-but-unproven claim.

## Acceptance run: status 2026-08-11

The plugin shipped and its CI is green, but the end-to-end acceptance defined
in the implementation plan is **not complete**, and nothing below should be
read as if it were. What was executed, and what was not:

**Executed and passing, verified directly against the shipped server:**

- MCP handshake. `uv run --script plugins/peer-review/mcp/server.py` over
  stdio: `initialize` returns `serverInfo.name = peer-review`, and
  `tools/list` returns exactly `peer_ask` and `peer_profiles`.
- The Phase 0 availability gate. With a profile whose `api_key_env` names an
  unset variable, `peer_profiles()` reports `available: false` and names the
  variable, `peer_ask` returns `api key environment variable 'OPENAI_API_KEY'
  is not set; refusing to send` without issuing a request, and no key value
  appears anywhere in either payload.
- Everything in the Results table above, on shipped content.

**Not executed, and why:**

- The `--dry-run` packet build, the real end-to-end deliberation, and the
  portability smoke test all require two things this environment lacks: a
  challenger API key, and an editing session started after the plugin was
  registered, so that its MCP server is actually connected. The plugin was
  registered mid-session, so `/peer-review:review` was not invokable in the
  session that built it.

**To finish the acceptance**, in a session started after installing or
updating the plugin, with a key exported:

1. Copy `plugins/peer-review/mcp/profiles.example.json` to
   `~/.peer-review/profiles.json` and export the key its `api_key_env` names.
2. Confirm the transport is live: `claude mcp list` should show the
   `peer-review` server connected.
3. Dry run first, against a profile whose `base_url` points at an unreachable
   host, to prove no call precedes consent:
   `/peer-review:review docs/superpowers/plans/2026-08-11-cross-model-peer-review.md --dry-run`
   Expected: a complete `00-packet.md` with all nine sections and the digest
   recorded, and zero network calls. This closes Case 7.
4. Real run, same artifact, real challenger, default rounds. Success is not
   that the challenger found something. It is that at least one finding
   reaches a terminal state through cited evidence on both sides, and that
   `04-verdict.md` presents either a real standoff or a documented genuine
   convergence.
5. Portability smoke test, one call: send `protocol/PROTOCOL.md` plus the
   Round 1 prompt as the system message and the packet as the user message,
   with no harness context at all, and confirm the reply executes the
   challenger role from the protocol text alone. If it cannot, the protocol
   layer is not portable and the protocol text is what to fix, not the prompt.

Append the outcome here when it runs.
