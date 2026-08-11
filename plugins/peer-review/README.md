# peer-review

Cross-model peer review of plans, specs, and the decisions a session has just made: a
second, independently-vendored model family attacks your artifact through an
evidence-backed, multi-round dialectic before you act on it.

## What this is

Cross-Model Peer Review is a harness-independent, provider-independent protocol for
putting a plan or a spec through adversarial cross-model challenge. It defines
fifteen numbered requirements (immutable roles, a packet contract, four-axis
provenance, an explicit egress consent gate, a challenge/response contract, falsifier
admissibility, verbatim carry through the ledger, mechanical termination, certification
against misrepresentation, a ledger-computed verdict, and source-to-request
transmission fidelity) plus two doctrine statements about what cross-model
independence actually buys you. None of it names a tool, a vendor, a model, or a
transport. The full, normative text ships with this plugin at `protocol/PROTOCOL.md`;
the `cross-model-peer-review` skill carries the doctrine layer and the decision guide
for when a run is and is not worth its cost.

This plugin, `peer-review`, is one conforming binding of that protocol for Claude
Code, not the protocol itself. `/peer-review:review` orchestrates a run: a
`packet-builder` subagent builds the immutable challenge packet from your artifact, an
MCP server sends it to an external challenger model over any OpenAI-compatible
`chat/completions` endpoint only after you explicitly consent, a `respondent` subagent
answers findings with evidence pulled from your repository, and the command computes a
verdict from a ledger it never hand-edits. Everything below is binding-specific
mechanism; the requirements it satisfies live in the protocol document, not here.

## Requirements

- `uv` on PATH. The MCP server is a PEP 723 inline-dependency script; `uv` resolves
  and runs it without a separate install step.
