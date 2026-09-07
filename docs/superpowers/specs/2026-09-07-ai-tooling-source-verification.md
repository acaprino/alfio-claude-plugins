# ai-tooling September 2026 refresh: source verification

Committed as evidence of the 2026-09-07 refresh, per the retention rule in the
`custom-plugin-refresh` skill, and as the fix for finding F04 of the peer review recorded in
`2026-09-07-ai-tooling-research-integration-design.md`.

**Why this file exists.** The design record states in one aggregate sentence that every source
behind a rule entering the knowledge base was verified. That sentence cannot tell a later
maintainer WHICH sources were checked, which were treated as background, and which carry a
claim in a shipped body without ever having been read. This file can. Five sources at the
bottom were not verified by any agent, and one of them, arXiv 2507.05424, does carry a
four-model claim in the `prompt-engineer` role, which is now marked unconfirmed in place.

sha256 of the body below: `6ddb45232293abaf37d7f05450b95cd92049b28f2fe54f31bae78b22d8495702`

---

# Source verification tables, 2026-09-07

Three parallel verifier agents, each capped at three fetches per paper, checked every source behind a rule that entered the ai-tooling 5.3.0 knowledge base against its arXiv abstract/HTML/PDF page or its journal page. Tables reproduced verbatim from the verifiers' reports.

## Verifier A (constraint and agent sources)

| ID | Title matches | Latest version, date | Venue stated | Numbers | Note |
|---|---|---|---|---|---|
| 2608.12426 | yes | v1, 12 Aug 2026 | No. Comments: "Reviewed in the ARR May 2026 cycle" | confirmed, all. Table 1 k*: GPT-5.5 7, Claude 4.7 Opus 6, Gemini 3.1 Pro 4, Claude 4.6 Opus 3, GPT-5.4 Pro 3, GPT-5.2 2, DeepSeek V4 Pro 3, Qwen 3 235B Inst. 2; 40.7% / 5.7% at k=8 (Fig. 1); mCSR(k)=72.0% x 0.922^(k-1); mean abs rho 0.029; 12 of 15 below 50% at k<=3; 36 types, 369,753 checks | k* is the paper's "compositional half-life" on sCSR; 0.922 is a fitted mean curve, not a per-model figure. |
| 2509.21051 | yes | v1, 25 Sep 2025 | Comments: "Accepted to EMNLP2025". Findings vs main track not stated | confirmed: "Characters per line" instruction 99% (Gemini 1.5 Pro) and 97% (Claude 3.5) alone, 20% and 2% combined with five others (StyleMBPP) | Cite as EMNLP 2025 unless Findings is verified elsewhere. |
| 2604.11088 | v1 yes; v2 retitled "Guardrails Beat Guidance: A Large-Scale Study of Rules, Skills, and Persistent Configuration for Coding Agents" | v2, 28 May 2026 | No | confirmed: Claude Code with Opus 4.6 on SWE-bench Verified; every rule condition beats the 50.0% no-rule baseline by 6.9 to 13.8 pp; random ties curated at 63.8% (+13.8 pp both); all shaping rules are negative constraints, all distorting rules positive directives; 20 pp drop removing "do not refactor unrelated code", McNemar p=0.016; 59 to 67% band from 0 to 50 rules, 66.7% vs 60.3% | Use the v2 title; write 6.9 to 13.8 pp rather than 7 to 14. |
| 2604.09443 | yes | v3, 14 Apr 2026 | No | partially. Confirmed: up to 12 levels, 853 tasks, ~40% (best Gemini 3.1 Pro 42.7%, GPT-5.4 39.5%); ordinal to scalar encoding: GPT 5.4 -8.4, Opus 4.6 -8.0 (Table 1b, Sec. 6.4). Contradicted: source says "Out of 12 model-transition pairs, 11 show a strict decrease" over 6 models and three variants (6, 8, 12 tiers), drops 6.8% (Qwen3.5-9B) to 24.1% (Sonnet 4.6) | Rewrite as 11 of 12 model-transition pairs across 6 models; ten models evaluated overall. |
| 2602.14878 | yes, short form of "Model Context Protocol (MCP) Tool Descriptions Are Smelly! Towards Improving AI Agent Efficiency with Augmented MCP Tool Descriptions" | v3, 31 May 2026 | No. PDF uses an ACM journal template, "Publication date: June 2026" | confirmed: MCP-Universe; GPT-4.1 18.18 to 29.44; Qwen3-Coder-480B-A35B 19.91 to 25.97 (Table 6, overall SR); median 5.85 pp SR, 15.12 AE, 67.46 steps, 16.67% regressions; "removing the Examples component does not statistically degrade performance" | The +15.12% is the Average Evaluator score, which the abstract calls partial goal completion. |
| 2605.23574 | yes | v1, 22 May 2026 | No | confirmed, all in the abstract: Claude Code (Sonnet 4.6) and Codex CLI (gpt-5.4) drop to 3 of 9 per condition at 100 artifacts; state-tracking retrieval controller 69 to 78% | The 69 to 78% is the state-tracking retrieval controller; a separate backlog controller reaches 25 to 50%. |
| 2608.26199 | yes | v1, 25 Aug 2026 | No | confirmed: Gemma 4 31B 0.956 to 0.571 and Gemma 4 E4B 0.731 to 0.179, Markdown prompt to few-shot (Table 8); Llama 3.1 8B 0.445 task-scoped vs 0.157 run-cumulative (Table 10); ECC = correctly executed expected calls / expected calls | Name the Gemma sizes (4 31B, 4 E4B) in the knowledge base. |

