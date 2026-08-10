<!-- Scorecard produced by an independent judge that read only this case file and the
candidate output. It could not read plugins/ai-tooling/, so it judged the output against the
assertions rather than against the implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.0 working tree (NOT the installed plugin, which
  was 4.1.0 on this machine; see the run note in RESULTS.md)
- **How the component was exercised:** a fresh subagent adopted the 5.0.0 component body from the
  working tree and received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: always-on-security

Judged against `evals/ai-tooling/cases/always-on-security/case.md`, the emitted output at
`scratchpad/evalrun/out/always-on-security.md`, the emitted project files it references
(`agent.js`, `guards.js`), and the installed
`@anthropic-ai/claude-agent-sdk@0.3.226` `sdk.d.ts`.

## Scores

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | pass | "Always-on enforcement is a **`PreToolUse` hook**. It runs before permission resolution, for every matching call, including calls made inside subagents. That is the layer that carries your guarantee." Emitted wiring: `PreToolUse: [ { matcher: '^Bash$', timeout: 10, hooks: [makeBashGuard({ onDecision })] }, ... ]`. `guards.js` shows the hook holds the real policy, not logging: `const verdict = evaluateBash(input.tool_input, input.cwd, denyRoots); ... return verdict.allowed ? NO_OPINION : deny(verdict.reason);` |
| 2 | MUST | pass | "Your requirement was \"every single Bash call, no exceptions.\" That rules out `canUseTool`, which is the natural place to reach for and the wrong one." And in `agent.js`: "Defence in depth, not the primary control." |
| 3 | MUST | pass | "`canUseTool` is the *last* step in permission evaluation: it only fires for calls that no rule, mode, or hook already resolved. The moment Bash gets allow-listed, or the mode auto-approves it, your check silently stops running." |
| 4 | MUST | pass | "`return { hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: ... } }`" and "Not `{ behavior: 'deny', message }`. That shape is `PermissionResult`, which belongs to `canUseTool` only." Provenance stated: "Verified against the installed SDK, `@anthropic-ai/claude-agent-sdk@0.3.226`, reading `sdk.d.ts` directly". Type check below. |
| 5 | SHOULD | pass | "**`disallowedTools`** is the only hard block in the system and outranks even `bypassPermissions`. Use it for anything you never want reachable." |
| 6 | SHOULD | pass | Framed by job, not as a menu: hook = "the layer that carries your guarantee"; `disallowedTools` = "the only hard block"; `canUseTool` = "Two independent evaluations, not one." `agent.js` states the same as a numbered layering by evaluation order. |

## Assertion 4, checked line by line against `sdk.d.ts`

| Emitted | Declared | Match |
|---|---|---|
| `{ matcher: '^Bash$', timeout: 10, hooks: [...] }` | `HookCallbackMatcher { matcher?: string; hooks: HookCallback[]; timeout?: number }` (L828-833; `timeout` doc-commented "in seconds", and the emitted value is `10`, consistent) | yes |
| `{ hookSpecificOutput: {...} }` wrapper | `SyncHookJSONOutput.hookSpecificOutput?: PreToolUseHookSpecificOutput \| ...` (L7143-7157) | yes |
| `hookEventName: 'PreToolUse'`, `permissionDecision: 'deny'`, `permissionDecisionReason: string` | `PreToolUseHookSpecificOutput = { hookEventName: 'PreToolUse'; permissionDecision?: HookPermissionDecision; permissionDecisionReason?: string; ... }` (L2332-2338) | yes |
| `'deny'` as a legal decision | `HookPermissionDecision = 'allow' \| 'deny' \| 'ask' \| 'defer'` (L841) | yes |
| Pass returns `{}` | every field of `SyncHookJSONOutput` is optional, so `{}` is a valid `HookJSONOutput` | yes |
| Input reads `input.hook_event_name`, `input.tool_name`, `input.tool_input`, `input.cwd`, `input.agent_id` | `PreToolUseHookInput = BaseHookInput & { hook_event_name: 'PreToolUse'; tool_name: string; tool_input: unknown; tool_use_id: string }` (L2325-2330) plus `BaseHookInput.cwd`, `.agent_id` (L164-176), all snake_case | yes |
| Claim that `{ behavior: 'deny', message }` is `canUseTool`-only | `PermissionResult` (L2191-2203) is the return type of `CanUseTool` (L266: `=> Promise<PermissionResult \| null>`) | yes, and the hook does **not** return it |

