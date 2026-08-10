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

# Verdict: audit-depth (deep companion run)

Scope: assertions 6 and 7 only. Assertions 1-5 belong to the quick-pass half and are marked `na`.

Output judged: `C:\Users\alfio\AppData\Local\Temp\claude\D--Projects-alfio-claude-plugins\10016771-ecb3-4b02-a328-463a9cd8e542\scratchpad\evalrun\out\audit-depth-deep.md`

## Scores

| # | Type | Outcome | Evidence |
|---|---|---|---|
| 1 | MUST | na | scored in the quick-pass half |
| 2 | MUST | na | scored in the quick-pass half |
| 3 | MUST | na | scored in the quick-pass half |
| 4 | SHOULD | na | scored in the quick-pass half |
| 5 | SHOULD | na | scored in the quick-pass half |
| 6 | MUST | pass | Named explicitly as a heading at line 3: "## Pass selected: deep", and restated after the trigger analysis at line 12: "Deep pass, full sequence." The pass is also *used*, not just declared: the output runs contract extraction (blocked, with the seven fields enumerated), archetype classification, dimension selection, threat model, reference baseline, semantic-diff scope, hardening, eval plan, and epistemic labels. |
| 7 | MUST | pass | Both appear as reasons for depth and as analyzed risk surfaces. Reasons: "it drives a tool loop" and "it takes untrusted input", under "Four of the deep-pass triggers fire at once, any one of which would be enough". Risks: two separate enumerated failure sets, "**From the untrusted channel:**" (5 threats incl. "Delimiter escape", "Second-order injection") and "**From the tool loop:**" (5 threats incl. "Double refund on ambiguous failure. The write call times out, the agent retries, the first one had landed."). Both also drive concrete artifacts: `<trust_boundary>` and the no-retry rule "If issue_refund returns an error, a timeout, or anything you cannot parse: do not call it again." |

## Result

MUST passed: **2 / 2 scored**

Verdict: **PASS 2/2**

## Observations (not scored)

The user never pasted the prompt to be improved, and the run handled this well. It named the gap immediately under its own heading ("## What I cannot do yet, and why it matters"), tied it to the process ("Step 1 of the audit process is contract extraction, and it operates on the prompt text"), and refused to fabricate: "I am not going to write a 'rewrite' of a prompt I have not read and present it as an improvement." It then split the deliverable explicitly, requested the artifact plus a seven-field contract table, and singled out the two genuinely blocking fields (interface, known failure modes) with reasons rather than listing all seven as equally urgent.

Crucially, it did not use the missing artifact as an excuse to stop. Everything determinable from the deployment description alone was delivered in full: archetype, the 10-of-11 applicable dimensions with `Creative latitude` marked N/A as a deliberate exclusion, the threat model, a reference baseline, the hardening items that cannot live in prompt text (nonce delimiters, server-side ceiling, idempotency keys), an eval plan, and two ready-to-run test inputs. The one real trap here is presenting a reference prompt as a rewrite, and the run defused it twice: "Read this as a **design target to diff your prompt against**, not as your rewrite" and "the honest result is 'no material optimization warranted'". It also withheld rubric numbers on principle: "a score written against a prompt I have not read would be decoration." That seems right; the alternative (either refusing outright or inventing a diagnosis of an unseen prompt) would be worse on a money-moving agent.

Two smaller notes. The reasoning-pattern decision is *recorded as a decision not to apply one* (ReAct considered, rejected, with the two constraints it contributes expressed as policy instead), which is a stronger outcome than either silently skipping or bolting on a scaffold. And the RUN-ACCOUNTING line shows `references/reasoning-patterns.md` was read on this run. That is the inverse of assertion 2, which forbids reading it on the quick half; here it is consistent with the deep pass and with the reference being load-bearing for the recorded decision, so it is not a defect. Nothing scored turns on it.