## Verifier B (judge-prompt sources)

| ID | Title matches | Latest version and date | Venue stated | Numbers | Note |
|---|---|---|---|---|---|
| 2601.03444 | yes | v1, 6 Jan 2026 | none | confirmed: pooled ICC 0.853/0.805/0.840 (Table 2); MT-Bench 0.517/0.570/0.470 (Table 4a); Qwen3-32B 0.731/0.684/0.714, DeepSeek-v3.2 0.696/0.670/0.624, GPT-4o 0.816/0.760/0.810, Gemini 0.782/0.749/0.784 (Table 4b) | "Gemini 2.5" is gemini-2.5-flash in Section 4.2; the paper also runs Llama-3.3-70B and Mistral-7B judges. |
| 2602.02219 | yes | v2, 24 Jun 2026 | none | confirmed: "score-option ordering" is the paper's term; Table 3 Balanced minus Fixed is Pearson r: +0.076 [+.047, +.105] Qwen3.5-27B on HANNA, +0.035 [+.014, +.055] Gemma-3-12B on SummEval; Section 5.3: about two-thirds of the K=1 to 10 gain by K=3, about 85% by K=5 | Gains are stated to hold mainly for judges with strong bias; absolute r values are not printed, only deltas. |
| 2606.29920 | yes | v2, 2 Sep 2026 | "Accepted to EMNLP 2026" (Comments) | confirmed: Table 2 Default prompt GPT-5.4 BAcc 91.4 deep research, 89.4 agentic coding; Default prompt is a yes/no judgment on one criterion; Table 3 Qwen3.5-27B Strict +11.8 on agentic coding; text: strict gives large gains to GPT-OSS-120B and Qwen3.5-27B, stronger models show smaller changes (GPT-5.4 and Gemini-3.1 Pro shift -0.3 to +1.0 on deep research) | Metric is balanced accuracy. Paper's word is "Default", not "simple binary criterion prompt", but the content matches. |
| 2606.07810 | yes | v1, 5 Jun 2026 | none | confirmed: 16 judges 0.6B to 14B; Phi-4 14B 89.55 (Table 2); RCR: "no debate beats the individual baseline of its strongest member"; best three-judge jury 89.61, 0.06 above best single judge; Lenient persona drops LLaMA-3.1-8B 10.20 points, Strict persona drops Phi-4-mini 11.91 | The jury result is the best of ten three-judge juries drawn from the top five, not literally "the three strongest". Top judges vary at most 0.55% under personas. |
| 2602.16802 | yes | v1, 18 Feb 2026 | "ICLR 2026 Camera Ready" (Comments) | confirmed: Table 2, average over five datasets (LLMBar-Natural, LLMBar-Adversarial, MTBench, InstruSum, HREF), GPT-4o references: Llama-3.1-8B 71.8 to 79.4, Mistral-7B-v0.3 61.2 to 69.6, Gemma-2-9B 80.8 to 85.7, Qwen2.5-14B 83.3 to 82.4 | Numbers are with frontier-model references; human references are tested separately on LLMBar-Adversarial only (Table 13). |
| 2507.06774 | yes | v2, 27 Jul 2025 | none on arXiv | partially: Qwen2.5-7B-Instruct judge confirmed; MM-Eval reasoning pairwise average 0.64 to 0.77 confirmed (Table 1); LitEval pointwise Kendall 0.17 to 0.38 confirmed (Table 3); Italian absent confirmed (languages: en, de, fr, es, ca, ru, zh, bn, ja, th, te, sw); GlobalNLP / RANLP 2025 venue not found | The venue claim is neither stated nor contradicted by arXiv; it needs a non-arXiv source before entering the knowledge base. |

