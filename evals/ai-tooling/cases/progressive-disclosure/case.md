# Case: progressive-disclosure

The 5.0.0 split only pays for itself if the references are loaded selectively. A skill that reads all five on every invocation has the old 1068-line context cost plus a directory listing.

## Setup

None beyond a scratch directory. This case is scored by observing which files the session reads.

## Run

```
How do I give an Agent SDK subagent its own restricted tool set and a different model
from the parent?
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | `references/sessions-subagents.md` is read |
| 2 | MUST | At most one other reference is read, and only if the answer genuinely spans it |
| 3 | MUST | `references/deployment.md` and `references/mcp-plugins-skills.md` are NOT read: neither is on the path from this question to its answer |
| 4 | SHOULD | The decision tree in the core is what routed the choice, visible as the shape named before the reference is opened |
| 5 | SHOULD | Subagent option names are resolved against the installed SDK or the docs rather than quoted from the reference as final |

## Scoring notes

Assertion 2 has a legitimate exception: subagent tool restriction touches permissions, so opening `permissions-hooks-security.md` is defensible. Opening all five is not. If the harness cannot observe file reads, this case is unscoreable rather than passing; mark it n/a and say so.
