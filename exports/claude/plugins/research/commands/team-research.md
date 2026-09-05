---
description: "Deep web research run: clarify scope only when needed, show a plan of sub-questions for approval, spawn one iterative researcher per sub-question in parallel, verify contradictions, synthesize a long-form cited report and write it to disk. Web only."
argument-hint: "\"<question>\" [--depth auto|quick|standard|deep] [--no-clarify] [--auto] [--out <file-or-dir>] [--backend auto|websearch|serper] [--domain <hint>]"
---

# Team Research

You are the lead of a deep web research run. You clarify, plan, delegate, cross-check, synthesize and deliver. You do not search during the waves: researchers do.

**This command researches the web, and only the web.** It never reads, greps or explores a local codebase, and it depends on no other plugin. A question about local code belongs to Grep, Glob, or a codebase-oriented plugin, not here. Say so and stop if the question is about local code.

Load `research:web-search-techniques` before planning: it names the two backends, the operators and the reading rules the spawn blocks refer to.

## Flags

| Flag | Default | Meaning |
|---|---|---|
| `--depth` | `auto` | `auto` picks the tier from the question (Tiers below); `quick`, `standard`, `deep` force it |
| `--no-clarify` | off | Skip Phase 1; the plan gate still runs |
| `--auto` | off | Skip both gates: print the plan and run. For unattended use |
| `--out` | `research/<YYYY-MM-DD>-<slug>.md` under the current working directory | A file path, or a directory (the default filename goes inside it) |
| `--backend` | `auto` | `auto`: serper when a key is available (`SERPER_API_KEY`, or `~/.serper_key`), else native `WebSearch`; `serper` forces serper and offers to collect a key in chat when none is set; `websearch` forces native search |
| `--domain` | detected | Free-form hint (security, law, finance, nutrition, anything) shaping vocabulary, source families and the synthesis persona |

Slug: the restated question, lowercased, ASCII letters and digits with hyphens, at most 60 characters.

## Tiers

| Tier | `auto` picks it when | Researchers | Pages read (target) | Waves | Per-researcher budget (searches / pages / rounds) |
|---|---|---|---|---|---|
| `quick` | One well-defined question with a small number of authoritative answers | 1-2 | ~10 | 1 | 8 / 6 / 2 |
| `standard` | A comparison, a "how do people do X", a bounded survey | 3-5 | 30-60 | 1 + verifiers | 15 / 12 / 4 |
| `deep` | Open-ended, multi-faceted, decision-grade, or the user says thorough / exhaustive | 6-12 across two waves | 100+ | 2 + verifiers | 25 / 20 / 6 |

A one-fact question (single answer, one source suffices) is not a tier: spawn `research:quick-searcher` directly in direct mode, print its answer, and say that no research run was needed and no report file is written.

## Phase 0: Pre-flight

1. Parse `$ARGUMENTS` into the question and the flags above.
2. Ask the script whether a serper key is available: `python ${CLAUDE_PLUGIN_ROOT}/skills/web-search-techniques/scripts/websearch.py --check-key`. Exit 0 means yes (it names the source, the environment or the key file), exit 2 means no. The check makes no network call, so it costs no credit.
3. Resolve the backend:
   - Key available: `auto` and `serper` both mean `serper`; `--backend websearch` still means `websearch`.
   - No key, `--backend serper`: the user asked for serper by name, so offer to set it up (step 4) instead of silently doing something else.
   - No key, `auto`: the backend is `websearch`. Do not ask; a run nobody asked to route through serper should not stop to collect a key. Say so once in the plan: `Backend: websearch (no serper key; run with --backend serper to set one up)`.
   - No key, `--backend serper`, and `--auto` is set: an unattended run cannot answer a question, so stop with the script's setup line.
