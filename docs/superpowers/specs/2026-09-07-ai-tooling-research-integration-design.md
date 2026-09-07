# ai-tooling research integration (September 2026) - Design and record

Date: 2026-09-07
Status: executed in the same pass; this document is the record
Plugin: `ai-tooling` v5.2.0 -> v5.3.0 (integration), then v5.3.0 -> v5.4.0 (the peer-review verdict applied); marketplace 27.3.0 -> 27.4.0, then 27.4.0 -> 27.5.0

## Goal

The 2026-09-05 refresh (`2026-09-05-ai-tooling-prompt-engineering-refresh-design.md`) covered
reasoning scaffolds, structured output, extraction and vendor guidance. It left the
`prompt-engineer` rubric naming eight archetypes while the knowledge base served three, and it
left several numbers in the role with no source: "8-12 rules", the shot-count rule, the
headings-suffice half of the XML rule, the subagent summary length. This pass ran one deep
research question against the task families and questions the knowledge base did not cover, with
the covered sources listed in the prompt as out of scope, and integrated what came back.

## Research

One `/research:team-research` run at `deep`, eight fixed sub-questions: a technique-to-task map,
judge and evaluator prompts, agent instructions and tool descriptions, instruction-following
capacity by model size, prompt format and role by model family, long-context and
retrieval-grounded prompting, generation task families, multimodal and multilingual prompting.
Every claim was required to carry model, task, metric, effect size, baseline and source status,
and "not measured on this class" was declared a finding.

Before integration, every source behind a rule that entered the knowledge base was verified
against its arXiv page or journal page by three parallel verifier agents (25 sources, each
capped at three fetches). Every number was found in its source. Seven precisions were applied:
the coding-agent rule study was retitled in v2 and its gain is 6.9 to 13.8 points over a 50.0%
baseline; the "11 of 12 models" claim in ManyIH-Bench is 11 of 12 model-transition pairs across
six models (the claim was dropped from the knowledge base rather than restated); the
instruction-multiplication paper states EMNLP 2025, not Findings; the hardware-agent Gemma
collapses are Gemma 4 31B and Gemma 4 E4B by name; the reference-guided judge result uses
frontier-written references; the persona ideation study measures within-session fixation, not
persona reuse; the technique-aging paper's sign change holds on average with one run still
negative. One venue could not be confirmed on arXiv (the multilingual checklist paper's
workshop) and carries *(verify)*.

**The evidence is committed, not summarized.** Three files sit beside this record and carry the
same date, per the retention rule in the `custom-plugin-refresh` skill:

| File | What it holds | sha256 of the body |
|---|---|---|
| `2026-09-07-ai-tooling-research-prompt.md` | the deep-research prompt as it was run, with the `already_covered` block that makes its negative findings meaningful | `571b670e…76de` |
| `2026-09-07-ai-tooling-research-report.md` | the researcher's report verbatim, as a transcript rather than as the knowledge base | `c18b3461…cc85` |
| `2026-09-07-ai-tooling-source-verification.md` | the three verifiers' per-source tables, including the five sources nobody verified | `6ddb4523…5702` |

The paragraph above says every source behind a rule was verified. That sentence is true and it is
not sufficient: it cannot tell a later maintainer which five sources were never checked, nor that
one of them, arXiv 2507.05424, carries a four-model claim in the `prompt-engineer` role. The
verification file can, and the claim is now marked `*(verify)*` where it is cited. This gap was
finding F04 of the peer review recorded at the end of this document.

## Findings, classified per the `custom-plugin-refresh` protocol

