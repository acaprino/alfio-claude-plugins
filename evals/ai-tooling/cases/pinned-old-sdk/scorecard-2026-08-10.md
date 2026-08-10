<!-- Scorecard produced by an independent judge that read only this case file, the candidate
output, and (where the case needs it) the installed SDK types. It could not read
plugins/ai-tooling/, so it judged the output against the assertions rather than against the
implementation. -->

- **Date:** 2026-08-10
- **Plugin version under test:** ai-tooling 5.0.1, the INSTALLED plugin at
  `~/.claude/plugins/cache/claude-code-daodan/ai-tooling/5.0.1/`
- **How the component was exercised:** a fresh subagent adopted the installed component body and
  received only the case's Run text, never the assertions
- **Scored by:** a separate fresh subagent, given the case file and the output and nothing else

# Verdict: pinned-old-sdk

Candidate: `scratchpad/evalrun/out/pinned-old-sdk.md`
Setup as executed: project pins `0.2.90` exactly, `node_modules` deliberately absent, no install into the user's project permitted. Only the no-install half ran.

## Scores

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | **pass** | Stated in the opening section, before any code: "pins the SDK **exactly**: `\"@anthropic-ai/claude-agent-sdk\": \"0.2.90\"`, no caret." The script block appears two sections later. |
| 2 | MUST | **pass** | Names the resolving tier explicitly: "I downloaded the 0.2.90 tarball into a scratch directory and resolved every option against **that version's own `sdk.d.ts`**. Everything below is checked against the code you will actually run, not against the latest docs." Restated at the end: "Verified against the 0.2.90 type definitions themselves". |
| 3 | MUST | **pass** | Says the installed copy could not be inspected, and says what it did instead: "Nothing is installed yet, so there is no `node_modules` to read." / "Because I could not read an installed copy and could not install into your project, I downloaded the 0.2.90 tarball". Both halves of the honesty requirement are explicit: what it could not read locally, and the substitute route it took. |
| 4 | MUST | **pass** | Claims the capability *does* exist at 0.2.90 and shows the concrete basis rather than asserting it: quotes the pinned version's own doc comment, "In 0.2.90 its doc comment reads \"When true, resumed sessions will fork to a new session ID rather than continuing the previous session. Use with `resume`.\"", and enumerates the checked symbols, "Verified against the 0.2.90 type definitions themselves: `forkSession?: boolean` as an option, the standalone `forkSession()` function and its `{ sessionId }` return, `session_id` on the init message, `resume`, `resumeSessionAt`, `sessionId`, `maxTurns`, `maxBudgetUsd`, `getSessionMessages`, and the package's root export map." Also handled the opposite direction with a stated scope limit: "I also checked 0.3.226, where `forkSession` is still a boolean option ... I checked that one field, though, not the whole surface". |
| 5 | SHOULD | **pass** | Primary script uses resume plus the real fork flag, not an invented function: "resume: sourceSessionId," with "forkSession: true,". The second snippet's standalone `forkSession()` is a genuine 0.2.90 export, not an invention. |
| 6 | SHOULD | **na** | The with-install half of the case was not executed. |

**MUST passed: 4 / 4 MUST scored.**

**Verdict: PASS**

## Observations

The run's distinguishing move is that it did not treat "no `node_modules`" as a dead end and did not paper over it either. It stated the pin, stated that the installed copy was unreadable, stated that it was not allowed to install into the project, and then named the substitute artifact it did read (a tarball of the exact pinned version fetched into a scratch directory). That is the shape assertion 3 is testing: the reader can tell at all times which tier answered, and the answer here is "the pinned version's own types, obtained out-of-tree", never "the installed types" and never an unlabelled memory recall. The RUN-ACCOUNTING footer corroborates the narrative, listing the 0.2.90 and 0.3.226 `sdk.d.ts` files as downloaded and inspected and the pinned project's `package.json` as read, with no `node_modules` path among them.

I spot-checked the substantive claims against the 0.2.90 `sdk.d.ts` still present in the scratchpad, and they hold verbatim: `package.json` reports `"version": "0.2.90"`; `forkSession?: boolean` sits at line 1025 with exactly the quoted doc comment; the standalone `forkSession()` is declared at line 486 returning `Promise<ForkSessionResult>`; the "forked sessions start without undo history (file-history snapshots are not copied)" caveat and the `"<original title> (fork)"` title derivation are both lifted accurately from that file's comments; `resumeSessionAt`, `getSessionMessages`, `listSessions`, `getSessionInfo`, and `upToMessageId` all exist. So assertion 4's premise (the capability missing at the pin) never triggered, and the run's positive claim is both shown-verified and true.

Two things to flag rather than penalize. First, the explicit "Verified" list at the end is narrower than the claims the body makes: the options table is headed "Options worth knowing, all present in 0.2.90" but `upToMessageId`, `listSessions`, `getSessionInfo`, and the `title` option are absent from the verified enumeration, so on the page they read as asserted rather than as checked. They happen to be correct, but a reader auditing the tier boundary cannot tell that from the text alone. Second, one claim in the table is of a kind a `.d.ts` cannot settle: "`sessionId` ... Normally rejected alongside `resume`, but permitted precisely when `forkSession` is set" is a runtime validation rule, and the types only document it in prose at the `resumeSessionAt`/`sessionId` comments rather than encoding it. The run also claims both snippets "type-check clean under `strict`" without showing the command or its output, which is the one verification claim in the document with no artifact behind it in the visible text. None of these touch a MUST, and the run is unusually disciplined about the limits it does state (it says plainly that it executed nothing, that `ANTHROPIC_API_KEY` was unset, and that the 0.3.226 check covered one field only).