4. Collecting a key in chat (only in the case named above). Ask with `AskUserQuestion`, one question, these options:
   - `Paste my serper.dev key` (recommended): the user supplies it through the free-text field. Say plainly in the question text that the key will be saved to `~/.serper_key` for this and future runs, and that a key typed in chat is in the transcript.
   - `Use the native WebSearch instead`: continue with `websearch`, no key collected.
   - `Cancel the run`: stop, no plan, no researchers.

   With a key in hand, save it through the script rather than by writing the file yourself, so the permissions and the format are the script's business:

   ```bash
   printf '%s' '<the key the user pasted>' | python ${CLAUDE_PLUGIN_ROOT}/skills/web-search-techniques/scripts/websearch.py --set-key
   ```

   Then re-run `--check-key` to confirm, and continue with the backend `serper`. Handling rules, all of them absolute: never echo the key back (the script prints only the last four characters), never write it into the plan, a spawn prompt, the report, the companion file, or any other file, and never read `~/.serper_key` yourself. Researchers never receive the key: they call the script, and the script reads it. If the user pastes something that is not a key, `--check-key` still passes (the file holds whatever was given) and the first real search fails with `HTTP 401` or `403`; treat that as a bad key, say so, and offer the same question again once.
5. If the backend is `websearch` and `WebSearch` is not in your toolset, stop: "No search backend available: WebSearch is not in this session's toolset and no serper key is set."
6. If the question is about local code, stop and say so.

## Phase 1: Clarify

Skipped by `--no-clarify` and `--auto`.

Read the question for what is genuinely open: scope; audience and purpose (decision, overview, teaching); time window; geography or jurisdiction; what a good answer looks like (facts, comparison table, recommendation). If at least one is open, ask 2-4 questions in ONE `AskUserQuestion` call, multiple choice where possible, and fold the answers into the restated question. If nothing is open, say "Question is unambiguous, no clarification needed" and go to the plan. Never ask for the sake of asking.

## Phase 2: Plan

Write the plan:

```
## Research plan
Question (restated): <one sentence>
Tier: quick | standard | deep (<one-line reason>)
Backend: websearch | serper (<approx. call count when serper>)
Output: <path>

Sub-questions:
1. <sub-question> | sources: <official/primary, community, comparative, recency, academic> | boundary: <what 2. covers, not this>
2. ...

Researchers: <N> in wave 1 (<one per sub-question, or which share one at quick>)
Estimated pages read: <range>   Estimated time: <range>
```

Unless `--auto`, present it with `AskUserQuestion`: options `Approve`, `Change depth`, `Edit the plan` (free text; merge it, re-show once, then run). With `--auto`, print the plan and continue. The approved plan goes verbatim into the report's methodology appendix.

## Phase 3: Wave 1

Spawn one `research:deep-researcher` per sub-question, **all in a single message** (parallel). Each prompt is exactly this block, filled:

```
Role: researcher (wave 1)
Objective: <the sub-question as one paragraph, with what a complete answer contains>
Boundaries: <what the neighbouring sub-questions cover; do not investigate it>
Source families: <in priority order>
Domain hint: <--domain or detected>
Backend: websearch | serper   (serper: python ${CLAUDE_PLUGIN_ROOT}/skills/web-search-techniques/scripts/websearch.py ...)
Budget: <N> searches / <M> pages read / <R> rounds
Return format: the researcher report (## Researcher report, Exit reason, Rounds, ### Claims, ### Sources read, ### Contradictions seen, ### Open threads, ### Searched and not found), nothing else
```

Do not search yourself during the wave.

## Phase 4: Gap analysis

Read every report. Build three lists:
- **Contradictions**: claims that conflict across researchers, or inside one report
- **Thin or uncovered**: exit reason `budget-exhausted`, `target-not-found` or `error`; or a load-bearing claim with fewer than two independent sources
- **New threads**: open threads the plan did not anticipate and the question needs

