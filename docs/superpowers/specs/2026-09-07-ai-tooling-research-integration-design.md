# ai-tooling research integration (September 2026) - Design and record

Date: 2026-09-07
Status: executed in the same pass; this document is the record
Plugin: `ai-tooling` v5.2.0 -> v5.3.0, marketplace 27.3.0 -> 27.4.0

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
