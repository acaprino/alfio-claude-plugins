# Prompting for extraction tasks

On-demand reference for the `prompt-engineer` agent and the `/prompt-optimize` command. Read it
when the archetype is extraction or classification: named-entity recognition (NER), relation
extraction (RE), event extraction (EE), key-value or schema-guided extraction from documents,
table extraction, text-to-structure. It says which prompt shapes measurably work per task, which
fail, and what changes on small open-weight models. Output-shape enforcement (JSON, schemas,
constrained decoding) is a separate concern with its own reference, `structured-output.md`; read
both when the extraction output is machine-parsed, which it almost always is.

Every number below is **measured**, on the named model and dataset, at the cited date. None of it
is measured on your model, your schema or your documents: applied to those it is a prediction
until you run the eval at the end of this file. Numbers checked 2026-09-05.

## Two facts that frame every extraction prompt

**Prompting lags fine-tuning on extraction at every model size, and the gap is large.** The
generative-IE survey (Xu et al., arXiv 2312.17617 v3, 2024-10) puts in-context learning far behind
supervised fine-tuning: NER on CoNLL03 90.91 F1 (GPT-NER, ICL) vs 96.77 (YAYI-UIE, SFT); RE on NYT
strict 32.17 (CodeIE, ICL) vs 91.96 (REBEL); EE on ACE05 trigger classification 37.4 (Code4UIE,
ICL) vs 77.13 (InstructUIE). After fine-tuning, backbones that differ by hundreds of times in
parameters land within a few points of each other. The 2026 zero-shot RE study (arXiv 2606.22606,
2026-06) makes the same point at the frontier: with a schema-enumerated system prompt and no
demonstrations, GPT-5.4 scores 0.693 and Claude Sonnet 4.6 0.662 positive-class micro-F1 over
seven RE benchmarks, while a fine-tuned Qwen2.5-0.5B reaches 0.828 and Llama-3.2-3B 0.844. The
consequence for an optimizer: for a fixed schema at volume, the best prompt is the baseline and a
fine-tuned small model is the ceiling. Say so when the caller's task is fixed and the volume is
high; do not sell a prompt as the end state.

**Output validity is the first failure on small models, before accuracy.** CodeNER (arXiv
2507.20423, 2025-07) measures Phi-3-mini-128k at 2.72 F1 with a plain-text NER prompt, a
near-total failure to produce usable BIO output, and Llama-3-8B at 26.00; Gemini 2.5 Pro was
dropped from the 2026 RE study for poor output validity. Under fine-tuning, output format alone
moves F1 by over 40% on BC5CDR ("Lost in Formatting", EACL 2026, on Qwen2.5 3B to 32B, Phi-3.5,
Mistral, Llama 3.1 8B, OLMo-2). Treat the output format as a hyperparameter to measure, not a
detail to tidy.

## Per-task recommendations

| Task | Prompt shape that measured best | Evidence | Caveat on small open-weight models |
|---|---|---|---|
| Flat NER | Enumerate the label set; require verbatim spans in order of appearance; retrieved (kNN) demonstrations; a self-verification pass against NULL and over-extraction; soft span matching in the eval | survey; empirical study (arXiv 2409.00369); GPT-RE; LangExtract | Plain-text prompts collapse on Phi-3-class models; a code or BIO-structured prompt lifts Phi-3-mini +19.5 F1 and Llama-3-8B +5.8 (CodeNER); disagreement-refined instructions add +14.9 F1 at 8B to 24B (DiZiNER); a fine-tuned 7B still wins (UniNER 87.5 on ACE04) |
| Nested and long-tail NER | Per-type definitions carrying negative examples, boundary rules and disambiguation rules; expect tail types at 15% to 70% of head-type F1 | empirical study; DiZiNER; guidelines-as-docstrings | Verbose definitions pasted into an already long prompt hurt GPT-4 in half the cases; only contrastive rules helped |
| Relation extraction | Schema-enumerated labels with an explicit no-relation option; two-stage on hard sets (which types are present, then the triples); task-aware kNN demonstrations with gold-label-induced reasoning; fix subject and object order explicitly | zero-shot RE study; empirical study; GPT-RE | Frontier zero-shot is a floor (0.66 to 0.69); fine-tuned 0.5B to 3B beats it; zero-shot small models on RE were not measured, expect worse |
| Event extraction | One Python class per event type with guideline docstrings that carry positive and negative examples; detect-then-extract in two stages; an "extract all required information" reminder; an empty list for no event | guidelines-as-docstrings (arXiv 2502.16377, Findings of ACL 2025); empirical study | Guideline gains survive at 1B only under instruction tuning; zero-shot joint EE is 2% to 26% of SOTA even for GPT-4 |
| Long documents, key-value | Chunk at about 1,000 characters, several passes in parallel, verbatim spans with character offsets, drop ungrounded extractions; a JSON Schema with field descriptions and explicit nullable fields; whole-record processing rather than page-by-page for lists; a verification loop on dense forms | LangExtract; ExtractBench (arXiv 2607.29677, 2026-08, vendor-authored) | LangExtract runs gemma2:2b through Ollama JSON mode but publishes no accuracy for it; ExtractBench scored Qwen3.6 35B and Gemma4 26B *(verify: scores not read)* |
| Tables | A multimodal model for cell content, a layout tool for structure; split or bypass the LLM on tables over 1,000 rows | ACL 2025 XLLM table benchmark; ExtractBench | Every VLM tested fell below 10% on tables over 1,000 rows |
| Classification with a fixed label set | An enum: a tool with an enum field, or a structured-output schema, rather than free text (see `structured-output.md`) | vendor migration guidance | On small models, constrained decoding is the enforcement that holds |