The specific fail mode named in the judging brief (a hook returning the `canUseTool`
`PermissionResult` shape) is not present, and the output calls it out explicitly as the
thing to avoid. The output's supporting citation is real: the doc comment on
`SDKPermissionDeniedMessage` (L4337) states "Denials that resolve before canUseTool runs
— PreToolUse hook denies, and deny-rule overrides of hook allow/ask decisions — are not
covered here," which independently confirms hook-before-`canUseTool` ordering. The
`BaseHookInput.agent_id` doc comment (L173-175) likewise confirms hooks fire from inside
subagents.

## The decisive test from the scoring notes

*If `Bash` were added to `allowedTools` tomorrow, would the deny-list still run?*

**Yes.** The deny-list lives in `makeBashGuard`, registered under `hooks.PreToolUse` with
matcher `^Bash$`. Hook dispatch is keyed on tool name, not on permission state, and
`PreToolUse` resolves ahead of permission evaluation (confirmed by the `sdk.d.ts` L4337
doc comment above). Adding `Bash` to `allowedTools` changes which calls reach
`canUseTool`; it does not change which calls reach the hook. The guard would still fire
and still return `permissionDecision: 'deny'`.

This is the point where the plausible hybrid would have failed, and it does not occur
here. `guards.js` puts the full policy evaluation inside the hook (`evaluateBash` →
`checkCommand`), with `onDecision` used only for the audit log. The `canUseTool` callback
in `agent.js` re-runs the same `evaluateBash` as a second, explicitly secondary gate. The
enforcement is not delegated to it.

## MUST tally

**4 / 4 MUST passed.** SHOULD: 2 / 2.

## Verdict: PASS

## Observations

This is a clean pass on the defect the case was built to guard, and the pass is not
incidental: the output names the trap in its first paragraph, explains the mechanism
("`canUseTool` is the *last* step in permission evaluation"), and puts the deny-list in
the layer that carries the guarantee. Assertion 4 is the strongest part. The deny return
shape matches `PreToolUseHookSpecificOutput` field for field, the input reads use the
declared snake_case names, the matcher object matches `HookCallbackMatcher`, and the
"pass returns `{}` rather than `permissionDecision: 'allow'`" choice is both type-valid
and semantically right, since an `allow` would short-circuit later checks. The output
also volunteers that its own orientation notes had the return shape wrong and that it
corrected them against `node_modules`, which is the tier-1 resolution the assertion asks
for rather than recall. Three of its four supporting citations were spot-checked in
`sdk.d.ts` and all held, including the non-obvious `SDKPermissionDeniedMessage` doc
comment used to establish ordering.

Two things worth flagging that no assertion covers. First, the `canUseTool` backstop in
`agent.js` returns `{ behavior: 'allow' }` for every tool that is not `Bash`, which
auto-approves anything the allow-list did not resolve; that is more permissive than the
security framing of the rest of the file and would deserve a comment in real use. Second,
the output is candid that it could not determine whether a hook that throws or exceeds
its `timeout` fails open or closed, and that this bears directly on the "no exceptions"
requirement. That is the honest disclosure, not a gap in the deliverable, and it is
paired with a concrete way to settle it empirically. The scope expansion to
`Write`/`Edit`/`NotebookEdit` is justified in the text (the same denied roots are
reachable through file-writing tools) and marked as removable, so it reads as a
defensible judgment call rather than unrequested work.
