# Cross-Model Peer Review for VS Code Copilot

A VS Code Copilot port of the `peer-review` plugin from
[acaprino/claude-code-daodan](https://github.com/acaprino/claude-code-daodan): cross-model
peer review of plans and specs. A second, independently vendored model family attacks
your artifact through an evidence-backed, multi-round dialectic before you act on it.

## What this is

Cross-Model Peer Review is a harness-independent, provider-independent protocol for
putting a plan or a spec through adversarial cross-model challenge. It defines fifteen
numbered requirements (immutable roles, a packet contract, four-axis provenance, an
explicit egress consent gate, a challenge/response contract, falsifier admissibility,
verbatim carry through the ledger, mechanical termination, certification against
misrepresentation, a ledger-computed verdict, and source-to-request transmission
fidelity) plus two doctrine statements about what cross-model independence actually
buys you. None of it names a tool, a vendor, a model, or a transport. The full,
normative text ships with this bundle at
`.github/skills/cross-model-peer-review/protocol/PROTOCOL.md`, byte-identical to the
upstream plugin's copy; the `cross-model-peer-review` skill carries the doctrine layer
and the decision guide for when a run is and is not worth its cost.

This bundle is one conforming binding of that protocol for VS Code Copilot, not the
protocol itself, in the same sense the upstream `peer-review` plugin is one conforming
binding for Claude Code. `/review` orchestrates a run through the
`peer-review-orchestrator` agent: a `packet-builder` subagent builds the immutable
challenge packet from your artifact, an MCP server sends it to an external challenger
model over any OpenAI-compatible `chat/completions` endpoint only after you explicitly
consent, a `respondent` subagent answers findings with evidence pulled from your
repository, and the orchestrator computes a verdict from a ledger it never hand-edits.
Everything below is binding-specific mechanism; the requirements it satisfies live in
the protocol document, not here.

## Install

This is one bundle of the [VS Code export catalog](../README.md). Copy it into your
project:

```bash
cp -r exports/vscode/peer-review/.github /path/to/your/project/
```

If the project already has a `.github/` directory, copy the three subdirectories
individually:

```bash
cp -r exports/vscode/peer-review/.github/skills/*  /path/to/your/project/.github/skills/
cp    exports/vscode/peer-review/.github/prompts/* /path/to/your/project/.github/prompts/
cp    exports/vscode/peer-review/.github/agents/*  /path/to/your/project/.github/agents/
```

Or install the [Claude Code Daodan extension](../README.md#install), which carries
every bundle at once and copies this skill into `~/.copilot/skills/`.

VS Code picks up the new skill, prompt, and agents without a restart. Verify with
**Chat: Configure Agents** and by typing `/review` in the Chat view.

## Requirements

- `uv` on PATH. The MCP server is a PEP 723 inline-dependency script; `uv` resolves
  and runs it without a separate install step.
- Python 3.11 or later (the server's own version floor).
- One API key for an OpenAI-compatible endpoint: OpenAI itself, an OpenRouter key, or
  a locally hosted server that answers the same `chat/completions` request shape.

## Setup

1. Copy the shipped example profile file,
   `.github/skills/cross-model-peer-review/mcp/profiles.example.json`, to one of the
   two locations the server checks by default: project-scoped
   `./.peer-review/profiles.json`, or user-scoped `~/.peer-review/profiles.json`. (Or
   set `$PEER_REVIEW_PROFILES` to any path of your choosing; when set, it is checked
   before either default location.)
2. Edit the copy. Each entry is a named profile the prompt's `--challenger` flag
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
3. Export that variable in the shell VS Code runs in, matching whichever profile you
   intend to use: `export OPENAI_API_KEY=...` for the example above.

## The MCP server

VS Code Copilot reads MCP server declarations from `.vscode/mcp.json`. This bundle
ships the same transport-only server the upstream plugin ships,
`.github/skills/cross-model-peer-review/mcp/server.py`, byte-identical to the Claude
Code copy: it is plain PEP 723 Python that speaks the standard MCP stdio protocol and
names no Claude Code mechanism anywhere in its own source, so it runs unchanged under
any MCP-compliant client. Add an entry naming it `peer-review`, matching the name the
prompt and the orchestrator agent both assume:

```json
{
  "servers": {
    "peer-review": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--script",
        "<path-to-server.py>"
      ]
    }
  }
}
```

Substitute `<path-to-server.py>` for wherever this bundle's copy actually lives on
disk: the extension's install (`~/.copilot/skills/cross-model-peer-review/mcp/server.py`
by default, confirm with **Daodan: Reveal Skills Folder**), or your per-project copy
(`.github/skills/cross-model-peer-review/mcp/server.py` relative to the project root)
if you used the `cp -r` install instead. `.vscode/mcp.json`'s exact schema (the
`type: "stdio"` field, whether it accepts variable expansion in `args`) is decided by
your VS Code version; check **Settings > MCP** or the current VS Code MCP
documentation if the server does not connect with the snippet above as written.

If the server fails to start, it degrades per-server: Copilot's MCP status view shows
it as disconnected. This does not break the rest of the bundle. The skill, the two
subagents, and the prompt's file-writing phases keep working; only the `peer_profiles`
and `peer_ask` tool calls fail when the orchestrator reaches them, which surfaces as
the transport-error handling described in `review.prompt.md`, not as a broken install.

## Usage

Run a dry run first. It builds the packet and stops at the consent gate, before it
asks for a decision, so nothing leaves your machine:

```
/review docs/plans/my-plan.md --challenger=gpt --dry-run
```

Inspect the packet written under `.peer-review/<timestamp>-<slug>/00-packet.md`, then
run it for real:

```
/review docs/plans/my-plan.md --challenger=gpt
```

At the consent gate you are shown the destination, the byte size, and the section
list before anything is sent. Only a literal `yes` proceeds; anything else aborts the
run with the packet left on disk for inspection.

Useful flags: `--rounds=N` (`2` or `3`, default `3`; a value below `2` is rejected, a
run with findings can never terminate after round one). `--apply` (after the verdict
is computed, apply its accepted changes to the artifact and append a changelog
section). `--challenger` may be omitted once `profiles.json` names a `default`.

This bundle reviews plans and specs only. Point it at a `.md` or `.markdown` file; it
refuses anything that looks like a unified diff or a source file and names
`/team-review` in the `_pipelines` bundle as the right tool for that target instead.

## Transport

The server speaks the `chat/completions` request shape OpenAI's API uses and most
alternative providers mirror, so any endpoint that accepts that shape works: OpenAI
directly, an OpenRouter key pointed at a different frontier model, or a locally hosted
OpenAI-compatible server. Requests are capped at 400,000 bytes and refused outright
above that, rather than silently truncated. A request is retried once, after a 5
second backoff, on HTTP 429/500/502/503/504; any other failure is returned as
`{"error": "..."}` for the orchestrator to handle rather than raised as an exception.
Responses are streamed, which makes the 600 second timeout an idle allowance between
chunks rather than a cap on the whole generation: a challenger that thinks for eight
minutes before emitting anything is a normal round, not a failure.

**The payload is a path, never a string.** `peer_ask` takes `content_path` and reads
the outgoing message off disk itself, and it reads nothing outside a `.peer-review/`
run directory below the working directory. This is R15 made mechanical. Asking the
agent that built the packet to reproduce it inside a tool call is asking it to retype
tens of kilobytes, and under that load it summarizes instead, which no later check can
detect because every later check reads the file rather than the request. The reply
carries `sent_bytes` and `sent_sha256`, computed over exactly the bytes that went on
the wire, and the run's verdict records them.

## What never leaves the machine

Explicit consent is given exactly once, at the single consent gate before round 1,
never per round. The prompt shows the destination, the packet's byte size, its sha256,
and its section list, and only a literal `yes` proceeds. The digest is there so the
approval attaches to one specific file: the transport reports back the digest of what
it actually sent, and the run stops if the two ever differ. That one `yes` covers the whole run:
the user approves the packet, and afterward the run may send round 2 and round 3
challenge payloads, the certification pass, and the corrective round if one runs, with
no further prompt. It also covers Phase 2b context amendments: repository material
granted to the challenger's context requests, mechanically capped at 10 files / 200 KB,
is sent as part of round 2's payload, tagged GIVEN, without a second approval step.
Everything else stays local: the rest of your repository beyond whatever the packet
and any granted amendments carried, `profiles.json` itself (only the resolved
`base_url` and `model` are transmitted as part of each request, never the file), the
ledger, the verdict, and the packet-building and response-answering work that happens
inside the `packet-builder` and `respondent` Copilot agents with full repository
access. The API key travels only in the outgoing request's `Authorization` header; the
server never logs or returns it, and redacts it from any error text it does return.

That boundary holds in the transport and not only in the prompt. Because the payload
is named by path, `peer_ask` refuses any path resolving outside a `.peer-review/` run
directory, symlinks and `..` included. A file the protocol did not write cannot be
sent, whatever a prompt in your artifact asks the agent to attach.

## Differences from the Claude Code plugin

| Area | Claude Code | This port |
|---|---|---|
| Command | `/peer-review:review` | `/review` |
| Dispatch | The command body fans out `packet-builder` and `respondent` from the main agent via `Task` blocks | The `peer-review-orchestrator` agent, the only thing that can hold the `agents:` allowlist VS Code gates dispatch behind |
| MCP tool references | `mcp__peer-review__peer_profiles`, `mcp__peer-review__peer_ask` (Claude Code's `mcp__<server>__<tool>` naming) | `peer_profiles`, `peer_ask` (bare names; an MCP server's tool ids depend on the name the user gave that server, so a fixed prefix cannot be assumed) |
| MCP registration | Plugin-root `.mcp.json`, auto-discovered on install, `${CLAUDE_PLUGIN_ROOT}` expansion | `.vscode/mcp.json`, added by hand (see above), no path-expansion variable assumed |
| `receiving-code-review` mindset | Loaded from the `superpowers` plugin, a declared hard dependency | Restated inline in `respondent.agent.md`; `superpowers` is a Claude Code plugin not ported to this catalog |
| Diff / code-change pointer | `/senior-review:code-review` | `/team-review` in the `_pipelines` bundle (the closest exported equivalent; `code-review` itself ships no automated fix loop in this catalog and is not exported) |

Protocol files, the MCP server, and the example profiles file are byte-identical to
the upstream plugin's copies. Nothing about the fifteen requirements changed in this
port; only the transport wiring and the dispatch mechanics did.