## Shapes that measurably work

- **Two-stage prompting.** Ask which types are present, then extract. On GPT-4 (arXiv 2409.00369,
  2024-08, 14 subtasks, 16 datasets): +16.82 F1 on joint EE, +2.05 on RE triplets, but -5.05 on
  flat NER. Use it where the schema is wide and the text dense; skip it for flat NER.
- **An "extract all required information" reminder.** +15.18 F1 on joint EE in the same study,
  under 2 points elsewhere. Missing spans are the dominant error, so the reminder pays where recall
  is the problem.
- **Retrieved demonstrations with label-induced reasoning.** GPT-RE (EMNLP 2023): task-aware kNN
  retrieval of demonstrations, each carrying a short gold-label-induced rationale, reaches state of
  the art on SemEval and SciERC and cuts the tendency to classify NULL examples into a real label.
  Five demonstrations add 3.0 to 13.0 F1 over zero-shot on GPT-4 across the empirical study's
  subtasks. Random demonstrations do not buy this; retrieval does.
- **Code-shaped prompts for zero-shot NER.** CodeNER embeds the BIO schema as Python: on average
  over ten datasets in five languages GPT-4 rises from 50.00 to 52.41 macro-F1 and GPT-4 Turbo from
  48.10 to 51.17, with the largest gain on FIN (+18.3); it loses on CoNLL03 (-3.76), MIT Movie
  (-3.83), WNUT-17 (-5.04) and DaNE (-9.18). It is a small-model technique first: Phi-3-mini
  2.72 to 22.26, Llama-3-8B 26.00 to 31.81, Llama-3-70B 36.72 to 39.17. Removing entity-label
  descriptions from the code prompt did not hurt on average.
- **Guidelines as class docstrings, with contrast.** Annotation guidelines written into event
  class docstrings give about +10 trigger-classification and +5 argument-classification points on
  ACE05 in full data for an instruction-tuned Llama-3.1-8B, and up to +30 and +20 in the
  2,000-sample regime; machine-generated guidelines carrying positive **and negative** examples beat
  human-written ones by up to 11 and 7 points because the human ones "lack explicit contrasts". The
  contrast is the active ingredient; the same study finds no gain once negative sampling is already
  in use, and more parsing errors from guidelines without it.
- **Refined instructions instead of more examples on small models.** DiZiNER (arXiv 2604.15866,
  2026-04) refines NER instructions from where eight 8B-to-24B open models disagree (Mistral Small
  3.2, Phi 4, Qwen 3 14B, Gemma 3 12B, DeepSeek-R1 8B, Llama 3.1 8B, Nemotron Nano, gpt-oss-20B):
  +14.9 F1 on average over 18 datasets with no parameter update, CoNLL03 81.3 to 86.9, OntoNotes
  32.2 to 62.5. What the refined instructions contain is the prescription: about a fifth
  span-boundary rules, a fifth entityhood rules, a fifth type-disambiguation rules. Write those
  three kinds of rule before adding a sixth example.
- **A self-verification pass.** GPT-NER's verifier asks, for each extracted entity, whether it is
  one; it targets the NULL-labelled-as-entity error that dominates over-extraction. Cheap and
  effective on strong models; on a small model, run it as a separate call with its own enforcement.
