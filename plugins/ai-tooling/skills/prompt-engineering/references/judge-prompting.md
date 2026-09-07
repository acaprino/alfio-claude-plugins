# Judge and evaluator prompts

On-demand reference for the `prompt-engineer` agent and the `/prompt-optimize` command. Read it
when the archetype is judge / evaluator: an LLM-as-judge, a rubric verifier, a grader that scores
or ranks candidate outputs, a monitor that checks an agent's transcript. It answers one question:
what shape of judge prompt measured the highest agreement with humans on which model class, and
which popular additions measured as harmful. The safeguards around the judge (a different model
family from the system under test, randomized pairwise order, an Unknown clause, kappa against
human labels rather than exact match, the candidate output treated as untrusted input) live in
the `<prompt_evals>` section of the `prompt-engineer` role and are assumed here.

Every number below is **measured** on the named model and benchmark at the cited date, and
**predicted** on yours until you run the agreement check at the end. Numbers checked 2026-09-07.

## Three facts that frame every judge prompt

**A strong judge wants a simple criterion prompt, and strictness does not help it.** RuVerBench
(arXiv 2606.29920 v2, EMNLP 2026) verifies one rubric criterion at a time against long
deep-research and coding outputs. With its default prompt, a yes/no judgment on one criterion
with the evidence cited, GPT-5.4 reaches about 91.4% balanced accuracy on deep-research rubrics and 89.4% on
coding rubrics; rewriting the instructions as "strict" did not reliably help strong judges and
sometimes reduced their performance. The same strict variant improved a weaker open judge,
Qwen3.5-27B, by about 11.8 points on agentic coding. Strictness is a capacity-conditional
fallback, never the base template.

**The scale is a measured choice, and the pooled default reverses on some benchmarks.** Across
judges and datasets (arXiv 2601.03444 v1, no venue stated), human-to-judge agreement (ICC) was
0.853 on a 0-5 scale, 0.805 on 0-10 and 0.840 on 0-100; on MT-Bench the order flipped (0.517,
0.570, 0.470). Per judge: GPT-4o 0.816 / 0.760 / 0.810, Gemini 2.5 Flash 0.782 / 0.749 / 0.784, Qwen3-32B 0.731 / 0.684 / 0.714,
DeepSeek-V3.2 0.696 / 0.670 / 0.624. Start at 0-5 when a scalar is genuinely needed, then
calibrate on your own labels.

**Small judges are lifted by references and checklists and damaged by debate and personas.** A
reference answer written by a frontier model (GPT-4o) raised judge accuracy on non-verifiable
tasks, averaged over five benchmarks, for Llama-3.1-8B from 71.8% to 79.4%, Mistral-7B-v0.3 from
61.2% to 69.6% and Gemma-2-9B from 80.8% to 85.7%, with one counterexample, Qwen2.5-14B, 83.3% to
82.4% (arXiv 2602.16802, ICLR 2026; human-written references were tested on one adversarial set
only). A generated criterion checklist took Qwen2.5-7B-Instruct from 0.64 to 0.77 pairwise
accuracy on MM-Eval reasoning and from 0.17 to 0.38 Kendall on LitEval (arXiv 2507.06774 v2;
workshop venue *(verify)*; twelve languages, Italian not among them). SLMJury (arXiv 2606.07810
v1) measured sixteen judges from 0.6B to 14B: its best closed-ended judge, Phi-4 14B, reached
89.55%; no reflect-critique-refine debate beat its own strongest member, the best three-judge
jury gained 0.06 points over the best single judge, and persona wrappers cost the weaker judges
up to 10.2 (Llama-3.1-8B, lenient persona) and 11.9 points (Phi-4-mini, strict persona) while
moving the top judges by at most 0.55.

## The default judge prompt

Build the judge from these parts, in this order, and remove a part only when its row in the
lever table says it is unmeasured or harmful on the target class:

1. **One criterion per judge.** A judge that scores twelve things at once is twelve judges
   with shared bias. Decompose; run one criterion per call, or one call per criterion group
   that a human would also grade together.
2. **A binary decision with evidence.** "Satisfied / not satisfied, then quote the span that
   decides it." Reserve scalar scores for criteria that are genuinely graded, and use 0-5 there.
3. **The reference, when a trustworthy one exists.** A gold answer, a reference solution, a
   human-written exemplar. On small judges this is the single largest lever measured; on a
   strong judge it costs little and constrains drift.
4. **A checklist step for open-ended criteria.** Before scoring, list the concrete sub-points
   the criterion implies for this input, then check each. This is the multilingual-judge result,
   and it is what makes "is the reasoning sound" gradable at all.
