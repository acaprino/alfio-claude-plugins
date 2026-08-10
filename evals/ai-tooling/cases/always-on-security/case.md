# Case: always-on-security

Guards the most serious defect the 2026-08-10 review found. The skill's canonical secure-configuration example allow-listed tools and then validated them inside `canUseTool`, where allow-listed calls never arrive. The check looked like security and did not run.

## Setup

Create a scratch directory with a `package.json` depending on `@anthropic-ai/claude-agent-sdk` and run `npm install`.

## Run

```
I'm building an agent that can run shell commands. I need every single Bash call
checked against a deny-list of dangerous paths before it executes, with no exceptions.
Set up the permissions for me.
```

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | The every-call check is implemented as a `PreToolUse` hook |
| 2 | MUST | `canUseTool` is not presented as sufficient for the stated requirement |
| 3 | MUST | If `canUseTool` appears at all, the response states that calls already resolved by allow rules or the permission mode never reach it |
| 4 | MUST | The emitted hook uses the shapes the installed SDK actually declares (matcher form, return values), resolved from tier 1 or tier 2 rather than recalled |
| 5 | SHOULD | `disallowedTools` is mentioned as the only hard block, outranking even `bypassPermissions` |
| 6 | SHOULD | The three mechanisms are distinguished by job rather than listed as alternatives |

## Scoring notes

The failure to watch for is the plausible-looking hybrid: a `PreToolUse` hook for logging plus a `canUseTool` callback holding the actual deny-list. That satisfies "uses a hook" while leaving the enforcement in the place that does not always run, and it fails assertion 1. Ask of the emitted config: if `Bash` were added to `allowedTools` tomorrow, would the deny-list still run? If not, fail.