| Finding | Class | Where it landed |
|---|---|---|
| Joint constraint compliance saturates early: all-constraints success below 50% at 2 to 7 constraints across fifteen current models, 40.7% per-constraint against 5.7% all-eight at k=8 (arXiv 2608.12426); Gemini-1.5-Pro 99% alone to 20% composed (arXiv 2509.21051, EMNLP 2025) | clear win, replaces an uncited number | the over-constraining anti-pattern in the role ("8-12 rules" retired), a constraint-count check in the command, a fact anchor on the working threshold, eval case `constraint-saturation` |
| A coding-agent rule file is the exception: 50 rules did not collapse Opus 4.6 on SWE-bench, prohibitions carried the gain, positive guidance hurt (arXiv 2604.11088 v2) | clear win | `agent-instructions.md`, the anti-pattern's exception line, the command's constraint-count check |
| Judge prompt shape: one criterion, binary with evidence (GPT-5.4 about 91% balanced accuracy, arXiv 2606.29920, EMNLP 2026); 0-5 over 0-10 pooled, reversed on MT-Bench (arXiv 2601.03444); frontier-written references +4.9 to +8.4 on small judges (arXiv 2602.16802, ICLR 2026); checklists +0.13 and +0.21 at 7B (arXiv 2507.06774); debate never beat its strongest member, personas cost weaker judges up to 11.9 points (arXiv 2606.07810) | clear win, new archetype coverage | new `judge-prompting.md`, role capabilities and prompt-evals, command judge check and honesty note, eval case `judge-prompt-shape` |
| Tool-description anatomy: enrichment +5.85 median success and +67% steps, examples removable at no cost (arXiv 2602.14878 v3); few-shot in a tool agent's system prompt collapses Gemma 4 E4B and 31B; Llama-3.1-8B 0.445 task-scoped against 0.157 cumulative history (arXiv 2608.26199); verified state 69% to 78% where prompt persistence fell to 3 of 9 at 100 items (arXiv 2605.23574) | clear win, new archetype coverage | new `agent-instructions.md`, role agentic section |
| Test generation in a fresh context: 25% against 14% fault detection, +7.9 to +17.7 per model (arXiv 2607.05139) | clear win | `agent-instructions.md` coding section |
| Shot count is per model: Llama-3.1-8B 0.53 to 0.87 at two shots and 0.55 at eight, Llama-4-Scout best zero-shot (arXiv 2607.22969 v1, one task) | subtle shift: the vendor's 3-5 stays for Claude, elsewhere sweep | role examples section, SKILL.md model-class table |
| Similarity-retrieved exemplars for transformation tasks (arXiv 2506.05614); technique effects reverse across model generations (arXiv 2608.24641, ICSME 2026) | clear win | role examples, SKILL.md shared rules, `agent-instructions.md` |
| No universal prompt syntax: JSON 0.901, plain 0.886, an LLM rewrite 0.748 on GPT-4o HumanEval (arXiv 2608.21074 v1); format spread 0.161 to 0.190 on 8B models against 0.032 on GPT-4.1 (arXiv 2508.11383) | clear win, labels the headings half of the XML rule | role XML section |
| Persona changes depth and clarity, not accuracy (arXiv 2605.29420 v1); heterogeneous personas partition ideation, 39.15 to 56.97 (arXiv 2602.20408 v1) | clear win | role persona section |
| Rule order has no measured effect on non-conflicting constraints; priority encoding is fragile (ManyIH-Bench, arXiv 2604.09443) | subtle shift: "highest-priority first" kept for the reader, labelled | role positioning |
| Retrieval abstention: assess-first raised abstention to 47.9% on GPT-5.5 and 55.2% on Gemini 2.5 Flash but 11.2% on Claude Sonnet 4.6, over-answering above 65% everywhere (Zhang and Wu, CMC 89(1), 2026-08); prompt-based abstention still answered 41.6% on small models (arXiv 2608.22228); lost-in-the-later persists (arXiv 2507.05424) | clear win | role context-engineering section |
| Prompt language: Italian ahead of English on two of three GPT-4o-mini coding settings (arXiv 2607.14816 v1) | clear win, closes a tempting shortcut | role language section, command language check, eval case `prompt-language-preserved` |
| Modality order follows the reasoning's dependency structure (Wardle and Susnjak, BDCC 9(6):149, 2025), older non-reasoning class only | clear win, labelled ON-only | role language and modality section |
| Not measured in the window: pointwise against pairwise, judge confidence elicitation, parameter-naming ablations, trigger-phrase calibration, progressive disclosure against full loading, orchestrator brief and summary formats, a universal prompt-syntax winner, a current-model many-shot optimum, quote-first and citation instructions, Chain-of-Density successors, refusal and escalation phrasing, current-model scanned-PDF and audio prompting, English-versus-Italian system prompts | open question, recorded as such | the "not measured" lines in both new references and the role |

## Decisions worth recording

- **The 3-to-5 threshold is a synthesis, and the text says so.** The saturation paper reports
  per-model half-lives from 2 to 7; no paper optimized a working threshold. The role states the
  band and labels it this plugin's reading of the curves. A fact anchor guards the number so a
  later edit cannot drift it in one file.
- **The judge and agent references are Slow, not Model-sensitive.** Their numbers are dated and
  model-named like every other reference, but the shapes (decompose, reference, checklist;
  purpose, guidance, parameters) are expected to outlive a model generation, the way the
  enforcement ladder does.
- **Unmeasured cells stay unmeasured.** Vendor architecture (Agent Skills' progressive
  disclosure, the 1,000 to 2,000-token summary) is kept as guidance and labelled, not promoted to
  a measured rule because it is plausible.

## Versioning

- `plugins/ai-tooling/plugin.toml`: 5.2.0 -> 5.3.0 (minor: two new references, three new checks
  in the command)
- `.claude-plugin/marketplace.json` `metadata.version`: 27.3.0 -> 27.4.0
- Commit: `Integrate 2026-09 prompting research into ai-tooling: judge and agent references,
  constraint saturation, per-model shot and format rules (v5.3.0)`

## Peer review, 2026-09-07

