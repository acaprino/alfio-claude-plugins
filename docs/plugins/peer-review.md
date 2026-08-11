# Peer Review Plugin

> Cross-model peer review of a plan or a spec, never a diff: a challenger model on a different model family attacks your artifact, the local session refutes with repository evidence, and the exchange terminates in a verdict computed from a verbatim ledger. The deliverable is not a review score; it is a reduction in decisional uncertainty.

## Prerequisites

`superpowers@claude-plugins-official` is a hard, qualified dependency (the `respondent` agent loads `superpowers:receiving-code-review` and stops if it is unavailable):

```bash
claude plugin install superpowers@claude-plugins-official
```

Beyond that, the plugin needs `uv` on PATH, Python 3.11 or later, and one API key for an OpenAI-compatible endpoint (OpenAI, OpenRouter, or a local server answering the same `chat/completions` shape).

## Setup

Three steps: install the plugin, write a profiles file, export the key it names.

**1. Install.** The MCP server needs no registration of its own:

```bash
claude plugin install peer-review@claude-code-daodan
```

The plugin ships a plugin-root `.mcp.json` declaring one stdio server that runs `uv run --script ${CLAUDE_PLUGIN_ROOT}/mcp/server.py`, and Claude Code auto-discovers it on install. Check `/mcp`: `peer-review` should be listed as connected. If it is not, the README's manual fallback registers the same definition at user scope with the cache path substituted for `${CLAUDE_PLUGIN_ROOT}`.

**2. Write a profiles file.** Copy the shipped `plugins/peer-review/mcp/profiles.example.json` to one of three locations. The server checks them in this order and the first file that exists wins, with no merging of the others:

| Order | Location | Scope |
|---|---|---|
| 1 | the path in `$PEER_REVIEW_PROFILES` | wherever you point it |
| 2 | `./.peer-review/profiles.json` | this project |
| 3 | `~/.peer-review/profiles.json` | this machine |

Each entry under `profiles` is a named challenger that `--challenger=<name>` selects:

```json
{
  "default": "gpt",
  "profiles": {
    "gpt": {
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-5.6",
      "api_key_env": "OPENAI_API_KEY",
      "max_output_tokens": 8000
    }
  }
}
```

| Field | Meaning |
|---|---|
| `base_url` | Endpoint root. The server appends `/chat/completions` to it |
| `model` | Model id sent in the request body. Required; a profile without it is refused at call time |
| `api_key_env` | The **name** of an environment variable, never a literal key |
| `max_output_tokens` | Optional per-profile cap, overridable per call |
| `default` (top level) | Profile used when `--challenger` is omitted |

The `api_key_env` indirection is the security boundary: the file holds a variable name, so it stays safe to commit, diff, or share. The server resolves the variable at call time, never logs or returns the key, redacts it from any error text, and sends it only in the outgoing request's `Authorization` header. Of the profile itself, only `base_url` and `model` ever reach the network.

**3. Export the key** in the environment Claude Code itself runs in, matching the variable your profile names:

```bash
export OPENAI_API_KEY=...          # bash / zsh
```
```powershell
$env:OPENAI_API_KEY = '...'        # PowerShell, current session
setx OPENAI_API_KEY "..."          # PowerShell, persisted for future sessions
```

The MCP server is a child process of Claude Code and inherits its environment at spawn time, so a variable exported in some other terminal after the session started is invisible to it. Export first, then start Claude Code, or restart the session after setting it.

**Verify.** `peer_profiles` reports one line per profile with `available: true` only when the named variable is set and non-empty, and it never returns the key itself. `/peer-review:review` checks this at its Phase 0 availability gate and stops there if the profile is unusable. A `--dry-run` exercises everything up to the consent gate without sending anything.

| Symptom | Cause |
|---|---|
| `/mcp` shows `Failed to connect` | `uv` not on PATH, or Python older than 3.11 |
| `unknown profile 'x' (known: ...)` | `--challenger` name does not match a key under `profiles` |
| `api key environment variable 'X' is not set; refusing to send` | The variable is unset in the server's inherited environment |

A failed server degrades per-server rather than breaking the install: the commands, agents, and skills keep working, and only the transport calls fail when the command reaches them.

[`plugins/peer-review/README.md`](../../plugins/peer-review/README.md) carries the same setup alongside the run output reference and the transport details.

## Usage

```
/peer-review:review <path> [--challenger=<profile>] [--rounds=N] [--dry-run] [--apply]
```

