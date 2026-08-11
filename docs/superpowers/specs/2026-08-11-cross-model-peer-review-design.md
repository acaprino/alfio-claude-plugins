# peer-review: a harness-agnostic deliberation protocol, hosted by Claude Code

Date: 2026-08-11
Plugin: `peer-review` (new)
Status: frozen. Implementation plan at `docs/superpowers/plans/2026-08-11-cross-model-peer-review.md`

## Context

Taking an execution plan and handing it to a different model family with a minimal amount of context produces critique that a same-family reviewer does not produce. The value is not the first critique: it is the exchange. The second round is where the challenger stops emitting generic advice and where the respondent stops conceding out of politeness.

This repo already carries the doctrine that explains why this works. The `epistemic-independence` spec (`docs/superpowers/specs/2026-08-10-review-pipeline-epistemic-independence-design.md`) established the shared-context provenance rule: N reviewers agreeing on a premise they were all given is one observation, not N. That work made review independent *inside* one pipeline. It could not solve the deeper case, because every reviewer in that pipeline shares weights, priors, and blind spots.

Four rounds of the manual version of this workflow were run on this document while it was being written, using GPT-5.6 as challenger. They produced:

- a state-machine correction (the first draft confused a respondent judgment with a debate outcome),
- a mechanical saturation test for termination,
- a softened doctrine claim (decorrelated errors, not absolute independence),
- an adversarial pass on the protocol itself, now the `Hardening` section,
- the structural correction that the protocol was conceptually cross-model but ontologically Claude-centric,
- provenance split into four separately recorded axes instead of one word,
- R14 restated as a rule about the act of repeating rather than about the fact, which opens the `GIVEN -> DERIVED` promotion path,
- a sixth failure mode the runs found in themselves: two of the first three rounds produced a finding about a degraded rendering of the document rather than about the document, which is now R15 and the transmission fidelity rule,
- and the round-4 precision pass: the packet-only limitation narrowed to source-fact promotion, model-provenance decorrelation scoped to model-based pairs, certification's `MISREPRESENTED` re-typed as procedural invalidation instead of a manufactured standoff, and R15 bounded to source-to-request fidelity.

**The protocol is the product. The harness is an integration.** That is the extension of the boundary already chosen for the transport layer, and it is what this design encodes.

Scope: plans and specs (intent artifacts). Not diffs, not agent prompts. Code review already has `/senior-review:code-review`.

The deliverable is not a review. It is a reduction in decisional uncertainty. Twelve findings destroyed with evidence is a success. One finding that changes an architectural decision is a success. Nobody changing their mind but a precise, informed standoff surfacing for the user to settle is a success. Finding count is never a quality measure.

## Three levels

```
1. PROTOCOL          harness-independent, provider-independent
                     roles, packet contract, evidence rules, falsifiers,
                     rounds, convergence, standoff, verdict, GIVEN vs DERIVED
                              |
2. HARNESS BINDING   this plugin: commands, agents, skills, Read/Grep/Bash,
                     MCP wiring, run directory
                              |
3. TRANSPORT         OpenAI-compatible endpoint via the MCP server
```

Level 1 never names a tool, a vendor, or a model. Level 2 states how each protocol requirement is met here. Level 3 is plumbing that knows `endpoint, auth, request, response, retry, limits` and nothing else.

### Roles, not vendors

- **artifact**: the plan or spec on trial. The protocol judges the artifact, never its author, so the **proposer is out of scope**: it may be a model, a person, or a document written months ago. A run therefore works unchanged on a plan this session did not write.
- **packet builder**: constructs the challenge packet.
- **challenger**: attacks the artifact. Sees only the packet.
- **respondent**: answers with evidence from the authoritative source.

The independence requirement is stated over roles, and provenance is recorded on four axes that are never collapsed into one word and never scored, because a composite number invites optimizing the number instead of the independence:

```
challenger:                          respondent:
  model provenance:   OpenAI GPT-5.6   model provenance:   Anthropic Opus 5
  runtime provenance: remote API       runtime provenance: Claude Code
  context provenance: packet-only      context provenance: repository + conversation
  human provenance:   none             human provenance:   none
```

When challenger and respondent are both model-based, decorrelation SHOULD hold on model provenance at minimum; when one participant is human, that axis is simply absent and the requirement falls on the remaining axes. Runtime decorrelation over an identical model family adds very little epistemic independence, and stating the axes separately is what makes that visible instead of hiding it behind "different participants". Context provenance carries a consequence used below: a `packet-only` participant can still derive plenty from the artifact itself (contradictions, failure scenarios, logical consequences), but it has no independent path to the authoritative source, so it can never promote a GIVEN source fact to DERIVED, and its agreement with GIVEN facts is repetition by construction.

