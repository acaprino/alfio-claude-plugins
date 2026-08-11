# Cross-Model Peer Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `peer-review` plugin: a harness-agnostic deliberation protocol (15 normative requirements), its Claude Code binding (command, two agents, skill), and a transport-only MCP server speaking to any OpenAI-compatible endpoint.

**Architecture:** Three levels with a hard boundary. `protocol/` is the portable core and never names a tool, vendor, or model. `bindings/`, `commands/`, `agents/`, `skills/` are the Claude Code integration. `mcp/server.py` is plumbing that knows endpoint, auth, request, response, retry, limits and nothing else.

**Tech Stack:** Static markdown plugin content plus one Python MCP server (official `mcp` SDK, PEP 723 inline metadata, launched via `uv run --script`, no install step). Verification is the repo's six stdlib-only CI checks, a scratchpad HTTP stub, and grep assertions.

**Source spec:** `docs/superpowers/specs/2026-08-11-cross-model-peer-review-design.md` (frozen after four manual challenger rounds)

## Global Constraints

Every task's requirements implicitly include this section.

- **No dash-aside construct anywhere**, in content, code comments, or commit messages. The ban targets wrapping a clause between dashes in any form (em dash, `--`, spaced hyphen). Rewrite into separate sentences, parentheses, or colons. Hyphenated compounds are fine. Scope checks to lines you added.
- **Stage explicit paths, never `git add -A`.** Other sessions run this repository concurrently. Diff `marketplace.json`, `exports/vscode/package.json`, and any CHANGELOG before staging.
- **Bundled paths**: every self-reference to a plugin file uses `${CLAUDE_PLUGIN_ROOT}/...` (or a skill-relative `references/...` path inside that same skill). Never `plugins/peer-review/...` in any body. No reference into another plugin's files by path.
- **The ontology rule**: no file under `plugins/peer-review/protocol/` may contain harness, vendor, model, or transport vocabulary. The mechanical checker from Task 4 is the gate. Vendor-named examples live only in `bindings/claude-code.md`.
- **Agent frontmatter**: `model: inherit`, `color` from `red, blue, green, yellow, purple, orange, pink, cyan`, `name` kebab-case matching the filename, long `description` in YAML `>` form with TRIGGER WHEN / DO NOT TRIGGER WHEN.
- **Version bumps land in Task 12 only.** `scripts/check_version_bumps.py` evaluates the whole pushed range, so one bump covers every commit in it. Read the current `metadata.version` at execution time and bump the minor: 19.2.0 was taken by the epistemic-independence ship on 2026-08-11, and other sessions may have moved it again.
- **Push once, at the end of Task 14.** Tasks 15 and 16 push separately (evals are dev assets; the acceptance run edits nothing).
- **Command file naming**: the command id derives from the filename (`code-review.md` gives `/senior-review:code-review`), so `/peer-review:review` requires `commands/review.md`. The spec's `commands/peer-review.md` spelling is superseded by this plan.