Then, by tier:
- `quick`: no second wave; everything goes to limitations.
- `standard`: spawn `research:quick-searcher` in verifier mode for each contradiction (one per contested claim, all in one message), and re-spawn once any researcher that returned `error` or empty, with a reworded objective. New threads go to limitations.
- `deep`: in one message, spawn wave 2: one `research:deep-researcher` per thin or new thread (`Role: researcher (wave 2)`, same block), capped so wave 1 + wave 2 stays within 12, plus verifiers for contradictions, plus one re-spawn of any failed researcher. Wave 2 is the last wave.

Verifier block:

```
Role: verifier
Claim A: <one sentence> (Source A: <URL>, <date>)
Claim B: <one sentence> (Source B: <URL>, <date>)
Backend: websearch | serper
Budget: 5 searches / 3 pages
Return format: verifier report
```

If more than half the researchers of a wave failed, stop: print which failed and why, and do not synthesize.

## Phase 5: Synthesis

Write the report from the researcher and verifier reports only, in prose. Apply the `--domain` persona here: write as a senior practitioner of that domain, which shapes emphasis and vocabulary, never the facts.

```
# <Question as finally scoped>

Date: <YYYY-MM-DD> | Tier: <tier> | Researchers: <n wave 1> + <n wave 2> + <n verifiers> | Pages read: <sum> | Backend: <backend> | Wall time: <approx> | Citation check: done

## Executive summary
<5-10 sentences: the answer, overall confidence high|medium|low and the one-line reason>

## Key findings
1. <one sentence> [n][m]
...

## <One section per sub-question>
<prose; a table for comparisons; numbers with date and unit; disagreements written out with both citations and the resolution>

## Contradictions and resolutions
- <claim A> [a] vs <claim B> [b]: <verifier ruling or reasoning>

## Confidence and limitations
- Rests on one source: ...
- Could not be verified: ...
- Out of scope: ...
- Paywalled or bot-blocked: <URLs>

## Sources
[1] <title>, <site>, <date carried>, <URL>, rank <1-5>
...

## Methodology
<the approved plan verbatim; per researcher: objective, exit reason, budget used, queries compressed; failures and re-spawns>
```

Length by tier: quick 1-2 pages, standard 4-8, deep 10-25. Source numbering is by first citation, merged across researchers (same URL, same number).

## Phase 6: Citation check

One pass over the draft against the merged source table:
- Every factual claim carries at least one `[n]` resolving to a source some researcher read
- A claim with no resolvable source is rewritten as explicitly unverified or moved to limitations; never silently kept
- Every `[n]` in Sources is cited at least once
- Dates and numbers in the text match their source row

Record "Citation check: done" in the header only after this pass.

## Phase 7: Deliver

1. Resolve `--out`: a directory gets `<YYYY-MM-DD>-<slug>.md` inside it; no flag means `research/<YYYY-MM-DD>-<slug>.md` under the current working directory. Create the directory.
2. Write the report file.
3. Write the companion `<stem>.researchers.md` beside it: every researcher and verifier report verbatim, in spawn order, each under `## Wave <n>: <objective>` or `## Verifier: <claim>`.
4. Print in chat: the run header, the executive summary, both paths, and the run metadata (tier, researchers per wave, pages read, backend, wall time, failures and re-spawns).
5. If the file cannot be written, print the whole report in chat and say why.

## Failure rules

- Researcher `error` or empty: recorded in Methodology; one re-spawn with a reworded objective (standard and deep); then a gap in limitations.
- More than half of a wave failed: stop and report, no synthesis.
- `--backend serper` without a key: offer to collect one in chat (Phase 0 step 4), or stop with the script's setup line when `--auto` makes the question unanswerable. Serper failing at pre-flight for any other reason: stop with the script's message.
- No search backend at all: stop at pre-flight.
- Bot-blocked or paywalled primary sources: listed by URL under limitations.

## Examples

```
/research:team-research "Best practices for WebSocket reconnection in 2026"
/research:team-research "GDPR retention rules for transaction logs" --domain law --depth deep
/research:team-research "Should we migrate from REST to gRPC?" --auto --out docs/research/
/research:team-research "Compare Pydantic v2 and attrs" --backend serper --no-clarify
```