- **Source grounding.** LangExtract returns a character interval into the source for every
  extraction, chunks long documents at `max_char_buffer=1000` ("smaller contexts improve
  accuracy"), runs `extraction_passes=3` for recall, and instructs that few-shot `extraction_text`
  be verbatim and listed in order of appearance. An extraction copied from the few-shot examples
  rather than the input comes back with no interval and is filtered. That is the only measured
  defense against demonstration leakage found; prompting does not catch it.

## What fails, with numbers

- **Verbose label definitions in a long prompt.** Adding label names and task definitions lowered
  GPT-4's scores in half the cases of the empirical study (joint EE 17.07 without vs 3.70 with).
  Definitions help when they are contrastive rules (above); paraphrase does not.
- **Chain-of-thought on extraction.** Few-shot CoT "cannot guarantee further gains" and is often
  worse on GPT-3.5 and GPT-4 across IE subtasks. CodeNER reports the opposite on its code prompt;
  the broader evidence is against. Extraction is not a reasoning task; do not add a scaffold to it.
- **Standoff formats on long, dense text.** Under fine-tuning, standoff JSON and tuple formats lose
  to inline, token-level formats on ACE2005, OntoNotes and BC5CDR because they omit spans when the
  text is long and dense (BC5CDR samples about 6x longer, about 19 spans each); "no single format
  consistently dominates". Example on Qwen2.5-3B: free text 62.68, standoff JSON 66.73, inline
  linear 72.07, column 72.12 F1.
- **Long documents drop whole records; page-by-page chunking loses them too.** ExtractBench: Gemini
  3.5 Flash goes from 87.9% F1 on short documents to 27.9% on long ones; dense scanned forms cause
  over-extraction; verification loops reduce it.
- **Span qualifiers.** GPT models add qualifiers to spans ("The University of Michigan"), so strict
  matching under-counts them: soft matching adds +6.30 F1 on aspect extraction and up to +16.5
  elsewhere. Decide the matching rule before the eval, not after.
- **Long-tail types.** 55.12 vs 83.94 F1 on CoNLL03, 2.30 vs 14.50 on NYT RE. A prompt cannot fix a
  type the model has barely seen; say so, and route those types to a fine-tuned model or a rule.
- **Malformed output.** Rare for GPT-4 except joint EE at 11.97%; the norm rather than the
  exception on small models (see the first section). Enforce the shape; see `structured-output.md`.

## Error taxonomy to diagnose against

From the empirical study's seven error types: missing spans and unannotated spans (false positives
absent from gold) together exceed 60% of errors on most tasks (RE triplets 53.07% missing, 33.94%
unannotated; EE triggers 46.74% and 38.70%). Flat NER is type-dominated instead: missing types
28.03%, incorrect types 24.69%. Diagnose an extraction prompt by counting these buckets on twenty
documents before rewriting anything; the bucket names the fix (recall reminder and two-stage for
missing spans; a no-relation option and self-verification for unannotated spans; contrastive type
rules for type errors).

## Small open-weight models, in order of what to try

1. Zero-shot with a code- or BIO-shaped prompt for NER, or a schema-enumerated prompt with an
   explicit none option for RE and classification. Measure output validity first.
2. Contrastive instructions: span-boundary rules, entityhood rules, type-disambiguation rules,
   negative examples. This is where DiZiNER's +14.9 F1 came from at 8B to 24B.
3. Enforce the output shape outside the prompt (validate-and-repair, then constrained decoding;
   `structured-output.md`). On these models the instruction is not the enforcement.
4. Retrieved demonstrations, verbatim and in order of appearance, with grounding to catch leakage.
5. If the schema is fixed and the volume justifies it, fine-tune: a 0.5B to 3B model beats frontier
   zero-shot on RE, and a 7B NER model beats GPT-4 in-context learning.

## The eval an extraction prompt needs

- Per-field precision and recall with nulls counted: an omitted key scores as an explicit null
  (ExtractBench's rule), so a prompt cannot improve its score by staying silent.
- Parse failures scored separately from wrong answers. The format-sensitivity literature finds most
  "sensitivity" is answer extraction failing, which is a different fix from a wrong extraction.
- The span-matching rule (strict or soft) declared before the run.
- Held out by document, never by span, so a demonstration cannot leak into its own test.
- Grounding checks: every extracted span must exist verbatim in the source, or the eval counts it
  as hallucinated.

## Sources

- Xu et al., "Large Language Models for Generative Information Extraction: A Survey", arXiv 2312.17617 v3, 2024-10-31
- Han et al., "An Empirical Study on Information Extraction using Large Language Models", arXiv 2409.00369, 2024-08, Neural Networks
- Wan et al., "GPT-RE: In-context Learning for Relation Extraction using Large Language Models", EMNLP 2023
- "CodeNER: Code Prompting for Named Entity Recognition", arXiv 2507.20423 v4, 2025-07
- "Instruction-Tuning LLMs for Event Extraction with Annotation Guidelines", arXiv 2502.16377 v2, Findings of ACL 2025
- "Lost in Formatting: How Output Formats Skew LLM Performance on Information Extraction", EACL 2026 (aclanthology 2026.eacl-long.256)
- "Sub-Billion, Super-Frontier: SLMs Rival Zero-Shot Frontier LLMs on Relation Extraction", arXiv 2606.22606, 2026-06-21
- "DiZiNER: Disagreement-guided Instruction Refinement for Zero-shot NER", arXiv 2604.15866, 2026-04-17
- ExtractBench, arXiv 2607.29677 v2, 2026-08-05 (LlamaIndex, vendor-authored)
- "Benchmarking Table Extraction: Multimodal LLMs vs Traditional OCR", ACL 2025 XLLM workshop
- google/langextract README (github.com/google/langextract)
- Not read, worth the next refresh: GoLLIE (arXiv 2310.03668), KnowCoder (2403.07969), UniversalNER (2308.03279), GPT-NER (2304.10428), "Event Extraction in Large Language Model" survey (2512.19537), LMDX (2309.10952), ReverseNER (2411.00533)