**Canonical numeric values** (the spec's defaults; cited by name, never re-decided):

| Value | Setting |
|---|---|
| Findings cap per round | 12 |
| Default rounds | 3 challenger turns, plus certification, plus at most 1 corrective round |
| Context amendment caps | 10 files, 200 KB total |
| Transport payload cap | 400000 bytes |
| Transport timeout | 180 s |
| Transport retry | exactly one, 5 s backoff, only on HTTP 429, 500, 502, 503, 504 |

**Canonical run-directory layout.** Run dir is `.peer-review/YYYY-MM-DD-HHMM-<slug>/`. Every task that reads or writes these uses exactly these names:

| File | Writer | Notes |
|---|---|---|
| `00-packet.md` | packet-builder | immutable once sent |
| `01-challenge-r1.md` | challenger via transport | |
| `01b-amendment.md` | command | granted and refused context requests |
| `02-response.md` | respondent | round 1 response |
| `03-ledger.md` | command | updated at every phase, append-only per finding |
| `04-verdict.md` | command | computed from the ledger, written last |
| `05-challenge-r2.md`, `07-challenge-r3.md` | challenger | later rounds |
| `06-response-r2.md`, `08-response-r3.md` | respondent | later rounds |
| `09-certification.md` | challenger | |
| `10-corrective.md` | both | only when certification invalidates a closure |

**Canonical vocabulary.** Finding states: `OPEN`, `CHALLENGED`, `RESOLVED_ACCEPT`, `RESOLVED_REFUTE`, `RESOLVED_WITHDRAWN`, `STANDOFF`, `UNTESTABLE`, `TRANSMISSION_ARTIFACT`, `CERTIFICATION_FAILED`. Respondent verdicts: `ACCEPT`, `REFUTE`, `NEEDS-EVIDENCE`, `DISAGREE`. Provenance axes: model, runtime, context, human. Epistemic tags: `GIVEN`, `TO JUDGE`, `DERIVED`, promotion `GIVEN -> DERIVED`. MCP tools: `peer_profiles`, `peer_ask`. Flags: `--challenger=<profile>`, `--rounds=N`, `--dry-run`, `--apply`.

---

### Task 1: `protocol/PROTOCOL.md`, the fifteen requirements

The portable core lands first because every other file cites requirement numbers.

**Files:**
- Create: `plugins/peer-review/protocol/PROTOCOL.md`

**Interfaces:**
- Produces: stable requirement identifiers `R1`..`R15`, the role vocabulary (`artifact`, `packet builder`, `challenger`, `respondent`), the epistemic tags (`GIVEN`, `TO JUDGE`, `DERIVED`), and the state list. Tasks 2 to 11 cite these by exact name.

- [ ] **Step 1: Write the file**

Write `plugins/peer-review/protocol/PROTOCOL.md` with exactly this structure and content (prose may be tightened, requirement numbers and normative sentences may not change meaning):

````markdown
# Cross-Model Peer Review Protocol

Version: 1.0.0
Status: normative. Requirement numbers are stable identifiers; binding documents cite them.

This protocol is harness-independent and provider-independent. No requirement names a
tool, a vendor, a model, or a transport. A conforming implementation supplies a binding
document stating, for each requirement, the concrete mechanism that satisfies it.

The deliverable of a run is not a review. It is a reduction in decisional uncertainty:
accepted changes, evidence-backed refutations, and precise standoffs for a human to
settle. Finding count is never a quality measure.

## Vocabulary

- **artifact**: the intent document on trial (a plan or a spec).
- **packet**: the self-contained challenge brief built from the artifact.
- **packet builder**: the role that constructs the packet.
- **challenger**: the role that attacks the artifact. It sees only the packet plus any
  granted amendments.
- **respondent**: the role that answers findings with evidence from the authoritative
  source.
- **authoritative source**: the repository or corpus the artifact is about.
- **GIVEN**: a statement supplied to a participant by the packet.
- **TO JUDGE**: a statement the packet explicitly submits for evaluation.
- **DERIVED**: a statement a participant established through its own access to the
  authoritative source.
- **ledger**: the run state carrying every finding verbatim from birth to terminal state.

## Requirements

### R1. Roles, not identities
A run has four roles: artifact, packet builder, challenger, respondent. The proposer
(whoever wrote the artifact) is out of scope: the protocol judges the artifact, never
its author. No rule may condition on which vendor, model, or person fills a role.

### R2. Artifact immutability
The artifact does not change during a run. Accepted changes are applied after the
verdict. A changed artifact means a new run.

### R3. Packet contract
The packet is immutable once sent and contains, in order: Mandate; Artifact (verbatim,
with byte length and content digest); Ground truth (source facts with locators, each
flagged GIVEN); Constraints; Considered and rejected (each entry split into a decision,
flagged GIVEN, and a rationale, flagged TO JUDGE); Known weaknesses of this artifact
(written against the builder's own side); Open questions; Out of scope; Response
contract. Material named by the artifact enters by mechanical extraction: judgment
controls how much of each source, never which sources.

### R4. Provenance, recorded on four axes
Each role's provenance is recorded on four separate axes: model, runtime, context,
human. The axes are never collapsed into one label and never scored. When challenger
and respondent are both model-based, decorrelation SHOULD hold on the model axis at
minimum; when a role is filled by a human, the model axis is absent and the requirement
falls on the remaining axes. A participant whose context axis is packet-only can still
derive consequences from the artifact, but it has no independent path to the
authoritative source and therefore can never promote a GIVEN source fact to DERIVED.

### R5. Egress consent
The packet is the complete set of bytes leaving the local environment. Before any
transmission the operator is shown its size, its section list, and the destination,
and gives explicit consent. A dry-run mode MUST exist that builds the packet and stops
without any transmission.

### R6. Challenge contract
The first challenge round contains, in order: a frame challenge (is the mandate the
right question, is the decomposition natural, which rejection rationale fails), before
any finding; context requests by locator; findings, capped, each carrying claim,
section attacked, failure scenario, severity, and falsifier; a cannot-assess section;
a strongest-objection section. Praise, restating the artifact, and generic advice are
banned.

### R7. Positive evidence
A refutation requires positive evidence at a stable locator in the authoritative
source. Absence of evidence is not a refutation: absence and contradiction are
different states. A refutation must satisfy the finding's falsifier as stated, not a
weaker restatement of it. No concession without verification; no defensiveness either.

### R8. Respondent inspection
The respondent MUST be capable of inspecting the authoritative source material needed
to evaluate the challenger's claims. The mechanism is binding-specific. A respondent
whose context axis is packet-only does not conform.

### R9. Falsifier admissibility
Before investigation, each falsifier is checked: decidable against the authoritative
source or a runnable procedure, decidable in bounded effort, and actually dispositive
for the claim. An inadmissible falsifier earns one restatement request; if still
inadmissible, the finding terminates as UNTESTABLE, which is neither accepted nor
refuted and is reported separately.

### R10. Verbatim carry
A finding's claim and falsifier travel verbatim through the ledger for the whole run.
Any restatement is labeled as such and must be confirmed by the challenger before it
can support a refutation.

### R11. Mechanical termination
A run terminates when all findings are terminal, or by evidence saturation (same
claim, same evidence, same positions across a round set STANDOFF for that finding
immediately), or at the round cap (remaining findings become STANDOFF, labeled
cap-terminated). A run with findings never terminates after the first challenge round.
STANDOFF means exactly one thing: both substantive positions survive the evidence
available at termination. Procedural failures never produce it.

### R12. Certification
Before the verdict, the challenger sees the proposed terminal state of its own
findings and may flag one as MISREPRESENTED, quoting its original text against the
respondent's rendering. A substantiated flag is a procedural failure of the
refutation: it invalidates the proposed closure, strikes the restatement, and reverts
the finding to CHALLENGED. If the round budget allows, one corrective round runs
against the original claim; otherwise the finding terminates as CERTIFICATION_FAILED,
neither accepted nor refuted, reported separately. A misrepresentation never
manufactures a standoff. An unsubstantiated flag is discarded.

### R13. Ledger-computed verdict
The verdict is computed from the ledger, never written freehand. Prose may explain a
state; it may never change one. The verdict reports, at minimum: accepted changes,
refutations with evidence, standoffs with what would settle each, untestable findings,
certification failures, transmission artifacts, unexplained withdrawals (reported as a
weakness of the run), refused context requests, the four-axis provenance of each role,
and any GIVEN -> DERIVED promotions.

### R14. Repetition of a GIVEN is never independent corroboration
Within a participant's contribution, repeating a GIVEN fact corroborates nothing. The
rule is about the act, not the fact: a participant that independently reaches the
authoritative source and verifies the fact there has derived it, and the ledger
records the promotion GIVEN -> DERIVED with the deriving role and locator, after which
it counts. Agreement produced by reading the packet back never counts.

### R15. Source-to-request transmission fidelity
The challenger judges the packet, never the artifact. The packet records the
artifact's byte length and content digest, and the verdict verifies that the source
document, the packet embedding, and the outgoing request are byte-identical. What the
remote participant internally perceived is unverifiable by construction; the guarantee
deliberately stops at the request boundary. A finding attacking material absent from
the source terminates as TRANSMISSION_ARTIFACT, neither accepted nor refuted, reported
separately so the run is repeated rather than trusted.

## Doctrine

Cross-family independence is the strongest practical model-level independence
available in this workflow, not absolute independence. Two frontier participants may
share a training corpus, conventions, and reasoning patterns. What makes a second
participant worth its cost is that its errors are sufficiently decorrelated, not that
it is a clean-room observer.
````

- [ ] **Step 2: Verify the ontology by eye (the mechanical gate arrives in Task 4)**

Run: `grep -inE "claude|anthropic|openai|gpt|gemini|copilot|codex|mcp\b|CLAUDE_PLUGIN_ROOT" plugins/peer-review/protocol/PROTOCOL.md`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add plugins/peer-review/protocol/PROTOCOL.md
git commit -m "Add the cross-model peer review protocol, R1..R15"
```

---

### Task 2: `protocol/finding-lifecycle.md`

**Files:**
- Create: `plugins/peer-review/protocol/finding-lifecycle.md`

**Interfaces:**
- Consumes: R9, R10, R11, R12 from Task 1.
- Produces: the state list, the transition table, the ledger entry template, and the saturation test. The command (Task 9) and the respondent (Task 8) encode these verbatim.

- [ ] **Step 1: Write the file**

````markdown
# Finding Lifecycle

One entry per finding, carried by ID. The claim and falsifier are verbatim for the
whole run (R10).

## States

| State | Terminal | Meaning |
|---|---|---|
| OPEN | no | raised, not yet answered |
| CHALLENGED | no | answered; the challenger has not yet replied or a closure was invalidated |
| RESOLVED_ACCEPT | yes | respondent accepted; becomes a concrete edit in the verdict |
| RESOLVED_REFUTE | yes | refuted with positive evidence satisfying the falsifier as stated |
| RESOLVED_WITHDRAWN | yes | challenger withdrew, naming the evidence that falsified it |
| STANDOFF | yes | both substantive positions survive the available evidence |
| UNTESTABLE | yes | falsifier inadmissible after one restatement (R9) |
| TRANSMISSION_ARTIFACT | yes | the finding attacks material absent from the source (R15) |
| CERTIFICATION_FAILED | yes | closure invalidated at certification, no round budget left (R12) |

STANDOFF is reserved for substantive survival. A procedural failure routes to
UNTESTABLE, TRANSMISSION_ARTIFACT, or CERTIFICATION_FAILED, never to STANDOFF.

## Transitions

- OPEN -> CHALLENGED: the respondent answers with ACCEPT, REFUTE, NEEDS-EVIDENCE, or
  DISAGREE, plus evidence at a locator for every non-ACCEPT verdict.
- CHALLENGED -> RESOLVED_*: the challenger concedes (naming the falsifying evidence)
  or the respondent accepts.
- CHALLENGED -> STANDOFF: evidence saturation, or the round cap (labeled
  cap-terminated).
- any non-terminal -> UNTESTABLE: falsifier fails admissibility twice.
- any -> TRANSMISSION_ARTIFACT: the attacked material is absent from the source at
  the recorded digest.
- proposed RESOLVED_REFUTE -> CHALLENGED: substantiated MISREPRESENTED flag at
  certification. One corrective round if budget remains, else CERTIFICATION_FAILED.
- A withdrawal that names no falsifying evidence does not close the finding: it stays
  CHALLENGED and the verdict reports the unexplained withdrawal as a run weakness.

## Saturation test (mechanical, run per finding per round)

new evidence since previous round = NO on both sides
AND both positions unchanged
=> STANDOFF now. No further rounds for this finding.

## Ledger entry template

```
Finding F<NN>
  claim (verbatim): <...>
  falsifier (verbatim): <...> | admissibility: OK | RESTATED | INADMISSIBLE
  challenger evidence: <...>
  respondent position: ACCEPT | REFUTE | NEEDS-EVIDENCE | DISAGREE
  respondent evidence: <locator>
  restatements: none | RESTATED AS "<...>" confirmed by challenger in R<N>
  state: <one of the nine states>
  new evidence since previous round: YES | NO
```
````

- [ ] **Step 2: Ontology grep**

Run: `grep -inE "claude|anthropic|openai|gpt|gemini|copilot|codex|mcp\b" plugins/peer-review/protocol/finding-lifecycle.md`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add plugins/peer-review/protocol/finding-lifecycle.md
git commit -m "Add the finding lifecycle: states, transitions, saturation, ledger"
```

---

### Task 3: `protocol/packet-anatomy.md` and `protocol/round-prompts.md`

**Files:**
- Create: `plugins/peer-review/protocol/packet-anatomy.md`
- Create: `plugins/peer-review/protocol/round-prompts.md`

**Interfaces:**
- Consumes: R3, R5, R6, R12, R15 and the vocabulary from Task 1.
- Produces: the packet section rules (consumed by packet-builder, Task 7) and the three versioned challenger prompts (consumed by the command, Task 9).

- [ ] **Step 1: Write `packet-anatomy.md`**

Nine sections in packet order. For each: what it contains, its epistemic tag, and the rule that hardens it. Include verbatim:

````markdown
# Packet Anatomy

The packet is the single unit of egress (R5) and the challenger's whole world. Build
it against these rules; the order is fixed by R3.

1. **Mandate.** What to judge and what to leave alone. One paragraph.
2. **Artifact.** Verbatim, unabridged. Record `bytes: <N>` and `sha256: <hex>`
   immediately above the embedded document (R15).
3. **Ground truth (given).** Source facts with locators, each line prefixed `GIVEN`.
   Enter facts by mechanical extraction from the material the artifact names:
   judgment controls how much of each source, never which sources.
4. **Constraints.** Conventions and non-negotiables. All `GIVEN`.
5. **Considered and rejected.** One entry per dismissed alternative:
   `decision (GIVEN):` what was dismissed; `rationale (TO JUDGE):` why. The decision
   is settled; the reasoning is attackable. This split is what lets the challenger
   reopen a bad reason without relitigating every settled choice.
6. **Known weaknesses of this artifact.** Written by the builder against its own
   side. Producing an empty section is itself a signal and must be stated as such.
7. **Open questions.** Where the artifact is genuinely unsure. This is the
   invitation to be useful.
8. **Out of scope.**
9. **Response contract.** The exact required output shape for round 1, copied from
   `round-prompts.md`.
````

- [ ] **Step 2: Write `round-prompts.md`**

Three prompts, each in its own fenced block so a change is visible in git. Verbatim content:

````markdown
# Round Prompts

Versioned challenger prompts. The transport sends these as the system message; the
packet or the round payload is the user message.

## Round 1 (critique)

```
You are the challenger in a structured peer review. You receive one packet: it is
your entire world. Facts marked GIVEN were supplied to you; repeating them proves
nothing. Entries marked TO JUDGE are yours to attack.

Respond with exactly these sections, in order:

## Frame challenge
Before any finding: is the mandate asking the right question? Is the decomposition
natural? Which rejected alternative's rationale does not hold?

## Context requests
Locators for material you need and were not given. Be specific.

## Findings
At most 12, strongest first. Each finding:
[F<NN>] claim: <one sentence, your exact words>
       section attacked: <packet section>
       failure scenario: <concrete inputs or events leading to concrete damage>
       severity: <critical | major | minor>
       falsifier: <the specific evidence that would make you withdraw this>

## Cannot assess
What the packet failed to supply, and what you would have checked with it.

## Strongest objection
The single point you would defend hardest, and why.

Banned: praise, restating the artifact, generic advice that fits any document.
```

## Challenge round (2..N)

```
You are the challenger, continuing a structured peer review. You receive only your
findings that are still open, each with the respondent's position and cited
evidence.

For each finding, exactly one:
- WITHDRAW: name the specific evidence that falsified your claim. A withdrawal
  without named evidence will not close the finding.
- MAINTAIN: state what new evidence or new argument you are adding. If you have
  neither, say "no new evidence" explicitly.
- REFINE: restate the claim more precisely. The restatement will be labeled and
  carried alongside your original words.

Do not repeat prior wording as if it were new support. Positions restated without
new evidence terminate as standoffs.
```

## Certification

```
You are the challenger. This is a certification pass, not a debate round. For each
of your findings you receive the proposed terminal state and the respondent's
rendering of your claim.

For each: CERTIFIED, or MISREPRESENTED with a quote of your original words next to
the rendering you dispute. An unsubstantiated flag will be discarded. Do not
introduce new findings or new evidence.
```
````

- [ ] **Step 3: Ontology grep over both files**

Run: `grep -inE "claude|anthropic|openai|gpt|gemini|copilot|codex|mcp\b" plugins/peer-review/protocol/packet-anatomy.md plugins/peer-review/protocol/round-prompts.md`
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add plugins/peer-review/protocol/packet-anatomy.md plugins/peer-review/protocol/round-prompts.md
git commit -m "Add packet anatomy and the three versioned round prompts"
```

---

### Task 4: The ontology-leak checker

**Files:**
- Create: `evals/peer-review/check_protocol_ontology.py`

**Interfaces:**
- Produces: `python evals/peer-review/check_protocol_ontology.py` exits 0 on a clean `protocol/` and 1 with file:line diagnostics otherwise. Task 14 runs it; eval case 11 (Task 15) cites it.

- [ ] **Step 1: Write the checker**

```python
"""Fail if the harness-independent protocol layer leaks harness, vendor, or
transport vocabulary. Stdlib only, runnable from the repo root."""
import re
import sys
from pathlib import Path

PROTOCOL_DIR = Path("plugins/peer-review/protocol")

# Case-insensitive: vendors, models, transports. Case-sensitive: tool names that
# are ordinary words in lowercase. "Read" is deliberately absent: too ambiguous
# for a mechanical check, covered by review instead.
INSENSITIVE = [
    r"\bclaude\b", r"\banthropic\b", r"\bopenai\b", r"\bgpt-?[0-9o]*\b",
    r"\bgemini\b", r"\bcopilot\b", r"\bcodex\b", r"\bmcp\b",
    r"\bchat/completions\b", r"CLAUDE_PLUGIN_ROOT",
]
SENSITIVE = [r"\bBash\b", r"\bGrep\b", r"\bGlob\b", r"\bWebFetch\b", r"\bWebSearch\b"]

def main() -> int:
    failures = []
    for path in sorted(PROTOCOL_DIR.glob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern in INSENSITIVE:
                if re.search(pattern, line, re.IGNORECASE):
                    failures.append(f"{path}:{number}: {pattern}: {line.strip()}")
            for pattern in SENSITIVE:
                if re.search(pattern, line):
                    failures.append(f"{path}:{number}: {pattern}: {line.strip()}")
    if failures:
        print("ontology leak in the protocol layer:")
        print("\n".join(failures))
        return 1
    print(f"protocol layer clean ({len(list(PROTOCOL_DIR.glob('*.md')))} files)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it and expect green**

Run: `python evals/peer-review/check_protocol_ontology.py`
Expected: `protocol layer clean (3 files)`. If it reports leaks, fix the protocol file, not the checker.

- [ ] **Step 3: Prove it can fail**

Append the line `test leak: OpenAI` to `PROTOCOL.md`, run the checker, expect exit 1 naming the line, then remove the line and re-run to green.

- [ ] **Step 4: Commit**

```bash
git add evals/peer-review/check_protocol_ontology.py
git commit -m "Add the ontology-leak checker for the protocol layer"
```

---

### Task 5: MCP declaration spike

The spec left one fact unverified: how a plugin in this marketplace declares an MCP server. Nothing here ships one yet.

**Files:**
- Create: none in the repo yet (scratchpad experiment). The result lands in Tasks 6, 10, and 12.

**Interfaces:**
- Produces: the verified declaration shape (either a plugin-root `.mcp.json` picked up automatically, or an `mcpServers` field in the marketplace entry), and the verified `${CLAUDE_PLUGIN_ROOT}` resolution inside it. Task 6 writes `.mcp.json` accordingly; Task 10 documents the fallback; Task 12 declares it.

- [ ] **Step 1: Read the current documentation**

Spawn the `claude-code-guide` agent with: "For the currently installed Claude Code version: how does a marketplace plugin declare a stdio MCP server? Is a `.mcp.json` at the plugin root picked up automatically, or must the marketplace/plugin manifest carry an `mcpServers` field? Is `${CLAUDE_PLUGIN_ROOT}` expanded inside that config? Cite the docs page."

- [ ] **Step 2: Verify empirically with a throwaway plugin**

In the scratchpad (never the repo), build a minimal marketplace containing one plugin whose `.mcp.json` declares a trivial stdio server:

```json
{
  "mcpServers": {
    "spike-echo": {
      "command": "python",
      "args": ["${CLAUDE_PLUGIN_ROOT}/echo.py"]
    }
  }
}
```

with `echo.py` printing its own path to a file on startup (so `${CLAUDE_PLUGIN_ROOT}` resolution is observable). Then: `claude plugin marketplace add <scratchpad-marketplace-dir>`, `claude plugin install <spike>@<marketplace>`, open a session, run `claude mcp list`, confirm the server appears and the path resolved into the plugin cache. Uninstall and remove the scratch marketplace afterwards.

- [ ] **Step 3: Record the outcome**

Write the verified shape and the resolution behavior into the scratchpad notes for Tasks 6, 10, and 12. If the plugin-root `.mcp.json` is NOT picked up automatically, Task 12 adds the working declaration key to the marketplace entry instead, and Task 10's README documents whichever shape proved true. No commit for this task.

---

### Task 6: The transport server

**Files:**
- Create: `plugins/peer-review/mcp/server.py`
- Create: `plugins/peer-review/mcp/profiles.example.json`
- Create: `plugins/peer-review/.mcp.json` (shape from Task 5)
- Test: scratchpad `stub_test.py` and `handshake_test.py` (never committed)

**Interfaces:**
- Produces: MCP tools `peer_profiles()` and `peer_ask(profile, system, messages, max_output_tokens?, temperature?)` returning `{text, usage, model, latency_ms}` or `{error}`. The command (Task 9) calls exactly these.

- [ ] **Step 1: Write the failing stub test**

Scratchpad `stub_test.py` (same PEP 723 header as the server so `uv run --script` resolves `mcp`): starts `http.server` on `127.0.0.1:0` with a handler that records every request (path, headers, body) into a list and replies per scenario; imports the server module by path; exercises the invariants:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp"]
# ///
import http.server, importlib.util, json, os, sys, threading
from pathlib import Path

SERVER = Path(sys.argv[1])  # path to plugins/peer-review/mcp/server.py
spec = importlib.util.spec_from_file_location("peer_server", SERVER)
peer = importlib.util.module_from_spec(spec); spec.loader.exec_module(peer)

hits, scenario = [], {"mode": "ok"}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        hits.append({"path": self.path, "auth": self.headers.get("Authorization"), "body": body})
        mode = scenario["mode"]
        if mode == "429-then-ok" and len(hits) == 1:
            self.send_response(429); self.end_headers(); return
        if mode == "http-400":
            self.send_response(400); self.end_headers()
            self.wfile.write(b'{"error":"bad request detail"}'); return
        if mode == "500-leaky":
            self.send_response(500); self.end_headers()
            self.wfile.write(f'{{"leak":"{os.environ["STUB_KEY"]}"}}'.encode()); return
        self.send_response(200)
        self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"choices": [{"message": {"content": "stub reply"}}],
                                     "usage": {"total_tokens": 5}, "model": "stub"}).encode())
    def log_message(self, *args): pass

httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{httpd.server_port}/v1"

profiles = {"default": "stub", "profiles": {"stub": {
    "base_url": base, "model": "stub-model", "api_key_env": "STUB_KEY", "max_output_tokens": 100}}}
profile_path = Path(os.environ["TEMP"]) / "peer-profiles-test.json"
profile_path.write_text(json.dumps(profiles), encoding="utf-8")
os.environ["PEER_REVIEW_PROFILES"] = str(profile_path)
peer.RETRY_BACKOFF_SECONDS = 0

failures = []
def check(name, condition):
    if not condition: failures.append(name)

# 1. unknown profile names the known ones, zero requests
r = peer.peer_ask("nope", "s", [{"role": "user", "content": "x"}])
check("unknown-profile", "unknown profile" in r.get("error", "") and "stub" in r["error"] and not hits)

# 2. missing key: named env var, zero requests
os.environ.pop("STUB_KEY", None)
r = peer.peer_ask("stub", "s", [{"role": "user", "content": "x"}])
check("missing-key", "STUB_KEY" in r.get("error", "") and not hits)

# 3. happy path: bearer auth, text extracted, usage present
os.environ["STUB_KEY"] = "sk-test-secret"
r = peer.peer_ask("stub", "sys", [{"role": "user", "content": "x"}])
check("happy", r.get("text") == "stub reply" and r["usage"]["total_tokens"] == 5
      and hits[-1]["auth"] == "Bearer sk-test-secret" and hits[-1]["path"].endswith("/chat/completions"))

# 4. one retry on 429, then success
hits.clear(); scenario["mode"] = "429-then-ok"
r = peer.peer_ask("stub", "s", [{"role": "user", "content": "x"}])
check("retry-429", r.get("text") == "stub reply" and len(hits) == 2)

# 5. no retry on 400
hits.clear(); scenario["mode"] = "http-400"
r = peer.peer_ask("stub", "s", [{"role": "user", "content": "x"}])
check("no-retry-400", "HTTP 400" in r.get("error", "") and len(hits) == 1)

# 6. payload cap: zero requests
hits.clear(); scenario["mode"] = "ok"
r = peer.peer_ask("stub", "s", [{"role": "user", "content": "x" * 500_000}])
check("payload-cap", "cap" in r.get("error", "") and not hits)

# 7. key never appears in an error path
hits.clear(); scenario["mode"] = "500-leaky"
r = peer.peer_ask("stub", "s", [{"role": "user", "content": "x"}])
check("redaction", "sk-test-secret" not in json.dumps(r))

# 8. peer_profiles: availability flag, never the key value
r = peer.peer_profiles()
check("profiles", r["profiles"][0]["available"] is True
      and "sk-test-secret" not in json.dumps(r))

print("FAIL: " + ", ".join(failures) if failures else "all 8 stub checks pass")
sys.exit(1 if failures else 0)
```

- [ ] **Step 2: Run it against the not-yet-written server, expect failure**

Run: `uv run --script <scratchpad>/stub_test.py plugins/peer-review/mcp/server.py`
Expected: FAIL (file not found).

- [ ] **Step 3: Write the server**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp"]
# ///
"""Transport-only MCP server for the peer-review plugin.

Knows endpoint, auth, request, response, retry, limits. Nothing else: no project
filesystem access, no knowledge of the deliberation protocol, no telemetry, no
disk writes. The command owns the run directory.
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from mcp.server.fastmcp import FastMCP

MAX_PAYLOAD_BYTES = 400_000
REQUEST_TIMEOUT_SECONDS = 180
RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_BACKOFF_SECONDS = 5

mcp = FastMCP("peer-review")


def _profile_locations() -> list[Path]:
    locations = []
    env_path = os.environ.get("PEER_REVIEW_PROFILES")
    if env_path:
        locations.append(Path(env_path))
    locations.append(Path.cwd() / ".peer-review" / "profiles.json")
    locations.append(Path.home() / ".peer-review" / "profiles.json")
    return locations


def _load_profiles() -> tuple[dict, str | None]:
    for path in _profile_locations():
        if path.is_file():
            with path.open(encoding="utf-8") as handle:
                return json.load(handle), str(path)
    return {"default": None, "profiles": {}}, None


def _redact(text: str, secret: str | None) -> str:
    return text.replace(secret, "<redacted>") if secret else text


@mcp.tool()
def peer_profiles() -> dict:
    """List configured challenger profiles with availability. Never returns a key."""
    config, source = _load_profiles()
    profiles = []
    for name, entry in config.get("profiles", {}).items():
        key_env = entry.get("api_key_env", "")
        profiles.append({
            "name": name,
            "base_url": entry.get("base_url", ""),
            "model": entry.get("model", ""),
            "api_key_env": key_env,
            "available": bool(key_env and os.environ.get(key_env)),
        })
    return {"default": config.get("default"), "profiles": profiles, "source": source}


@mcp.tool()
def peer_ask(
    profile: str,
    system: str,
    messages: list[dict],
    max_output_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    """Send one request to the named profile's OpenAI-compatible endpoint."""
    config, _ = _load_profiles()
    entry = config.get("profiles", {}).get(profile)
    if entry is None:
        known = ", ".join(sorted(config.get("profiles", {}))) or "none configured"
        return {"error": f"unknown profile '{profile}' (known: {known})"}
    key_env = entry.get("api_key_env", "")
    api_key = os.environ.get(key_env) if key_env else None
    if not api_key:
        return {"error": f"api key environment variable '{key_env or '<unset>'}' is not set; refusing to send"}

    payload: dict = {
        "model": entry["model"],
        "messages": [{"role": "system", "content": system}, *messages],
    }
    tokens = max_output_tokens or entry.get("max_output_tokens")
    if tokens:
        payload["max_tokens"] = tokens
    if temperature is not None:
        payload["temperature"] = temperature
    body = json.dumps(payload).encode("utf-8")
    if len(body) > MAX_PAYLOAD_BYTES:
        return {"error": f"payload is {len(body)} bytes, over the {MAX_PAYLOAD_BYTES} byte cap; not sent"}

    url = entry["base_url"].rstrip("/") + "/chat/completions"
    attempts = 0
    while True:
        attempts += 1
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode("utf-8"))
            latency_ms = int((time.monotonic() - started) * 1000)
            return {
                "text": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", entry["model"]),
                "latency_ms": latency_ms,
            }
        except urllib.error.HTTPError as error:
            detail = _redact(error.read().decode("utf-8", "replace")[:500], api_key)
            if error.code in RETRY_STATUSES and attempts == 1:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return {"error": f"HTTP {error.code} from {url}: {detail}"}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as error:
            return {"error": _redact(f"request failed: {error}", api_key)}


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Run the stub test to green**

Run: `uv run --script <scratchpad>/stub_test.py plugins/peer-review/mcp/server.py`
Expected: `all 8 stub checks pass`.

- [ ] **Step 5: Handshake test**

Scratchpad `handshake_test.py`: spawn `uv run --script plugins/peer-review/mcp/server.py` with `subprocess.Popen` (pipes on stdin/stdout), write the JSON-RPC `initialize` request then `notifications/initialized` then `tools/list`, read responses with a timeout, assert the tool names are exactly `{"peer_profiles", "peer_ask"}`, terminate the process. Run it; expected: `handshake ok, 2 tools`.

- [ ] **Step 6: Write `profiles.example.json` and `.mcp.json`**

`profiles.example.json`: the spec's example verbatim (default `gpt`, `base_url` `https://api.openai.com/v1`, `model` `gpt-5.6`, `api_key_env` `OPENAI_API_KEY`, `max_output_tokens` 8000). `.mcp.json` in the shape Task 5 verified, launching `uv run --script ${CLAUDE_PLUGIN_ROOT}/mcp/server.py`.

- [ ] **Step 7: Commit**

```bash
git add plugins/peer-review/mcp/server.py plugins/peer-review/mcp/profiles.example.json plugins/peer-review/.mcp.json
git commit -m "Add the transport-only MCP server with profiles and invariants"
```

---

### Task 7: The packet-builder agent

**Files:**
- Create: `plugins/peer-review/agents/packet-builder.md`

**Interfaces:**
- Consumes: R3, R15, `packet-anatomy.md` section list (Task 3).
- Produces: agent `peer-review:packet-builder`, spawned by the command's Phase 1, writing `00-packet.md` in the run directory it is given.

- [ ] **Step 1: Write the agent**

Frontmatter:

```yaml
---
name: packet-builder
description: >
  Builds the immutable challenge packet (00-packet.md) for a /peer-review:review run:
  the artifact verbatim with byte length and sha256 digest, GIVEN-flagged ground truth
  extracted mechanically from every file the artifact names, constraints, each
  considered-and-rejected entry split into decision (GIVEN) and rationale (TO JUDGE),
  a Known-weaknesses section written against its own side, open questions, out of
  scope, and the response contract copied from the protocol round prompts.
  TRIGGER WHEN: spawned by the /peer-review:review command during Phase 1 to construct
  the packet. DO NOT TRIGGER WHEN: invoked outside the peer-review pipeline, or the
  target is a diff or source code rather than a plan or spec.
model: inherit
color: cyan
---
```

Body (terse keyword style, house convention): Mission; Inputs (artifact path, run directory, mandate text from the command); Protocol (read `${CLAUDE_PLUGIN_ROOT}/protocol/packet-anatomy.md` and follow its nine sections in order); Mechanical extraction rule (list every file path the artifact names via grep over the artifact, include an excerpt of each; judgment sets excerpt size, never file selection; record every skipped file with its reason); Digest step, verbatim:

```
Compute and record above the embedded artifact:
bytes: $(stat -c %s <artifact>)   [or wc -c]
sha256: python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <artifact>
```

Known-weaknesses duty (write at least three genuine weaknesses or state explicitly that none could be named, which the verdict reports as a signal); Self-check list (all nine sections present, every ground-truth line carries GIVEN and a locator, every rejected entry split, digest present); Output contract (write `00-packet.md`, report byte size and section list back to the command, edit nothing else).

- [ ] **Step 2: Verify frontmatter and paths**

Run: `grep -n "CLAUDE_PLUGIN_ROOT" plugins/peer-review/agents/packet-builder.md` (expect the protocol read); `grep -n "plugins/peer-review" plugins/peer-review/agents/packet-builder.md` (expect no output).

- [ ] **Step 3: Commit**

```bash
git add plugins/peer-review/agents/packet-builder.md
git commit -m "Add the packet-builder agent"
```

---

### Task 8: The respondent agent

**Files:**
- Create: `plugins/peer-review/agents/respondent.md`

**Interfaces:**
- Consumes: R7, R8, R9, R14, `finding-lifecycle.md` verdicts and ledger template (Task 2).
- Produces: agent `peer-review:respondent`, spawned by the command's Phase 3 and each later response phase, writing `02-response.md` / `06-response-r2.md` / `08-response-r3.md`.

- [ ] **Step 1: Write the agent**

Frontmatter:

```yaml
---
name: respondent
description: >
  Answers challenger findings in a /peer-review:review run with evidence from the
  repository. Checks each falsifier for admissibility before investigating, then
  verdicts every finding ACCEPT, REFUTE, NEEDS-EVIDENCE, or DISAGREE with a file:line
  locator for every non-ACCEPT verdict. A refutation must satisfy the falsifier as
  stated; absence of evidence is never a refutation; no concession without
  verification and no defensiveness either.
  TRIGGER WHEN: spawned by the /peer-review:review command during a response phase
  with a challenge file and a ledger to update. DO NOT TRIGGER WHEN: invoked outside
  the peer-review pipeline, or asked to judge code diffs (senior-review owns those).
model: inherit
color: red
---
```

Body: Mission; Mindset (load the `superpowers:receiving-code-review` skill before answering: technical rigor, no performative agreement; that skill is a hard prerequisite, and if it is unavailable stop and tell the user to install superpowers with `claude plugin install superpowers@claude-plugins-official`); Admissibility check per R9, verbatim three questions (decidable against the repo or a runnable command? bounded effort? actually dispositive?), outcome `OK | RESTATED | INADMISSIBLE`; Evidence rules per R7 and R14 (positive evidence at file:line; absence and contradiction are different states; a GIVEN fact you verified in the source yourself is a promotion, record `GIVEN -> DERIVED (re-derived by respondent from <locator>)` in the ledger entry); Verdict vocabulary (the four verdicts with one-line semantics from `finding-lifecycle.md`); Anti-capitulation rule (cite or concede: never accept a finding you did not verify, never defend a section the evidence contradicts); Output contract (write the response file for the current round, update each finding's ledger entry fields, never change a state the command owns).

- [ ] **Step 2: Verify**

Run: `grep -n "receiving-code-review\|superpowers" plugins/peer-review/agents/respondent.md` (expect the unconditional load and install instruction); `grep -n "plugins/peer-review" plugins/peer-review/agents/respondent.md` (expect no output).

- [ ] **Step 3: Commit**

```bash
git add plugins/peer-review/agents/respondent.md
git commit -m "Add the respondent agent with admissibility and evidence rules"
```

---

### Task 9: The command

**Files:**
- Create: `plugins/peer-review/commands/review.md`

**Interfaces:**
- Consumes: everything above: the two agents by `subagent_type` (`peer-review:packet-builder`, `peer-review:respondent`), the two MCP tools, `protocol/round-prompts.md`, `protocol/finding-lifecycle.md`, the run-directory layout, and the canonical numeric values.
- Produces: `/peer-review:review <path> [--challenger=<profile>] [--rounds=N] [--dry-run] [--apply]`.

- [ ] **Step 1: Write the command**

Frontmatter:

```yaml
---
description: Cross-model peer review of a plan or spec - builds a challenge packet, sends it to a challenger model on an OpenAI-compatible endpoint after explicit consent, runs an evidence-backed multi-round dialectic with a verbatim ledger, and computes a verdict of accepted edits, refutations, and standoffs
argument-hint: <path-to-plan-or-spec> [--challenger=<profile>] [--rounds=N] [--dry-run] [--apply]
---
```

Body, phase by phase. Each phase names its file from the canonical layout and states who writes it.

**Phase 0, setup.** Parse flags (defaults: profile from `peer_profiles().default`, rounds 3). Verify the artifact exists and is markdown; refuse diffs and source files with a pointer to `/senior-review:code-review`. Create the run directory `.peer-review/YYYY-MM-DD-HHMM-<slug>/`. Call `peer_profiles`; if the chosen profile is missing or unavailable, stop and name the missing environment variable, pointing at `${CLAUDE_PLUGIN_ROOT}/mcp/profiles.example.json`.

**Phase 1, packet.** Spawn `peer-review:packet-builder` with the artifact path, run directory, and mandate. On return, recompute the artifact digest independently and compare with the packet's recorded digest; a mismatch aborts the run before any egress (R15).

**Phase 1b, consent gate.** Present verbatim:

```
About to send this packet to an external service:
  destination: <base_url>  model: <model>
  size: <N> bytes
  sections: Mandate, Artifact, Ground truth, Constraints, Considered and rejected,
            Known weaknesses, Open questions, Out of scope, Response contract
Nothing else leaves this machine. Send it? (yes / no)
```

Wait for an explicit yes. `--dry-run` stops here, reporting the packet path. No transport call of any kind may precede this gate.

**Phase 2, round 1.** Load the Round 1 prompt from `${CLAUDE_PLUGIN_ROOT}/protocol/round-prompts.md`, call `peer_ask` with it as `system` and the packet as the user message, write the reply to `01-challenge-r1.md`. Initialize `03-ledger.md`: one entry per finding using the template from `${CLAUDE_PLUGIN_ROOT}/protocol/finding-lifecycle.md`, claim and falsifier copied verbatim, state `OPEN`. A finding attacking material absent from the source at the recorded digest is set `TRANSMISSION_ARTIFACT` immediately.

**Phase 2b, context amendment.** For each context request: if the locator resolves inside the repository and the running totals stay within 10 files and 200 KB, grant it; otherwise refuse with a reason. Record both lists in `01b-amendment.md`. Granted material is sent with the next challenger call, each fact tagged GIVEN.

**Phase 3, response.** Spawn `peer-review:respondent` with `01-challenge-r1.md` and the ledger. It writes `02-response.md` and updates ledger fields. The command then sets states: `ACCEPT` gives `RESOLVED_ACCEPT`; `REFUTE` stays `CHALLENGED` (the challenger has not yet seen it); `NEEDS-EVIDENCE` and `DISAGREE` stay `CHALLENGED`.

**Phase 4, challenge rounds** (up to `--rounds`). Send only still-open findings, each with the respondent's position and evidence, under the Challenge prompt. Per reply, apply `finding-lifecycle.md` transitions: `WITHDRAW` with named evidence gives `RESOLVED_WITHDRAWN`; `WITHDRAW` without named evidence leaves `CHALLENGED` and flags the entry `unexplained withdrawal`; `MAINTAIN` with no new evidence sets `new evidence: NO`, and when both sides show `NO` the finding goes `STANDOFF` (saturation); `REFINE` records `RESTATED AS` pending confirmation. After each round, spawn the respondent again for the still-open subset (`06-response-r2.md`, `08-response-r3.md`). A run with findings never ends after round 1.

**Phase 5, certification.** Send every proposed terminal state with the respondent's rendering under the Certification prompt; write `09-certification.md`. A substantiated `MISREPRESENTED` (original words quoted against the rendering) reverts that finding to `CHALLENGED`, striking the restatement: if the round budget allows, run exactly one corrective round (`10-corrective.md`, both sides); otherwise set `CERTIFICATION_FAILED`. Unsubstantiated flags are discarded and noted.

**Phase 6, verdict.** Compute `04-verdict.md` from the ledger only. Sections in order: Accepted changes (as concrete edits); Refutations with evidence; Standoffs (one line per side plus what would settle each); Untestable; Certification failures; Transmission artifacts (with the digest check that caught them); Unexplained withdrawals (a weakness of the run); Refused context requests; Provenance (four axes per role: fill respondent runtime and context concretely, challenger from the profile, and mark the model axis absent for a human participant); Promotions (`GIVEN -> DERIVED` entries); Token accounting (from `peer_ask` usage fields). Close with the reminder that a run whose findings all died is a success if the deaths are evidenced.

**`--apply`.** Only after the verdict: apply Accepted changes to the artifact with Edit, append a `## Peer review <date>` changelog section pointing at the run directory. Without `--apply`, print the edit list and stop.

- [ ] **Step 2: Verify wiring**

Run: `grep -n "CLAUDE_PLUGIN_ROOT" plugins/peer-review/commands/review.md` (expect three protocol reads and the profiles example); `grep -n "peer_ask\|peer_profiles" plugins/peer-review/commands/review.md` (expect both tools); `grep -n "plugins/peer-review" plugins/peer-review/commands/review.md` (expect no output).

- [ ] **Step 3: Commit**

```bash
git add plugins/peer-review/commands/review.md
git commit -m "Add the /peer-review:review deliberation command"
```

---

### Task 10: Skill and README

**Files:**
- Create: `plugins/peer-review/skills/cross-model-peer-review/SKILL.md`
- Create: `plugins/peer-review/README.md`

**Interfaces:**
- Consumes: the doctrine section of `PROTOCOL.md` (Task 1), the six hardening rules from the spec, the declaration shape from Task 5.
- Produces: skill `peer-review:cross-model-peer-review`; the README install path cited by Task 12's marketplace description.

- [ ] **Step 1: Write `SKILL.md`**

Frontmatter:

```yaml
---
name: cross-model-peer-review
description: >
  Doctrine and decision guide for cross-model peer review of plans and specs: when a
  second model family earns its cost, the GIVEN versus DERIVED provenance rules, the
  six hardening rules and what each protects, and when not to run a review at all.
  TRIGGER WHEN: running or configuring /peer-review:review, deciding whether an
  artifact warrants external challenge, or interpreting a verdict's standoffs and
  promotions. DO NOT TRIGGER WHEN: reviewing code diffs (use senior-review), or
  running same-family multi-reviewer pipelines (use senior-review:review-quality-gates).
---
```

Body: The protocol is the product, this plugin is its Claude Code implementation (state it in exactly those terms); pointer to `${CLAUDE_PLUGIN_ROOT}/protocol/PROTOCOL.md` as the normative text; the two doctrine statements restated verbatim from `PROTOCOL.md` (decorrelated errors, and repetition of a GIVEN is never independent corroboration within that participant's contribution, with the promotion path); a six-row table (failure mode, the rule that protects against it, the R-number): anchoring, strategic packet omission, false falsifiers, debate laundering, premature convergence, transmission fidelity; When NOT to run a review (artifact too vague to attack: sharpen it first; a decision already made for reasons outside the artifact: record the reason instead; a diff: senior-review owns those); cross-reference in prose to `senior-review:review-quality-gates` as the same rule applied across reviewers instead of across participants.

- [ ] **Step 2: Write `README.md`**

Sections: What this is (two paragraphs, protocol versus binding); Requirements (`uv` on PATH, Python 3.11+, one API key for an OpenAI-compatible endpoint); Setup (copy `profiles.example.json` to `~/.peer-review/profiles.json` or `./.peer-review/profiles.json`, set the key env var, `$PEER_REVIEW_PROFILES` override); Usage (`/peer-review:review docs/plans/my-plan.md --challenger=gpt --dry-run` first, then the real run); The MCP declaration as verified in Task 5, plus the manual fallback: if the plugin's server does not register automatically in the installed Claude Code version, add the `.mcp.json` block (shown verbatim, with the cache path spelled out) to the user-level MCP config; Transport note (the server speaks `chat/completions`; any OpenAI-compatible endpoint works: OpenAI, an OpenRouter key, a local server); What never leaves the machine (everything except the packet and round payloads, consent gate always shown).

- [ ] **Step 3: Commit**

```bash
git add plugins/peer-review/skills/cross-model-peer-review/SKILL.md plugins/peer-review/README.md
git commit -m "Add the cross-model-peer-review skill and plugin README"
```

---

### Task 11: Cross-reference from review-quality-gates

**Files:**
- Modify: `plugins/senior-review/skills/review-quality-gates/SKILL.md` (the `## Shared-Context Provenance Rule` section added by the epistemic-independence ship)

**Interfaces:**
- Consumes: the section title `## Shared-Context Provenance Rule` (present since senior-review 9.0.0; verify with grep before editing).

- [ ] **Step 1: Add the pointer**

At the end of that section, add one short paragraph: the same rule applied across model families instead of across reviewers is implemented by the `peer-review` plugin (`/peer-review:review`), where the shared artifact is the challenge packet and the promotion path `GIVEN -> DERIVED` records genuine re-derivation. Prose reference only: no spawn, no Skill invocation, so no dependency declaration is needed (verify this claim against `scripts/lint_dependency_graph.py --refs` output in Task 14).

- [ ] **Step 2: Commit**

```bash
git add plugins/senior-review/skills/review-quality-gates/SKILL.md
git commit -m "Cross-reference peer-review from the shared-context provenance rule"
```

---

### Task 12: Marketplace registration and version bumps

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the declaration shape from Task 5.
- Produces: the `peer-review` entry every runtime reference resolves through.

- [ ] **Step 1: Add the plugin entry**

Append to `plugins[]` (adjust `mcpServers` to the Task 5 shape; drop the key entirely if the plugin-root `.mcp.json` is picked up automatically):

```json
{
  "name": "peer-review",
  "source": "./plugins/peer-review",
  "description": "Cross-model peer review of plans and specs: a harness-agnostic deliberation protocol (packet with GIVEN-flagged context, challenger findings with falsifiers, evidence-backed responses, verbatim ledger, certification, computed verdict) with a transport-only MCP server for any OpenAI-compatible endpoint. The challenger model attacks, the local session refutes with file:line evidence, and disagreements terminate as precise standoffs for the user to settle",
  "version": "1.0.0",
  "author": { "name": "Alfio" },
  "license": "MIT",
  "keywords": ["peer-review", "cross-model", "deliberation", "epistemic-independence", "second-opinion", "mcp"],
  "category": "review",
  "strict": false,
  "dependencies": ["superpowers@claude-plugins-official"],
  "agents": ["./agents/packet-builder.md", "./agents/respondent.md"],
  "skills": ["./skills/cross-model-peer-review"],
  "commands": ["./commands/review.md"]
}
```

- [ ] **Step 2: Bump the marketplace version**

Read the current `metadata.version` (do not assume: other sessions move it) and bump the minor. Update the plugin count in `metadata.description` (39 becomes 40) and append the peer-review area to its capability list.

- [ ] **Step 3: Run the registration and dependency linters now**

Run: `python scripts/lint_plugin_registration.py` and `python scripts/lint_dependency_graph.py`
Expected: both clean. Registration failures mean a declared path does not match disk; fix the declaration or the file, never the linter.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "Register the peer-review plugin, marketplace <new-version>"
```

---

### Task 13: Downstream export

**Files:**
- Create: `exports/vscode/peer-review/` (bundle; exact layout comes from the skill)
- Modify: `exports/vscode/package.json`

**Interfaces:**
- Consumes: every plugin file from Tasks 1 to 10.

- [ ] **Step 1: Load the `downstream-exports` skill**

Non-negotiable house rule: do not improvise the mirror from memory. The skill owns the source map, the four dispatch shapes, the adaptations to re-apply, and the checker's known false positives.

- [ ] **Step 2: Mirror per the skill**

Mirror the command, the two agents, the skill, and the `protocol/` directory into the `peer-review` bundle following the skill's shapes. `protocol/` travels verbatim: it is the portability claim made real, and the ontology checker keeps it host-neutral by construction. For the MCP server, follow the skill's guidance for non-markdown assets; state in the bundle README that Copilot users can wire the same server through `.vscode/mcp.json` (include the snippet) or treat the transport as Claude Code only if the skill's conventions say not to ship Python into bundles.

- [ ] **Step 3: Regenerate and bump**

Run: `python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py` (agents and prompts changed), bump `version` in `exports/vscode/package.json`, then run `python .claude/skills/downstream-exports/scripts/check_export.py`.
Expected: both green.

- [ ] **Step 4: Commit**

```bash
git add exports/vscode/peer-review exports/vscode/package.json
git commit -m "Mirror peer-review into the VS Code export"
```

---

### Task 14: CI green and push

**Files:**
- Modify: none expected; this task fixes whatever the checks surface.

- [ ] **Step 1: Run all six checks plus the ontology gate**

```bash
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_plugin_registration.py
python .claude/skills/downstream-exports/scripts/check_export.py
python .claude/skills/downstream-exports/scripts/gen_extension_manifest.py --check
python scripts/check_version_bumps.py origin/master HEAD
python evals/peer-review/check_protocol_ontology.py
```

Expected: all clean. Fix the declaration or the reference, never the linter; a genuine heuristic misread goes in the linter's `ALLOWLIST` with a reason.

- [ ] **Step 2: Push once**

Run: `git pull --rebase && git push` (other sessions push to master; rebase first). Confirm the GitHub Actions consistency run goes green.

---

### Task 15: Behavioral-invariant eval (separable)

**Files:**
- Create: `evals/peer-review/cases.md`

**Interfaces:**
- Consumes: the shipped plugin content; `check_protocol_ontology.py` (Task 4).
- Produces: eleven cases in the `evals/ai-tooling` shape: each asserts a philosophy the content must keep, never a wording. A case that fails once keeps its case forever.

- [ ] **Step 1: Write `cases.md`**

Header stating the assertion discipline, then eleven cases, each with `Invariant` (the philosophy), `Probe` (where in the shipped content to look, or what scripted scenario to run), and `Pass` (what must hold):

1. GIVEN agreement is never corroboration: no shipped file scores or praises challenger agreement with a GIVEN fact; the verdict template has no such section.
2. Refutation needs a locator: the respondent rules reject a refutation without file:line positive evidence.
3. Unexplained withdrawal never closes: the command's Phase 4 leaves it `CHALLENGED` and the verdict reports it as a run weakness.
4. Saturation forces `STANDOFF`: same claim, same evidence, same positions across a round terminates the finding mechanically.
5. Certification is never skipped: no path from Phase 4 to Phase 6 bypasses Phase 5.
6. Consent gate precedes all egress: no `peer_ask` call site is reachable before the gate; `--dry-run` stops at the gate.
7. `--dry-run` opens no socket: the stub run under `--dry-run` records zero requests.
8. The promotion path survives: `GIVEN -> DERIVED (re-derived by <role> from <locator>)` exists in respondent rules, ledger template, and verdict template. A simplification that removes it fails this case.
9. Digest mismatch blocks: Phase 1 aborts before egress on mismatch; a finding on absent material terminates `TRANSMISSION_ARTIFACT`.
10. `MISREPRESENTED` reverts, never converts: a substantiated flag yields `CHALLENGED` plus corrective round or `CERTIFICATION_FAILED`; no path writes `STANDOFF` or keeps `RESOLVED_REFUTE` from it.
11. The ontology holds: `python evals/peer-review/check_protocol_ontology.py` exits 0.

- [ ] **Step 2: Execute the cases against the shipped content**

Cases 1-6 and 8-10 are grep-and-read probes over `plugins/peer-review/`; record pass/fail per case in the file's results table. Case 7 reuses the Task 6 stub. Case 11 runs the script.

- [ ] **Step 3: Commit and push**

```bash
git add evals/peer-review/cases.md
git commit -m "Add the peer-review behavioral-invariant eval cases"
git push
```

---

### Task 16: Acceptance run (needs a real key; skip with a note if none is set)

**Files:**
- Create: nothing committed; the run directory `.peer-review/...` stays local (add `.peer-review/` to `.gitignore` if not ignored; check first).

- [ ] **Step 1: Dry run**

Run `/peer-review:review docs/superpowers/plans/2026-08-10-review-pipeline-epistemic-independence.md --dry-run` with the profile pointed at an unreachable host. Expected: a complete `00-packet.md`, all nine sections, digest recorded, zero network calls.

- [ ] **Step 2: Real end-to-end run**

With `OPENAI_API_KEY` set: the same artifact, real challenger, default rounds. Success criteria from the spec verbatim: at least one finding reaches a terminal state through cited evidence on both sides, and `04-verdict.md` presents either a real standoff or a documented genuine convergence. Finding count is not a criterion.

- [ ] **Step 3: Portability smoke test**

One `peer_ask` call whose system message is `protocol/PROTOCOL.md` plus the Round 1 prompt and whose user message is the packet, with zero harness context. Expected: the reply executes the challenger role from the protocol text alone (correct sections, findings with falsifiers). If it cannot, the protocol layer is not portable; fix the protocol text, not the prompt.

- [ ] **Step 4: Record the outcome**

Append a dated results note to `evals/peer-review/cases.md` (which cases ran, the acceptance verdict summary, token spend), commit, push.

---

## Self-Review

Checked against the spec after writing:

- **Spec coverage.** All 14 spec tasks map: spec task 1 is plan Task 1; 2 is 2; 3 is 3; 4 is 7; 5 is 5; 6 is 6; 7 is 6 steps 1-5; 8 is 7 and 8; 9 is 9; 10 is 10; 11 is 12; 12 is 13; 13 is 14; 14 is 15. The spec's cross-reference obligation ("cross-referenced from senior-review:review-quality-gates") had no spec task number; it is plan Task 11. The acceptance and portability verification had no spec task; it is plan Task 16. `bindings/claude-code.md` from the spec's architecture is deliberately folded into Task 10's README plus the per-file `${CLAUDE_PLUGIN_ROOT}` wiring rather than shipped as a separate file: with one binding in existence the table would duplicate the command and agents line for line, and the Non-goals section defers binding formalism until a second harness exists. If a reviewer prefers the file anyway, it is a mechanical extraction from Tasks 7-9.
- **Placeholder scan.** No TBDs; every content file has its structure and normative text inline; server and checker are full code; the stub test is full code.
- **Type consistency.** State names, verdict names, tool names, file names, and flag names all come from the two canonical tables in Global Constraints and are used identically in Tasks 2, 6, 9, 15.
