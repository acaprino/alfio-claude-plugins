# Advanced RAG Patterns

Beyond hybrid+rerank: when to escalate to GraphRAG, agentic retrieval, hippocampus-style memory, or long-context-LLM patterns. Each row in the selection guide below tells you when the complexity is worth it.

## When to use

You've shipped a hybrid + rerank baseline (`retrieval-patterns.md`) and need more -- multi-hop reasoning, cross-document themes, evolving corpora, or unreliable retrieval. For evaluation that decides which of these to pick, see "Evaluation frameworks" below.

## Pattern selection guide (the table to start with)

| Pattern | Complexity | Best for | When to use |
|---------|-----------|----------|-------------|
| Naive RAG | Low | Simple Q&A, clean docs | Start here |
| **Hybrid + Reranking** | Medium | Most production cases | **Default modern baseline** |
| Contextual Retrieval | Medium | Ambiguous chunks | 49-67% fewer retrieval failures |
| Agentic RAG | High | Complex multi-hop queries | Simple retrieval insufficient; diverse query types |
| LongRAG | Low-Medium | Long-context LLM available | Let the LLM read fewer, longer chunks |
| HippoRAG / HippoRAG 2 | High | Multi-hop + continual learning | KG + Personalized PageRank over evolving corpora |
| LightRAG | Med-High | Evolving corpora | Cheaper graph RAG than Microsoft GraphRAG |
| Graph RAG (incl. LazyGraphRAG) | High | Cross-document themes | Global queries; **benchmark vs hybrid+rerank first** |
| RAPTOR | High | Long documents | Answers span multiple doc sections |
| CRAG | Medium | Unreliable corpus | Retrieved docs often irrelevant |
| Self-RAG | High | Variable query types | Some queries don't need retrieval |

## Critical caveat: GraphRAG often loses to a tuned hybrid pipeline

2025 benchmarks ([arxiv:2502.11371](https://arxiv.org/html/2502.11371v2), [arxiv:2506.05690](https://arxiv.org/html/2506.05690v3)) show GraphRAG variants frequently **underperform** a well-tuned hybrid + reranking pipeline on real-world tasks. Default to hybrid + rerank first; escalate to GraphRAG only for cross-document theme questions.

If you need GraphRAG, **start with LazyGraphRAG** (Microsoft, 2024) -- same concept but indexing is deferred per-query, cutting upfront cost by orders of magnitude. Only use full GraphRAG if you run many queries over the same corpus.

## Pattern crib notes (when each one is the right escalation)

- **Agentic RAG** -- LLM agent decides per-query whether/where/how to retrieve. Frameworks: LangGraph, LlamaIndex `AgentRunner`, CrewAI. Survey: https://github.com/asinghcsu/AgenticRAG-Survey.
- **HippoRAG 2** (ICML 2025) -- KG + Personalized PageRank from query entities; 7% lift on associative-memory benchmarks vs SOTA embeddings; supports continual learning. Use for multi-hop Q&A on evolving corpora.
- **LightRAG** (HKU/BUPT 2024) -- dual-level retrieval (entity + concept) + graph-enhanced indexing with **incremental updates without reprocessing**. Cheaper than full GraphRAG.
- **LongRAG** -- pair "long retriever" with "long reader." Group docs into ~4K-tok units, retrieve fewer/longer, let a 1M+ context LLM (Claude, Gemini 2M, GPT-4o-long) do the reading. 62.7% EM on NQ, 64.3% on HotpotQA without retriever fine-tuning. Cost scales with long-context LLM usage.
- **RAPTOR** -- recursive summary tree from leaf chunks → root. At query time, traverse top-down. Good when answers span many doc sections.
- **Corrective RAG (CRAG)** -- evaluator grades each retrieved doc as Correct/Ambiguous/Incorrect, falls back to web search on Incorrect.
- **Self-RAG** -- model emits special tokens (`[Retrieve]`, `[IsRel]`, `[IsSup]`, `[IsUse]`) to decide retrieval and self-critique factuality.
- **Modular RAG** -- formalize Router / Retriever / Evaluator / Generator / Refiner as swappable modules.

## Multi-modal RAG

- **Tables**: extract as HTML (preserves structure best); embed text + LLM-generated summary.
- **Images**: multimodal embeddings (CLIP, SigLIP) for matching; vision LLMs to generate text descriptions; **ColPali / ColQwen** for late-interaction on document page images (no OCR needed).
- **PDFs**: Unstructured.io for element-level; LlamaParse for LlamaIndex; consider page-level vision indexing for complex layouts.

## Evaluation frameworks (the 2026 stack)

| Framework | Role | Best for |
|-----------|------|----------|
| **RAGAS** | Reference-free metrics (Context Precision/Recall, Faithfulness, Answer Relevance) | Metric exploration during system design |
| **DeepEval** | Pytest-style assertions | CI/CD quality gates |
| **TruLens** | Live production monitoring | Production observability dashboards |
| **Langfuse** | Traces + evals combined | End-to-end LLM observability |
| ARES | Academic benchmarking | Comparative research (less adopted in 2025-2026 production) |

Recommended pipeline: **RAGAS during design → DeepEval gates in CI → TruLens or Langfuse in prod.**

## Legacy patterns (you'll see these in older codebases)

FiD (Fusion-in-Decoder), RA-DIT, REPLUG -- still referenced academically but rarely appear in 2025-2026 production stacks. Modern agentic + hybrid-rerank + long-context-LLM pipelines subsume their capabilities. Document them if you encounter legacy systems; prefer the patterns above for new work.

## Official docs / papers

- Microsoft GraphRAG: https://github.com/microsoft/graphrag (docs: https://microsoft.github.io/graphrag/, paper: https://arxiv.org/html/2404.16130v1)
- HippoRAG v1 paper: https://arxiv.org/abs/2405.14831 | v2 paper: https://arxiv.org/html/2502.14802v1 | code: https://github.com/OSU-NLP-Group/HippoRAG
- LightRAG paper: https://arxiv.org/abs/2410.05779 | code: https://github.com/LarFii/LightRAG-hku
- LongRAG paper: https://arxiv.org/abs/2406.15319
- RAPTOR code: https://github.com/parthsarthi03/raptor
- CRAG paper: https://arxiv.org/abs/2401.15884
- Self-RAG paper: https://arxiv.org/abs/2310.11511
- HybridRAG benchmark (2025): https://arxiv.org/html/2502.11371v2
- Contextual AI on GraphRAG alternatives: https://contextual.ai/blog/an-agentic-alternative-to-graphrag
- RAGAS paper: https://arxiv.org/abs/2309.15217
- DeepEval RAG metrics: https://deepeval.com/docs/metrics-ragas
- Agentic RAG survey: https://github.com/asinghcsu/AgenticRAG-Survey

## Related

- `retrieval-patterns.md` -- the hybrid+rerank baseline these escalate from
- `production-guide.md` -- observability, evals, security, framework overhead
- `chunking-strategies.md` -- per-pattern chunking implications (RAPTOR, parent-child)
