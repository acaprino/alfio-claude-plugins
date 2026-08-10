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

# Verdict: progressive-disclosure

Output judged: `scratchpad\evalrun\out\progressive-disclosure.md`
Case: `D:\Projects\alfio-claude-plugins\evals\ai-tooling\cases\progressive-disclosure\case.md`

The RUN-ACCOUNTING line is the evidence base for assertions 1-3. Verbatim, in full:

> `RUN-ACCOUNTING: files_read=C:\Users\alfio\.claude\plugins\cache\claude-code-daodan\ai-tooling\5.0.1\skills\agent-sdk-builder\SKILL.md, C:\Users\alfio\.claude\plugins\cache\claude-code-daodan\ai-tooling\5.0.1\skills\agent-sdk-builder\references\sessions-subagents.md, C:\Users\alfio\.claude\projects\D--Projects-alfio-claude-plugins\10016771-ecb3-4b02-a328-463a9cd8e542\tool-results\toolu_01VN9Fwkk9DgxhBuTGmg8MUA.txt`

Three files total: the skill core, exactly one reference, and one transcript/tool-result artifact that is not a skill reference.

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | pass | `...\skills\agent-sdk-builder\references\sessions-subagents.md` appears in `files_read`. |
| 2 | MUST | pass | The only path under `references\` in `files_read` is `references\sessions-subagents.md`. Zero other references were opened, so the "at most one other" ceiling is not approached. The permitted `permissions-hooks-security.md` exception was not needed even though the answer discusses permission modes and `PreToolUse`. |
| 3 | MUST | pass | Neither `deployment.md` nor `mcp-plugins-skills.md` occurs anywhere in `files_read=...SKILL.md, ...references\sessions-subagents.md, ...tool-results\toolu_01VN9Fwkk9DgxhBuTGmg8MUA.txt`. |
| 4 | SHOULD | fail | No quote available. The output opens straight into the answer, "Both are fields on the subagent's `AgentDefinition`, inside the `agents` option you pass to `query()`", and never names the question's shape or the routing decision. Its section headers are `## Environment`, `## TypeScript`, `## Python`, `## The per-agent fields worth knowing`, `## Six things that actually bite`, `## Provenance`: none states which branch of the core's decision tree applied. The accounting shows `SKILL.md` read before `sessions-subagents.md`, which is consistent with core-first routing, but the assertion requires the shape to be *named*, and it is not. |
| 5 | SHOULD | pass | Option names were resolved past the bundled reference and the resolution path is stated: "I could not inspect an installed SDK for this run: `npm ls -g` and `pip show claude-agent-sdk` found nothing... So every API-sensitive detail below comes from the current official documentation rather than from the types you will actually compile against." The itemization follows: "Verified against the current official docs today (`/agent-sdk/subagents`, `/agent-sdk/python`, `/agent-sdk/permissions`, `/agent-sdk/hooks`): the full `AgentDefinition` field list and types, the model alias set including `fable` and `inherit`, the `Agent`-in-`allowedTools` requirement..." |

MUST passed: 3 / 3
SHOULD passed: 1 / 2

**Verdict: PASS 3/3 MUST** (assertion 4 missed as a SHOULD).

## Observations

The case is scoreable exactly because the RUN-ACCOUNTING line exists, and on the three MUST assertions the run is not marginal: it opened one reference out of five, the correct one, and did not even spend the permitted second read on `permissions-hooks-security.md` despite the answer covering permission-mode inheritance and `PreToolUse` hooks at length. That content came from `sessions-subagents.md` and the docs rather than from a second reference, which is the selective-loading behavior the 5.0.0 split was supposed to buy. The third entry in `files_read` is a `tool-results\toolu_*.txt` transcript artifact, not a skill file, so it does not count against assertion 2 and does not disturb assertion 3.

Assertion 4 fails on the literal reading requested. The read order in the accounting (core, then one reference) is circumstantial evidence that the core's decision tree did the routing, but the assertion asks for the routing to be *visible*, with the shape named before the reference is opened, and no sentence in the output does that. The output reads as a finished answer with no trace of how the file selection was made. Two assertions here are checking different things (correct selection vs. legible selection), and this run demonstrates the first without the second.

Assertion 5 passes, with one caveat worth recording. The output does not merely repeat the reference: it declares the installed SDK unavailable, names the probes it ran (`npm ls -g`, `pip show claude-agent-sdk`), falls back to current docs, cites four doc paths, and then separates verified claims from one explicitly unverified interaction (whether a parent-level `disallowedTools` deny binds a subagent's own `tools` list) and from version-sensitive behavior (background-by-default at v2.1.198, nesting default moving between v2.1.172 and v2.1.219). Details like the `fable` alias and those version numbers are not the kind of thing a static bundled reference would supply as-is. The caveat: `files_read` records only file opens, so a judge cannot confirm from the accounting alone that the doc fetches happened; the single `tool-results` artifact is consistent with a fetched payload but does not prove it. Scored pass on the strength of the itemized, falsifiable provenance in the output text, which is what the assertion asks about.