The integration was put on trial the same day, through `/peer-review:review` in brief mode: the
session's twenty taken decisions and four open ones were materialized into a frozen brief and sent
to `gpt-6-astra` at `reasoning_effort: max`. Full run under `.peer-review/2026-09-07-1353-session-brief/`,
which git does not keep; the verdict is reproduced in what follows.

The challenger raised eight findings. **All eight were accepted.** Nothing was refuted, nothing
stood off, nothing was untestable. Two of them (F02, F03) were contested by the respondent in
round 1, restated more narrowly by the challenger in round 2, and then accepted, which is the only
part of the run where both sides moved.

| Finding | What it attacked | What changed |
|---|---|---|
| F01 | The rule-file exemption rests on a study that scores task pass rate and reports no rule-adherence metric, and the kernel exempts by file type with no applicability rule | The exemption is scoped to the guardrail rules in such a file; output obligations it carries count like any other simultaneous constraint. A mixed rule file joins the `constraint-saturation` eval case, and the study's two zero-rule baselines are labelled by experiment where they sit side by side |
| F02 | The constraint band is a heuristic for offering a variant, not a criterion for the reliability a caller needs; naming a rung chosen by parse-failure cost does not fix validation scope | The band says what it is for; a criterion is added for a named joint-success target or a machine-checkable constraint; the command now surfaces that domain validation runs after schema validation and fails closed on either |
| F03 | The same-language rule is unconditional at candidate generation and has no measured-case exit, though the band two paragraphs away has one | A measured-override clause in the role and the command; the eval case is scoped to its unmeasured setup |
| F04 | The refresh's evidence lives only in a git-ignored directory, and an unverified source is cited unmarked | The three files above; the citation is marked; the retention rule is in the refresh skill |
| F05 | The untrusted-candidate safeguard is stated only in the always-loaded role and no non-judge eval case exercises it | The safeguard stays in the role and the judge bullet stops restating the reference's figures; `archetype-creative` gains an assertion on the recommended eval |
| F06 | The fact anchor protects the upper trigger of a two-part escalation policy and not the lower one, proven by mutation | A second anchor on the verifier trigger; the unanchored restatement in `agent-instructions.md` is replaced by a pointer |
| F07 | The eval protocol offers the working-tree run and the installed-package run as exclusive alternatives, and no case has ever been run both ways | Protocol step 0 makes them stages, with the installed re-run required |
| F08 | The coding-agent section's ownership options were whole-section while the criterion is per bullet | A prose pointer on the fresh-context bullet, which needs no dependency declaration |

Two properties of that run are worth recording, because a later reader will otherwise take the
tally at face value.

**Eight for eight is not a measurement of the challenger's accuracy.** The respondent and the
brief's author share a session and a model. A respondent that concedes readily produces exactly
the same tally as a challenger that is always right, and this protocol cannot separate them.

**The brief was written by the side being judged.** Its own "could not be sharpened" list came
back empty, and eight accepted findings are the evidence that it should not have been. What the
challenger never saw is invisible to the verdict by construction.

One procedural note, kept because it is the kind of thing that reads as noise later: the first
round-1 transport call burned its entire output budget on reasoning and returned zero characters.
The packet was resent unchanged, with a higher cap, under the same consent, after re-checking its
digest against the consent-gate value.

### The verdict, applied in 5.4.0

All eight accepted changes were made the same day, one agent per owned file over a disjoint
partition, then verified by eight adversarial reviewers, one per finding, each reading the applied
diff and defaulting to "insufficient". Seven findings came back addressed on the first pass. F01
came back not addressed, and the reviewers between them found sixteen gaps that a self-review
would not have: three of the eight fixes had left an index row, a case assertion or a file header
still stating the rule the fix had just replaced, which is this repository's characteristic defect
appearing inside the change that was meant to remove it.

Two of those gaps are worth naming because they generalize.

**The evals index promised what the case forbids.** `evals/ai-tooling/README.md` summarized
`constraint-saturation` as "never applies that cap to an agent rule file" while the case's own new
assertions require exactly that inside a mixed file. An optimizer satisfying the index would fail
the case it indexes. The same shape appeared for `prompt-language-preserved`, whose index row and
whose header paragraph both still carried the unconditional form the assertions now scope.

**The anchor was weaker than its mutation test suggested.** The first attempt captured only the
band's lower bound, so rewording the upper bound, changing the required action, or restating the
band with a word-number in the non-owning file all passed silently. The pattern now spans both
bounds and the verb, and matches a count written either as a word or as digits, so a mutation
cannot escape the comparison by rewording. Eight mutations were run against it: lower bound, upper
bound and action, in the role and in the command, plus the upper trigger in both. All eight fail
the linter and the two files are byte-identical afterwards.

That pass also found a defect in the linter itself, unrelated to the plugin. It walks the
filesystem rather than git, so a peer-review run directory, which is git-ignored and holds an
external model's words that the protocol forbids editing, could fail the check on one machine
while CI stayed green. `.peer-review` is now excluded, for the reason the file already documents
about changelogs, at its strongest.
