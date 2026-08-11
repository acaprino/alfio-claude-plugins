# Peer Review Plugin

> Cross-model peer review of a plan or a spec, never a diff: a challenger model on a different model family attacks your artifact, the local session refutes with repository evidence, and the exchange terminates in a verdict computed from a verbatim ledger. The deliverable is not a review score; it is a reduction in decisional uncertainty.

## Prerequisites

`superpowers@claude-plugins-official` is a hard, qualified dependency (the `respondent` agent loads `superpowers:receiving-code-review` and stops if it is unavailable):

```bash
claude plugin install superpowers@claude-plugins-official
```

Beyond that, the plugin needs `uv` on PATH, Python 3.11 or later, and one API key for an OpenAI-compatible endpoint (OpenAI, OpenRouter, or a local server answering the same `chat/completions` shape). Full install and profile setup is in [`plugins/peer-review/README.md`](../../plugins/peer-review/README.md); this page covers the idea, not the setup steps.

## Three layers, kept apart

The plugin is one conforming binding of a protocol it does not own, and the layering is the point:

| Layer | What it is | Where |
|---|---|---|
| Protocol | Harness-independent, provider-independent. Fifteen numbered requirements (R1-R15), a nine-state finding lifecycle, packet anatomy, three round prompts. Names no tool, vendor, model, or transport | `plugins/peer-review/protocol/` |
| Claude Code binding | This plugin's implementation of the protocol | `commands/review.md`, `agents/packet-builder.md`, `agents/respondent.md`, `skills/cross-model-peer-review/` |
| Transport | Two stateless MCP tools, `peer_profiles` and `peer_ask`, against any OpenAI-compatible endpoint | `mcp/server.py` |

`evals/peer-review/check_protocol_ontology.py` mechanically enforces that the protocol names no concrete tool or vendor. The protocol is the product; everything else here is its Claude Code implementation.

## Agents

| Agent | Role |
|---|---|
| `packet-builder` | Builds the immutable challenge packet from the artifact: verbatim text with a byte length and content digest, mechanically extracted ground truth, and the response contract. Never argues the artifact's merits |
| `respondent` | Answers the challenger's findings with evidence from the repository (R8). Checks every falsifier for admissibility before investigating, and requires positive evidence at a locator to refute, never absence of evidence |

## Skill

`cross-model-peer-review` carries the doctrine: when a run is worth its cost, the GIVEN/TO JUDGE/DERIVED provenance vocabulary, and a table mapping six hardening rules (anchoring, strategic omission, false falsifiers, debate laundering, premature convergence, transmission fidelity) to the requirements that guard against each.

## Command

`/peer-review:review <path> [--challenger=<profile>] [--rounds=N] [--dry-run] [--apply]` runs the full deliberation: packet, consent gate, round 1, an optional context amendment, up to two more challenge rounds, certification, and a ledger-computed verdict. It refuses anything that looks like a diff or a source file; `/senior-review:code-review` is the tool for those.

## Concepts worth knowing before a run

**The packet is the challenger's whole world.** Everything it can attack traces back to what the packet builder extracted. Ground truth and constraints enter by mechanical extraction, not relevance judgment: naming a file in the artifact is what earns it a place. Considered-and-rejected alternatives are split in two: the `decision` is GIVEN (settled, not up for debate) and the `rationale` is TO JUDGE (attackable). That split is what stops the challenger relitigating a choice you already made while still letting it go after a bad reason for making it.

**Every finding carries its own falsifier**, the specific evidence that would make the challenger withdraw its claim. The respondent checks that falsifier for admissibility (decidable against the source, decidable in bounded effort, actually dispositive) before investigating at all, and a refutation must satisfy it exactly as stated, never a weaker restatement.

**Repeating a GIVEN fact is never corroboration.** Reading the packet back and calling it verification is, per the protocol's own doctrine, the single most common way a run's evidence looks stronger than it is. What does count: a participant that independently reaches the authoritative source and verifies a fact there has derived it, and the ledger records the promotion `GIVEN -> DERIVED` with the deriving role and locator. This is the cross-model arm of a rule `senior-review:review-quality-gates` states one level up for reviewers sharing context inside a single pipeline: shared context cannot independently corroborate a claim it was the source of. Same failure mode, different multiplicity; the two plugins state it independently and neither depends on the other to enforce it.

**Provenance is recorded on four axes**, model, runtime, context, human, per role, never collapsed into one label and deliberately never scored.

**Consent is given once.** A single gate before round 1 shows the destination, the packet's byte size, and its section list; only a literal `yes` proceeds. That one approval covers everything the run may later send: rounds 2 and 3, certification, a corrective round if one runs, and up to 10 files or 200 KB of repository material granted to a Phase 2b context request, tagged GIVEN. `--dry-run` builds the packet and stops before that gate is even asked, so nothing reaches the network.

**Termination is mechanical, not narrative.** Every finding ends in one of nine states:

| State | Meaning |
|---|---|
| OPEN | Raised, not yet answered |
| CHALLENGED | Answered; awaiting the challenger's reply, or a closure was invalidated |
| RESOLVED_ACCEPT | Respondent accepted; becomes a concrete edit |
| RESOLVED_REFUTE | Refuted with positive evidence satisfying the falsifier as stated |
| RESOLVED_WITHDRAWN | Challenger withdrew, naming the evidence that falsified it |
| STANDOFF | Both substantive positions survive the available evidence |
| UNTESTABLE | Falsifier inadmissible even after one restatement |
| TRANSMISSION_ARTIFACT | The finding attacks material absent from the source |
| CERTIFICATION_FAILED | A certified closure was invalidated with no round budget left to retry |

STANDOFF is reserved for genuine substantive survival; every procedural failure routes to one of the other three terminal-but-not-resolved states instead, never to STANDOFF.

**Finding count is never the quality measure.** Twelve findings destroyed with evidence is a success. One finding that changes a decision is a success. A precise, evidenced standoff left for the user to settle is a success. The deliverable is a reduction in decisional uncertainty, not a review.

## Acceptance status

The end-to-end deliberation has not been run yet: the plugin was registered mid-session while it was being built, so no session with a live, connected MCP server and a real challenger API key has driven a full `/peer-review:review` invocation. The MCP handshake and the Phase 0 availability gate were verified directly against the shipped server, and CI is green, but the real cross-model dialectic itself is unproven, not merely undocumented. Treat the plugin as shipped-but-not-yet-accepted until that run happens; the runbook to close it out is at the end of `evals/peer-review/cases.md`.

**Related:** [senior-review](senior-review.md) (diff and PR review; `review-quality-gates` states the same shared-context provenance rule for reviewers inside one pipeline)