- Python 3.11 or later (the server's own version floor).
- One API key for an OpenAI-compatible endpoint: OpenAI itself, an OpenRouter key, or
  a locally hosted server that answers the same `chat/completions` request shape.

## Setup

These steps assume the plugin is already installed
(`claude plugin install peer-review@claude-code-daodan`).

1. Copy the shipped example profile file, `mcp/profiles.example.json`, to one of the
   two locations the server checks by default: project-scoped
   `./.peer-review/profiles.json`, or user-scoped `~/.peer-review/profiles.json`. (Or
   set `$PEER_REVIEW_PROFILES` to any path of your choosing; when set, it is checked
   before either default location.)
2. Edit the copy. Each entry is a named profile the command's `--challenger` flag
   selects by name:

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

   A profile takes its key from one of two fields:

   | Field | Holds | Use it when |
   |---|---|---|
   | `api_key_env` | the **name** of an environment variable | the key already lives in your environment, or a machine sets it |
   | `api_key` | the key itself | you would rather not manage an environment variable |

   When both are present the environment wins if that variable is set, so a machine can
   override the file without editing it, and `api_key` is the fallback. The server reads
   the key at call time and never returns it, not even in its own availability check.

   Pasting a key into `api_key_env` is the one mistake worth naming: it is looked up as
   a variable name, resolves to nothing, and the profile reports `available: false`.
   `peer_profiles` catches it and reports `key_source: "malformed_env_name"` with an
   explanation, and it never echoes the offending value back, because in that situation
   the value is the key.

   A literal key belongs in `~/.peer-review/profiles.json`, which sits outside every
   repository. If you keep one in a project-scoped file instead, `peer_profiles` checks
   whether git ignores that file and warns when it does not.
3. If you chose `api_key_env`, export that variable in the shell Claude Code runs in,
   matching whichever profile you intend to use: `export OPENAI_API_KEY=...` for the
   example above.

## Usage

Run a dry run first. It builds the packet and stops at the consent gate, before it
asks for a decision, so nothing leaves your machine:

```
/peer-review:review docs/plans/my-plan.md --challenger=gpt --dry-run
```

Inspect the packet written under `.peer-review/<timestamp>-<slug>/00-packet.md`, then
run it for real:

```
/peer-review:review docs/plans/my-plan.md --challenger=gpt
```

At the consent gate you are shown the destination, the byte size, and the section
list before anything is sent. Only a literal `yes` proceeds; anything else aborts the
run with the packet left on disk for inspection.

Useful flags: `--rounds=N` (`2` or `3`, default `3`; a value below `2` is rejected, a
run with findings can never terminate after round one). `--apply` (after the verdict
is computed, apply its accepted changes to the artifact with the Edit tool and append
a changelog section). `--challenger` may be omitted once `profiles.json` names a
`default`.

### Two modes

**Artifact mode** judges a document already on disk. Point the command at a `.md` or
`.markdown` file. It refuses anything that looks like a unified diff or a source file
and names `/senior-review:code-review` as the right tool for that target instead.

**Brief mode** judges what exists only in the session. Run the command with no path,
optionally with a topic to scope it:

```
/peer-review:review
/peer-review:review "the repo-hygiene split"
```

Phase 0b materializes the session's situation, its decisions already taken with their
rationale, its still-open decisions with their options, and its constraints into
`00-brief.md`, freezes that file, and puts it on trial. Everything after Phase 0b is
the same run as artifact mode.

A mistyped path is not a topic: a token containing a path separator or ending in `.md`
that does not exist stops the run, rather than quietly becoming a brief-mode subject.

Two things differ in brief mode. The brief is drafted by the same session that made the
decisions, so the verdict records that the artifact was materialized rather than
independently authored (R13), and `brief-builder`'s "could not be sharpened" list is
carried into the packet's Known-weaknesses section instead of being hidden. And
`--apply` is refused, because the brief is a frozen record that nothing downstream
reads: the verdict's Accepted changes list names decisions to revisit, not text to
rewrite.

## What you get back

Everything lands in one run directory, `.peer-review/YYYY-MM-DD-HHMM-<slug>/`. Read
`04-verdict.md` first: it is the only file written for a human, and it is computed
from the ledger rather than composed, so its prose can explain a finding's outcome but
never change one.

| File | What it holds |
|---|---|
| `00-packet.md` | Everything that left your machine, exactly as the challenger saw it |
| `01-challenge-r1.md` | The challenger's frame challenge, findings with falsifiers, and what it could not assess |
| `01b-amendment.md` | Repository material it asked for: what was granted, and every refusal with its reason |
| `02-response.md` | Your side's verdict per finding, with a locator for every non-ACCEPT |
| `03-ledger.md` | Run state, one entry per finding, claim and falsifier carried verbatim throughout |
| `04-verdict.md` | The outcome |
| later rounds, `09-certification.md`, `10-corrective.md` | The exchange, and the challenger's last word on how its own findings were rendered |

The verdict's first three sections are the ones that carry decisions. **Accepted
changes** are concrete edits, applied for you if you passed `--apply`. **Refutations**
each cite the evidence that satisfied the finding's falsifier. **Standoffs** are the
point of the exercise: one line per side plus what would settle it, which is a decision
that is genuinely yours rather than a bug either party can close.

The sections after those describe the run's own health, and they are worth a look
before trusting it. Untestable findings, certification failures, and transmission
artifacts are findings that died procedurally rather than on the merits, so none of
them is evidence that the artifact is sound. Unexplained withdrawals and refused
context requests both point at gaps: the first at a challenger that dropped a claim
without saying why, the second at material it wanted and did not get. A run with
several refusals reviewed less than it appears to have reviewed.

Two habits pay off. Read `Cannot assess` in `01-challenge-r1.md`: what the challenger
could not judge is a statement about your packet, not about your plan. And check the
provenance block in the verdict, which records model, runtime, context, and human
axes per role without collapsing them into a score. A challenger whose context axis
reads `packet-only` has no path to the authoritative source, so its agreement with any
fact you supplied is repetition rather than confirmation.

Runs are cheap to keep and cheap to discard. The directory is git-ignored, and every
file in it is plain markdown you can diff, grep, or hand to someone else.

## The MCP server

This plugin ships a plugin-root `.mcp.json` declaring one stdio server, `peer-review`,
running `uv run --script ${CLAUDE_PLUGIN_ROOT}/mcp/server.py`. A plugin-root
`.mcp.json` is auto-discovered on install with no extra configuration, and
`${CLAUDE_PLUGIN_ROOT}` expands to wherever your Claude Code installation placed this
plugin, so the declaration is portable across machines and installs. The marketplace
entry additionally points at the same file (`"mcpServers": "./.mcp.json"`), so there is
one source of truth for the server's configuration rather than two.

If a server fails to start, it degrades per-server: `/mcp` shows it as `Failed to
connect` with an Issue line naming the problem. This does not break the rest of the
plugin. Its commands, agents, and skills keep working; only `/peer-review:review`'s
transport calls (`peer_profiles`, `peer_ask`) fail when the command reaches them,
which surfaces as the transport-error handling described in `commands/review.md`, not
as a broken install.

**Manual fallback.** If, after installing the plugin, the server does not appear
connected in `/mcp`, register it directly at user scope instead of waiting on
auto-discovery. Locate this plugin's installed copy of `server.py` under Claude Code's
plugin cache directory (typically
`~/.claude/plugins/cache/claude-code-daodan/peer-review/<installed
version>/mcp/server.py` on this marketplace; this is also what `${CLAUDE_PLUGIN_ROOT}`
resolves to at runtime, and `/mcp` or your Claude Code installation's plugin listing
will confirm the exact installed version), then add the same server definition this
plugin already ships, with that path substituted in for `${CLAUDE_PLUGIN_ROOT}`, to
your user-level MCP configuration:

```json
{
  "mcpServers": {
    "peer-review": {
      "command": "uv",
      "args": [
        "run",
        "--script",
        "~/.claude/plugins/cache/claude-code-daodan/peer-review/<installed version>/mcp/server.py"
      ]
    }
  }
}
```

## Transport

The server speaks the `chat/completions` request shape OpenAI's API uses and most
alternative providers mirror, so any endpoint that accepts that shape works: OpenAI
directly, an OpenRouter key pointed at a different frontier model, or a locally hosted
OpenAI-compatible server. Requests are capped at 400,000 bytes and refused outright
above that, rather than silently truncated. A request is retried once, after a 5
second backoff, on HTTP 429/500/502/503/504; any other failure, and a request timeout
after 180 seconds, is returned as `{"error": "..."}` for the command to handle rather
than raised as an exception.

## What never leaves the machine

Explicit consent is given exactly once, at the single consent gate before round 1,
never per round. The prompt shows the destination, the packet's byte size, and its
section list, and only a literal `yes` proceeds. That one `yes` covers the whole run:
the user approves the packet, and afterward the run may send round 2 and round 3
challenge payloads, the certification pass, and the corrective round if one runs, with
no further prompt. It also covers Phase 2b context amendments: repository material
granted to the challenger's context requests, mechanically capped at 10 files / 200 KB,
is sent as part of round 2's payload, tagged GIVEN, without a second approval step.
Everything else stays local: the rest of your repository beyond whatever the packet
and any granted amendments carried, `profiles.json` itself (only the resolved
`base_url` and `model` are transmitted as part of each request, never the file), the
ledger, the verdict, and the packet-building and response-answering work that happens
inside Claude Code subagents with full repository access. The API key travels only in
the outgoing request's `Authorization` header; the server never logs or returns it,
and redacts it from any error text it does return.