In this implementation the respondent is the hosting session and the challenger is a transport profile. Nothing in the protocol fixes that assignment.

## Architecture

```
plugins/peer-review/
  protocol/                        LEVEL 1, harness-independent, no tool vocabulary
    PROTOCOL.md                    numbered normative requirements R1..R15
    packet-anatomy.md
    finding-lifecycle.md
    round-prompts.md               challenger prompts, role vocabulary only
  bindings/
    claude-code.md                 LEVEL 2, one line per requirement: how it is met here
  commands/
    peer-review.md                 /peer-review:review
  agents/
    packet-builder.md
    respondent.md
  skills/
    cross-model-peer-review/
      SKILL.md                     doctrine, when not to run one, pointer to protocol/
  mcp/
    server.py                      LEVEL 3, PEP 723 deps, `uv run --script`
    profiles.example.json
  .mcp.json
  README.md
```

`protocol/` is the portable core. A future integration copies or references it; nothing in it may be edited to suit a harness. Reads use `${CLAUDE_PLUGIN_ROOT}/protocol/...` so the bundled-path linter passes.

### Transport

Two MCP tools, both stateless. Run state lives in the run directory as markdown, so a run is resumable, greppable, and diffable.

- `peer_profiles()` returns configured profiles with availability, never a key.
- `peer_ask(profile, system, messages[], max_output_tokens?, temperature?)` posts to `{base_url}/chat/completions`, returns `{text, usage, model, latency_ms}`.

Server invariants, each testable: refuses to send when `api_key_env` is unset (naming the variable), redacts the key from every error and log path, hard payload cap (default 400 KB), timeout plus one backoff retry on 429 and 5xx with no retry on 4xx, no telemetry, no disk writes.

Profiles resolve `$PEER_REVIEW_PROFILES`, then `./.peer-review/profiles.json`, then `~/.peer-review/profiles.json`, and store `api_key_env` rather than a key:

```json
{
  "default": "gpt",
  "profiles": {
    "gpt": { "base_url": "https://api.openai.com/v1", "model": "gpt-5.6",
             "api_key_env": "OPENAI_API_KEY", "max_output_tokens": 8000 }
  }
}
```

## The protocol

`/peer-review:review <path>` with `--challenger=<profile>`, `--rounds=N` (default 3 challenger turns plus certification), `--dry-run`, `--apply`. Run directory `.peer-review/YYYY-MM-DD-HHMM-<slug>/`.

**Phase 1, packet** (packet builder) writes `00-packet.md`, immutable once sent:

1. `## Mandate` what to judge, what to leave alone
2. `## Artifact` verbatim, with its byte length and content digest recorded for the fidelity check
3. `## Ground truth (given)` source facts with locators, each flagged GIVEN
4. `## Constraints` conventions and non-negotiables
5. `## Considered and rejected` each entry split into `decision` (GIVEN) and `rationale` (TO JUDGE)
6. `## Known weaknesses of this artifact` written against its own side
7. `## Open questions` where the artifact is genuinely unsure
8. `## Out of scope`
9. `## Response contract`

**Phase 1b, consent gate.** The packet is the complete set of bytes leaving the local environment. The command prints size, section list, destination endpoint and model, and waits for an explicit yes. `--dry-run` builds the packet and stops without opening a socket.

**Phase 2, challenge round 1** writes `01-challenge-r1.md`. Required sections in order: `## Frame challenge` (is the mandate the right question, is the decomposition natural, which rejection rationale fails) before any finding; `## Context requests` by locator; `## Findings` capped at 12, each `[ID] claim | section attacked | failure scenario | severity | falsifier`; `## Cannot assess`; `## Strongest objection`. Banned: praise, restating the artifact, generic advice.

**Phase 2b, context amendment.** Requested material inside the repository is supplied verbatim, capped (default 10 files, 200 KB). Every refusal is recorded with its reason and surfaces in the verdict, so omission becomes a visible event instead of a silence.

**Phase 3, response** (respondent) writes `02-response.md`. Per finding: `ACCEPT`, `REFUTE`, `NEEDS-EVIDENCE`, `DISAGREE`. Before investigating, each falsifier gets an admissibility check: checkable against the authoritative source, decidable in bounded effort, actually dispositive. Rules:

- A refutation needs positive evidence at a stable locator. Absence of evidence is not a refutation, because absence and contradiction are different states.
- The refutation must satisfy the falsifier as stated, not a weaker restatement of it.
- No concession without verification, no defensiveness either. Cite or concede.