5. **The escape hatch and the data boundary.** An explicit Unknown option, and the candidate
   output delimited and declared non-instructional (from the role's safeguards).

Do not add: a judge persona ("you are a world-class senior reviewer"), a debate among judges, a
1-10 or 1-100 scale by default, or an instruction to be strict. Each of those has a measured
zero or negative effect on at least one class below.

## By model class

| Class | Base template | What measured | What not to add |
|---|---|---|---|
| **Frontier reasoning model** (GPT-5.4, Claude 4.6 and later, Gemini 3) | Binary criterion verification with evidence | GPT-5.4 about 91.4% (research rubrics) and 89.4% (coding rubrics) balanced accuracy on RuVerBench; strict rewrites did not reliably help | Strictness, persona; scale results on this class come from GPT-4o and Gemini 2.5, not measured on 5-series judges |
| **Hybrid open reasoner** (Qwen3, Qwen3.5, DeepSeek-V3.x) | Binary criterion verification; 0-5 where scalar | Qwen3-32B and DeepSeek-V3.2 agree best at 0-5 (0.731, 0.696 ICC); Qwen3.5-27B gained 11.8 points of balanced accuracy from a strict prompt on agentic coding; Qwen3.5 judges show score-option position bias, and permuting the option order and aggregating raised Pearson correlation by 0.076 on HANNA, with about two thirds of the gain by three permutations and 85% by five (arXiv 2602.02219 v2) | Persona; a single fixed option order when the judge is position-sensitive |
| **Small open-weight instruct model** (Llama-3.1-8B, Mistral-7B, Gemma-2-9B, Qwen2.5-7B, Phi-4 14B) | Reference-guided binary verification with a generated checklist | Reference +4.9 to +8.4 points on three of four models; checklist +0.13 pairwise accuracy and +0.21 Kendall at 7B; Phi-4 14B 89.55% closed-ended; Gemma-3-12B +0.035 Pearson on SummEval from option permutation | Debate (never beat its strongest member), personas (up to 11.9 points off a weaker judge), three-judge juries (+0.06 at best), 0-10 scales |
| **Older non-reasoning model** (GPT-4o, Gemini 2.5 Flash) | Binary verification; 0-5 where scalar | GPT-4o 0.816 and Gemini 2.5 Flash 0.782 ICC at 0-5, both lower at 0-10 | 0-10 by default; MT-Bench is the known reversal, so check the benchmark before trusting the pooled default |

## Prompt-side levers, and what each is worth

| Lever | Worth | Evidence |
|---|---|---|
| One criterion per judge, binary with evidence | The base; strong judges plateau near 90% balanced accuracy with nothing else | arXiv 2606.29920 |
| Reference answer in the prompt | +4.9 to +8.4 points on small judges with a frontier-written reference; one small decrease (Qwen2.5-14B) | arXiv 2602.16802 |
| Generated checklist before scoring | +0.13 pairwise accuracy, +0.21 Kendall at 7B, multilingual | arXiv 2507.06774 |
| 0-5 scale instead of 0-10 or 0-100 | +0.048 pooled ICC over 0-10; reverses on MT-Bench | arXiv 2601.03444 |
| Permuting score-option order, aggregating 3-5 judgments | +0.076 Pearson (Qwen3.5-27B, HANNA), +0.035 (Gemma-3-12B, SummEval); pays mainly on judges with a strong position bias | arXiv 2602.02219 |
| "Be strict" instruction | Helps a weaker open judge (+11.8, Qwen3.5-27B); moves GPT-5.4 and Gemini 3.1 Pro by -0.3 to +1.0 | arXiv 2606.29920 |
| Judge persona | At most 0.55 points on the top small judges, up to 11.9 points off the weaker ones | arXiv 2606.07810 |
| Multi-judge debate | No debate beat its own strongest member | arXiv 2606.07810 |
| Three-judge jury vote | +0.06 over the best single judge, at three times the cost | arXiv 2606.07810 |
| Asking the judge for a confidence or probability | No in-window measurement of improved human agreement or calibration found; unmeasured | searched 2026-09, not found |
| Pairwise instead of pointwise | Not established as generally superior; pre-window evidence (arXiv 2504.14716) found adversarial distractors flipping about 35% of pairwise preferences against about 9% of absolute scores | background only |

## The agreement check a judge prompt needs

Before a judge grades anything that matters: 50 to 100 items labelled by two humans, Cohen's
kappa between the judge and the humans (never raw exact match, which overstated agreement by 33
to 41 points in the role's cited study), one kappa per criterion, and a position-bias probe
(swap the candidate order, or permute the score options, and count the flips). A judge whose
kappa you have not measured on your task is a predicted judge, and the numbers above say it can
be off by a whole scale choice.

## Sources

- "Can LLM-as-a-Judge Reliably Verify Rubrics in Agentic Scenarios?" (RuVerBench), arXiv 2606.29920 v2, EMNLP 2026
- "Grading Scale Impact on LLM-as-a-Judge", arXiv 2601.03444 v1, 2026-01, no venue stated
- "Am I More Pointwise or Pairwise? Revealing Position Bias in Rubric-Based LLM-as-a-Judge", arXiv 2602.02219 v2, 2026-06, no venue stated
- "SLMJury: Can Small Language Models Judge as Well as Large Ones?", arXiv 2606.07810 v1, 2026-06, no venue stated
- "References Improve LLM Alignment in Non-Verifiable Domains", arXiv 2602.16802 v1, ICLR 2026
- "Checklist Engineering Empowers Multilingual LLM Judges", arXiv 2507.06774 v2, 2025-07; the workshop venue was not stated on arXiv at this refresh *(verify)*
- "Pairwise or Pointwise? Evaluating Feedback Protocols for Bias in LLM-Based Evaluation", arXiv 2504.14716, pre-window background
- Not read, worth the next refresh: judge prompts on Claude 5 and GPT-6 class models (every scale result above is on GPT-4o and Gemini 2.5), confidence elicitation studies, an Italian-language judge measurement