One invocation runs the whole deliberation: packet, consent gate, round 1, an optional context amendment, up to two more challenge rounds, certification, and a ledger-computed verdict. The target is a plan or a spec in markdown, never a diff and never a source file: the command inspects the path and refuses those, naming `/senior-review:code-review` as the tool for them.

### The first run, step by step

**1. Dry run first.** Nothing reaches the network:

```
/peer-review:review docs/plans/my-plan.md --challenger=gpt --dry-run
```

The command resolves the profile, checks the key is available, spawns the packet builder, and stops before the consent gate is even presented. It prints the path of the run directory it created, `.peer-review/YYYY-MM-DD-HHMM-<slug>/`.

**2. Read `00-packet.md`.** This is the whole world the challenger gets: the artifact verbatim, the ground truth mechanically extracted from the files it names, constraints, considered-and-rejected decisions, known weaknesses, open questions, out of scope, and the response contract. A disappointing run usually traces back to a thin packet rather than to a weak challenger, and this is the moment to notice that.

**3. Run it for real,** same command without `--dry-run`. The consent gate appears once, before round 1:

```
About to send this packet to an external service:
  destination: https://api.openai.com/v1  model: gpt-5.6
  size: 48213 bytes (transport cap: 400000 bytes)
  sections: Mandate, Artifact, Ground truth, Constraints, Considered and rejected,
            Known weaknesses, Open questions, Out of scope, Response contract
Nothing else leaves this machine. Send it? (yes / no)
```

Only a literal `yes` proceeds. Anything else aborts the run with the directory left on disk. That single approval covers the whole run: rounds 2 and 3, certification, a corrective round, and any repository material granted to a context request. You are not asked again.

**4. Read `04-verdict.md`.** It is the only file written for a human, and it is computed from the ledger rather than composed, so its prose can explain an outcome but never change one.

### Flags

| Flag | Effect |
|---|---|
| `--challenger=<profile>` | Profile to challenge with. Omit it to use the `default` named in `profiles.json` |
| `--rounds=N` | `2` or `3`, default `3`. A value below `2` is rejected: a run with findings can never end after round 1 |
| `--dry-run` | Build the packet, stop before the consent gate. Nothing is sent |
| `--apply` | After the verdict, apply its accepted changes to the artifact with the Edit tool and append a changelog section. Without it, the edits are printed for you to make yourself |

### What a run leaves on disk

Everything lands in the one run directory, which is git-ignored and made of plain markdown you can diff, grep, or hand to someone else:

| File | What it holds |
|---|---|
| `00-packet.md` | Everything that left your machine, exactly as the challenger saw it |
| `01-challenge-r1.md` | The frame challenge, the findings with their falsifiers, and what the challenger could not assess |
| `01b-amendment.md` | Repository material it asked for: what was granted, and every refusal with its reason |
| `02-response.md` | Your side's verdict per finding, with a locator for every non-ACCEPT |
| `05-challenge-r2.md`, `06-response-r2.md`, `07-challenge-r3.md`, `08-response-r3.md` | Later rounds, each processing only what is still open |
| `09-certification.md`, `10-corrective.md` | The challenger's last word on how its own findings were rendered, and the corrective round if a misrepresentation flag was substantiated |
| `03-ledger.md` | Run state, one entry per finding, claim and falsifier carried verbatim throughout |
| `04-verdict.md` | The outcome |

### Reading the verdict

Its first three sections carry decisions. **Accepted changes** are concrete edits. **Refutations** each cite the evidence that satisfied the finding's falsifier. **Standoffs** are the point of the exercise: one line per side plus what would settle it, a decision that is genuinely yours rather than a bug either party can close.

The sections after those describe the run's own health, and they are worth a look before trusting it. Untestable findings, certification failures, and transmission artifacts died procedurally rather than on the merits, so none of them is evidence that the artifact is sound. Unexplained withdrawals and refused context requests both point at gaps: the first at a challenger that dropped a claim without saying why, the second at material it wanted and did not get. A run with several refusals reviewed less than it appears to have.

Two habits pay off. Read `Cannot assess` in `01-challenge-r1.md`: what the challenger could not judge is a statement about your packet, not about your plan. And check the provenance block, where a challenger whose context axis reads `packet-only` has no path to the authoritative source, so its agreement with any fact you supplied is repetition rather than confirmation.

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