**Phase 4, challenge rounds.** Only still-open findings go back, each carrying the respondent's evidence. This keeps the debate anchored to real controversies and prevents drift. A withdrawal must name the evidence that falsified it; an unexplained withdrawal does not close a finding.

**Phase 5, certification.** One short challenger turn: it sees the proposed terminal state of its own findings and may flag `MISREPRESENTED`, quoting its original text against the respondent's rendering. A substantiated flag is a procedural failure of the refutation, not evidence that both substantive positions survive: it invalidates the proposed closure, strikes the restatement, and reverts the finding to `CHALLENGED`. If the round budget allows, one corrective round runs on the reverted finding against the original claim; otherwise it terminates as `CERTIFICATION_FAILED`, which is neither accepted nor refuted and is reported separately. A misrepresentation never manufactures a standoff. An unsubstantiated flag is discarded, which stops the mechanism from becoming a veto.

**Phase 6, verdict.** `04-verdict.md` is computed from the ledger, never written freehand; prose may explain a state, never change it. Sections: accepted changes as concrete edits, refutations with evidence, standoffs (one line per side plus what would settle it), untestable findings, unexplained withdrawals reported as a weakness of the run, transmission artifacts with the digest check that caught them, certification failures, packet blind spots from `Cannot assess`, refused context requests, the four-axis provenance block for each role, any `GIVEN -> DERIVED` promotions, token accounting.

`--apply` edits the artifact with the accepted changes and appends a `## Peer review <date>` changelog pointing at the run directory.

### The ledger

`03-ledger.md` is the run state. One entry per finding, carried by ID with its **original text verbatim** for the whole run:

```
Finding F03
  claim (verbatim, never paraphrased)
  falsifier (verbatim) | admissibility: OK | RESTATED | INADMISSIBLE
  challenger evidence
  respondent position | respondent evidence (locator)
  restatements: none | RESTATED AS "..." confirmed by challenger in R2
  state: OPEN | CHALLENGED | RESOLVED_ACCEPT | RESOLVED_REFUTE
       | RESOLVED_WITHDRAWN | STANDOFF | UNTESTABLE
       | TRANSMISSION_ARTIFACT | CERTIFICATION_FAILED
  new evidence since previous round: YES | NO
```

`STANDOFF` means exactly one thing: both substantive positions survive the evidence available at termination. Procedural failures never produce it, which is why `TRANSMISSION_ARTIFACT` and `CERTIFICATION_FAILED` exist as separate terminal states.

Termination is mechanical, not felt: all findings terminal; or **evidence saturation**, where the same claim, same evidence, and same positions across a round set `STANDOFF` for that finding immediately, because models are very good at producing new words without new information; or round cap, where remaining findings become `STANDOFF` labeled as cap-terminated so a reader can tell the difference. A run with findings can never terminate at round 1, since the challenge round is the mechanism that produces the value.

## Hardening

Six failure modes, each with the rule it produces. None may be optimized away later without replacing the property it protects.

**Anchoring.** The packet frames the problem in the artifact author's ontology, so the deepest error (wrong decomposition, wrong problem) has no slot to land in, and `Considered and rejected` suppresses legitimate reopening along with the noise it exists to kill. Rules: rejection rationale is TO JUDGE while the decision is GIVEN, and `## Frame challenge` precedes the findings so they do not anchor the challenger further.

**Strategic packet omission.** The packet is built by the side whose artifact is on trial. Even with no intent, what the builder considers irrelevant correlates exactly with its blind spots, and neither party can see the gap. Rules: material named by the artifact enters by mechanical extraction (judgment controls how much of each file, never which files), the builder owes `## Known weaknesses` against its own side, and the challenger pulls context by locator in phase 2b with every refusal recorded. Control over context is inverted toward the party that lacks it.

**False falsifiers.** The falsifier requirement is the strongest idea in the protocol and it is gameable in both directions: an unfalsifiable falsifier makes a finding immortal, a weak one lets the respondent manufacture a refutation. Rules: admissibility check before investigation, one restatement round, then `UNTESTABLE` as a terminal state that is neither accepted nor refuted and is reported separately.

**Debate laundering.** The process can produce the appearance of adjudication: paraphrase drifts toward a weaker claim that is easier to refute, the arguing party self-scores the outcome, and three rounds read as scrutiny regardless of content. Rules: verbatim carry through the ledger, `RESTATED AS` labels the challenger must confirm before a restatement can support a refutation, a verdict computed from the ledger, and a certification turn where the challenger has the last word on its own findings.

