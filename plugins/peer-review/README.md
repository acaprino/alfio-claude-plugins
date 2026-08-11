# peer-review

Cross-model peer review of plans and specs: a second, independently-vendored model
family attacks your artifact through an evidence-backed, multi-round dialectic before
you act on it.

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

   `api_key_env` names an environment variable, never a literal key. The server reads
   it at call time and never returns it, not even in its own availability check.
3. Export that variable in the shell Claude Code runs in, matching whichever profile
   you intend to use: `export OPENAI_API_KEY=...` for the example above.

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

This command reviews plans and specs only. Point it at a `.md` or `.markdown` file; it
refuses anything that looks like a unified diff or a source file and names
`/senior-review:code-review` as the right tool for that target instead.

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

The only bytes that cross the wire are the packet (round 1) and each subsequent
round's payload, sent to the single profile named at the consent gate, and even those
never go out without an explicit `yes` shown against the destination, size, and
section list first, every time a packet is about to be sent. Everything else stays
local: the rest of your repository, `profiles.json` itself (only the resolved
`base_url` and `model` are transmitted as part of the request, never the file), the
ledger, the verdict, and the packet-building and response-answering work that happens
inside Claude Code subagents with full repository access. The API key travels only in
the outgoing request's `Authorization` header; the server never logs or returns it,
and redacts it from any error text it does return.