## Verifier C (format, RAG, code, multilingual, multimodal sources)

| ID | Title matches | Latest version, date | Venue stated | Numbers | Note |
|---|---|---|---|---|---|
| 2607.22969 | yes | v1, 2026-07-25 | none (comments: 12 pp, code link) | confirmed (Table II; Table V p=0.1249 for GPT-4o-mini 8 vs 0 shot, marked not significant) | Full title continues "A Systematic Empirical Study of Shot-Count Effects..." |
| 2605.29420 | yes | v1, 2026-05-28 | none ("Submitted for peer review") | confirmed (Table II, all five figures; GPT-4o mini stated as answering model) | Baseline vs "General expert" row |
| 2608.21074 | yes | v1, 2026-08-21 | none | confirmed (Section 4.1; 5x164x10=8200) | Baseline is called "vanilla" in the paper |
| 2508.11383 | yes | v1, 2025-08-15 | none | confirmed (Table 4, incl. ensemble rows 0.028 and 0.018) | DeepSeek printed as "DeepSeek V3 0324" |
| 2608.22228 | yes | v1, 2026-08-23 | "Committed to AACL-IJCNLP 2026" (a commitment, not a stated acceptance) | confirmed (both figures in abstract) | Three small frozen models, 3.8B to 8B |
| 2607.05139 | yes | v1, 2026-07-06 | none | confirmed (abstract 14% vs 25%; Fig. 4 text gives all five deltas) | DeepSeek is "DeepSeek-V4-Flash" in the paper |
| 2602.20408 | yes | v1, 2026-02-23 | none | partially: all numbers confirmed (39.15, 50.40, 56.97; 2.04 to 2.36; gpt-4o-2024-11-20). Fixation is measured as exploration-rate slopes over ten sequential ideas within one persona session, not a persona reused across sessions | Rephrase the fixation claim as within-session |
| 2607.14816 | yes | v1, 2026-07-16 | none | confirmed (Table 3; ClassEval 37.00 EN vs 33.00 IT) | Models: GPT-4o mini, DeepSeek, Claude; 460 tasks |
| 2506.05614 | yes | v1, 2025-06-05 | none | confirmed (Table IV; Observation 1 "No single prompt technique consistently outperforms others") | Assert-generation best technique is also ES-KNN |
| 2608.24641 | yes | v1, 2026-08-25 | "Accepted at ICSME 2026" | confirmed on aggregate: Table VI few-shot deltas Qwen2 -4.2/-4.2/-8.2, Qwen2.5 +7.2/+1.4/-1.3 (one Qwen2.5 run still negative) | Say "reverses on average" rather than unconditionally |
| Zhang & Wu, CMC 89(1) | yes | issue published 2026-08-13 | Computers, Materials & Continua 89(1) | confirmed (P1 to P3: GPT-5.5 0% to 47.9%, Gemini 5.2% to 55.2%, Claude 7.2% to 11.2%; over-answer above 65%, Claude 90.5%) | Model printed as "Gemini 2.5 Flash"; 91 is a rounding of 90.5 |
| Wardle & Susnjak, BDCC 9(6):149 | yes | published 2025-06-03 (received 2025-03-27) | Big Data and Cognitive Computing 9(6), 149, DOI 10.3390/bdcc9060149 | confirmed (Table 5, columns TF/IF/IN: GPT-4o chem 0.32/0.67/0.72, econ 0.73/0.58/0.48; Gemini-1.5 chem 0.25/0.43/0.43; Claude-3 physics 0.48/0.18/0.26) | MDPI returns 403 to WebFetch; verified via headed Chrome. arXiv 2410.03062 v1 is an earlier draft with different tables, so cite the journal only |

Not verified by any agent (cited in the report but not behind a rule that entered the knowledge base, or cited only as background): Liu et al. taxonomy (Frontiers of Computer Science 2026), arXiv 2507.05424 (Lost-in-the-Later, cited in the role's retrieval bullet as a phenomenon), arXiv 2504.14716 and 2405.09798 and 2406.06608 (pre-window background).