**Premature convergence.** Models are agreeable, and locator citations look authoritative even when they do not support the claim. Rules: a withdrawal must name the falsifying evidence or the finding stays open, unexplained convergence is reported as a weakness of the run, saturation handles mutual exhaustion mechanically, and round 1 cannot be terminal.

**Transmission fidelity.** The challenger judges the packet, never the artifact. If the rendering degrades in transit (truncation, duplication, reordering, a stale copy), findings about the rendering are indistinguishable from findings about the content, and both sides can spend a full round adjudicating something that does not exist. This was found empirically: the manual runs of this protocol on this very document produced such a finding twice in the first three rounds. Rules: the packet records the artifact's byte length and content digest, the verdict verifies **source-to-request fidelity** (source file, packet embedding, and locally constructed request are byte-identical; what the remote model internally perceived is unverifiable by construction, so the guarantee deliberately stops at the request boundary), and a finding attacking material absent from the source terminates as `TRANSMISSION_ARTIFACT`, which is neither accepted nor refuted and is reported separately so the run is repeated rather than trusted.

Budget shape, so nobody trims the wrong turn later: one large challenger call, one small one per challenge round over open findings only, one tiny certification call, and at most one corrective round when certification invalidates a proposed closure. Three to five calls typical. The expensive work is local, because it is the respondent inspecting source.

## Doctrine

Cross-family independence is the **strongest practical model-level independence available in this workflow**, not absolute independence. Two frontier models still share an internet-scale corpus, software conventions, and reasoning patterns. What makes the second participant worth its cost is that its errors are sufficiently **decorrelated**, not that it is a clean-room observer.

That independence is bounded from inside as well: **repeating a GIVEN fact is never independent corroboration within that participant's contribution.** The rule is about the act, not about the fact. A GIVEN fact is not permanently unconfirmable: a participant that reaches the authoritative source independently and verifies it there has genuinely derived it, and the ledger records the promotion `GIVEN -> DERIVED (re-derived by <role> from <locator>)`, after which it counts. What never counts is agreement produced by reading the packet back.

This matters practically because of the context provenance axis: a `packet-only` participant has no path to promotion by construction, so every agreement it offers on a GIVEN fact is repetition, while a participant with source access can convert one into evidence. Stating the rule as a prohibition on facts would have made the second case impossible and pushed future implementations toward a rigidity the doctrine never intended.

This is the shared-artifact rule from the epistemic-independence spec applied across participants instead of across reviewers, and it holds for any harness and any provider.

Both statements live in `protocol/PROTOCOL.md`, are restated in `skills/cross-model-peer-review/SKILL.md`, and are cross-referenced from `senior-review:review-quality-gates`.

## Non-goals

Deliberate, and not to be revisited without a second real harness in hand:

- No standalone CLI, no `orchestrator/`, no `providers/` package. The transport stays one MCP server.
- No participant adapter interfaces, no capability configuration schema, no evidence resolver abstraction. Abstraction lives in the requirement text, not in speculative Python.
- No `integrations/` directory until a second harness is actually attempted.
- Only the `review` workflow. Not `compare`, `deliberate`, or `adjudicate`.
- No arbiter role.
- No harness-side generalization of the respondent's inspection mechanism. R8 states the requirement; Claude Code satisfies it with Read, Grep, and Bash.

## Implementation tasks

1. **`protocol/PROTOCOL.md` first.** Fifteen numbered normative requirements, written in role vocabulary with no tool, vendor, or model names: R1 roles and the out-of-scope proposer, R2 artifact immutability, R3 packet contract, R4 four-axis provenance recorded per role, with model-provenance decorrelation required when both participants are model-based, R5 egress consent over the complete packet, R6 challenge contract, R7 positive-evidence rule, R8 respondent inspection requirement with harness-specific mechanism, R9 falsifier admissibility, R10 verbatim carry and restatement confirmation, R11 saturation and termination, R12 certification with the procedural invalidation path (revert to `CHALLENGED`, corrective round or `CERTIFICATION_FAILED`), R13 ledger-computed verdict, R14 repeating a GIVEN is never independent corroboration, with the `GIVEN -> DERIVED` promotion path, R15 source-to-request transmission fidelity via digest and the `TRANSMISSION_ARTIFACT` terminal state.
2. **`protocol/finding-lifecycle.md`**, since the command, both agents, and the verdict all encode it: states, transitions, admissibility, saturation, certification, ledger format.
3. **`protocol/packet-anatomy.md`** and **`protocol/round-prompts.md`** (critique, challenge, certification), versioned so a prompt change is visible in git.
4. **`bindings/claude-code.md`**: one line per requirement stating the concrete mechanism here. This file is where harness vocabulary is allowed to appear.
5. **Verify the plugin MCP declaration.** No plugin in this repo ships one and no `plugin.json` exists anywhere, since everything is declared in `marketplace.json`. Confirm the exact key (`mcpServers` in the marketplace entry pointing at `./.mcp.json`, versus a plugin-root `.mcp.json` picked up automatically) and how `${CLAUDE_PLUGIN_ROOT}` resolves inside it, against the installed Claude Code version. Document the manual user-level fallback in the README.
6. **Server.** `mcp/server.py` with PEP 723 metadata (`dependencies = ["mcp"]`), the two tools, every invariant above. `uv` is on PATH and Python is 3.13, so `uv run --script` needs no install step from the user.
7. **Stub test.** A throwaway OpenAI-compatible stub in the scratchpad, never in the repo, verifying request shape, auth header, retry, size cap, and key redaction without spending tokens.
8. **Agents.** `packet-builder.md` (mechanical extraction, GIVEN and TO JUDGE split, `Known weaknesses` duty) and `respondent.md` (admissibility, positive evidence, anti-capitulation). Reference `superpowers:receiving-code-review` unconditionally, per the house rule.
9. **Command.** `commands/peer-review.md`: phases 0 to 6, consent gate, context amendment, termination, run directory layout.
10. **Skill.** `SKILL.md`: the doctrine, the six hardening rules and what each protects, the harness-independence statement, and when not to run a review (artifact too vague to attack, or a decision already made for reasons outside the artifact).
11. **Marketplace.** New entry `peer-review` at 1.0.0, category `review`, `dependencies: ["superpowers@claude-plugins-official"]` in qualified form, plus the `mcpServers` field from task 5. Bump `metadata.version` to the next minor available at commit time (19.2.0 was taken by the epistemic-independence ship on 2026-08-11; check before staging, since several sessions run this repo at once).
12. **Exports.** Mirror the prompt and skill layer into `exports/vscode/peer-review/.github/`, regenerate the extension manifest, bump `exports/vscode/package.json`. Decision to settle in this task: Copilot supports MCP through `.vscode/mcp.json`, so either ship that snippet in the bundle README or state that the transport is Claude Code only. The `protocol/` directory travels with the bundle either way, which is the first real test of its portability.
13. **CI.** All six checks: dependency graph, bundled paths (`.mcp.json`, command, and agents must use `${CLAUDE_PLUGIN_ROOT}`, never `plugins/peer-review/...`), plugin registration (every agent, skill, and command file declared in the marketplace entry, since an undeclared file does not exist at runtime), export checker, manifest check, version bumps.
14. **Behavioral-invariant eval** (separable, last), following `evals/ai-tooling/`: agreement on a GIVEN fact never scores as corroboration; a refutation without a locator is rejected; a withdrawal without named evidence does not close a finding; identical evidence across a round forces `STANDOFF`; certification and consent gate are never skipped; a substantiated `MISREPRESENTED` reverts the finding instead of closing it as refuted or converting it to a standoff; `--dry-run` never opens a socket; a fact re-derived from the authoritative source *does* count, so the promotion path cannot be removed by a later simplification; a digest mismatch blocks the verdict; and a mechanical **ontology-leak check** asserting that no file under `protocol/` contains harness or vendor vocabulary.

## Verification

- Handshake: `uv run --script plugins/peer-review/mcp/server.py` initializes over stdio and lists exactly two tools.
- Stub: every server invariant, including that a missing `OPENAI_API_KEY` produces a named error and no request.
- `--dry-run` against an unreachable host still produces a complete `00-packet.md`, proving no network call precedes consent.
- Protocol dry runs against a scripted stub challenger, no real tokens: an unexplained withdrawal leaves the finding open, a repeated position triggers saturation, a quoted `MISREPRESENTED` flag reverts the finding to `CHALLENGED` (corrective round if budget remains, `CERTIFICATION_FAILED` otherwise) while an unsubstantiated one is discarded, and an inadmissible falsifier terminates as `UNTESTABLE`.
- Real end-to-end run against the frozen epistemic-independence plan (`docs/superpowers/plans/2026-08-10-review-pipeline-epistemic-independence.md`), which is long, opinionated, and already peer reviewed once. Success is not that the challenger found something: it is that at least one finding reaches a terminal state through cited evidence on both sides, and that `04-verdict.md` presents either a real standoff or a documented genuine convergence.
- Portability smoke test, cheap and revealing: hand `protocol/PROTOCOL.md` plus a packet to the challenger with no harness context and confirm it can execute its role from the protocol text alone.
- The six CI checks pass from the repo root.
