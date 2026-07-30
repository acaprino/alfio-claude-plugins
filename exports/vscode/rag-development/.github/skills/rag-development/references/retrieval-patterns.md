# Retrieval Strategies & Patterns

How to retrieve the right chunks for a query. Hybrid search + reranking is the modern baseline; everything else is a specialization.

## When to use

Designing the retrieval stage of a RAG pipeline. For chunking decisions feeding this stage, see `chunking-strategies.md`. For end-to-end agentic patterns, see `advanced-rag-patterns.md`.

## The default modern recipe (memorize this)

1. **Hybrid search**: dense (vector) + sparse (BM25/SPLADE), fused with **Reciprocal Rank Fusion at k=60**.
2. **Rerank top-50-100** to top-5-10 with a modern cross-encoder reranker (Voyage / Cohere / Jina / mxbai).
3. **Pass top-5 to the LLM** for generation.

**Latency target**: < 200ms total for retrieve + rerank + top-k fetch. If you blow this, audit dense-search `top_k`, reranker batch size, and whether you're calling a remote reranker for tiny corpora.

RRF formula -- the only equation worth memorizing:
```
RRF_score(d) = sum(1 / (k + rank_i(d)))   for each retrieval method i,  k=60
```

## Reranker matrix (2025-2026)

| Reranker | Released | Context | Pricing | Notes |
|----------|----------|---------|---------|-------|
| Jina Reranker v3 | 2025 | 131,072 tok (query + all docs) | See vendor | 0.6B listwise; 61.94 nDCG@10 BEIR; highest evaluated quality |
| Jina Reranker v2 (base-multilingual) | 2024-06 | 1024 (auto-chunked) | $0.02 / 1M in + $0.02 / 1M out | 100+ languages, code search |
| Voyage rerank-2.5 | 2025-08 | 32,000 tok | $0.05 / 1M | Instruction-following; 8x Cohere v3.5 context |
| Voyage rerank-2.5-lite | 2025-08 | 32,000 tok | $0.02 / 1M | Cheapest high-context commercial reranker |
| Cohere Rerank 3.5 (rerank-v3.5) | 2024-12 | ~4K tok | See vendor | 100+ languages; strong reasoning |
| BAAI bge-reranker-v2-m3 | 2024-03 | ~8K | Open (self-host) | Multilingual baseline, slim |
| BAAI bge-reranker-v2-gemma | 2024-03 | [UNVERIFIED] | Open | Higher-quality open-source (Gemma-2B base) |
| BAAI bge-reranker-v2.5-gemma2-lightweight | 2024 | [UNVERIFIED] | Open | Latest BAAI; claims SOTA BEIR + MIRACL |
| Mixedbread mxbai-rerank-large-v2 | 2025 | 8K | Apache 2.0 | 57.49 nDCG@10 BEIR; 1.5B Qwen-2.5 base, GRPO trained |
| Mixedbread mxbai-rerank-base-v2 | 2025 | 8K | Apache 2.0 | 55.57 nDCG@10 BEIR at 0.5B; excellent speed/quality |
| cross-encoder ms-marco-MiniLM-L-12-v2 | 2021 | 512 | Open | Legacy; outclassed -- use only when resource-starved |

## Selection guide

- **Commercial, long docs, multilingual** → Voyage rerank-2.5 or Cohere Rerank 3.5 (Voyage wins on context + price).
- **Self-hosted production** → mxbai-rerank-base-v2 (small/fast) or mxbai-rerank-large-v2 (higher quality).
- **Highest retrieval quality** → Jina Reranker v3 (listwise, 131K context).
- **Open-source multilingual baseline** → bge-reranker-v2-m3 or bge-reranker-v2.5-gemma2-lightweight.
- **Legacy** → keep MS MARCO cross-encoders only for existing pipelines that haven't been retrained.

## Gotchas

- **HyDE is best when query phrasing diverges from the document.** Embed an LLM-generated hypothetical answer instead of the bare query. Useless when query already looks like the answer.
- **Multi-query / decomposition trades latency for recall.** Each variant = N more retrieval calls. Use only when single retrieval misses too much.
- **Step-back prompting** = ask the broader question first ("principles of adiabatic processes"), then the specific. Mostly useful for foundational/conceptual gaps in the corpus.
- **MMR (Maximal Marginal Relevance)** with lambda 0.5-0.7 prevents near-duplicate chunks dominating top-k. Lower lambda = more diversity, higher = more relevance.
- **ColBERT / ColBERTv2** late-interaction is still relevant in 2026 for zero-shot cross-domain. Use via RAGatouille for training on custom data.
- **Self-query** (LLM extracts metadata filters from natural language: "Python tutorials from 2024" → filter `{language:python, year:>=2024}`) requires a clean metadata schema; messy metadata = poor extraction.

## Contextual Retrieval (Anthropic) -- the high-impact local pattern

Prepend chunk-specific explanatory context (LLM-generated from the full document) before embedding AND BM25 indexing.

**Reported impact**: 49% fewer failed retrievals, **67% when combined with reranking**.

```python
CONTEXT_PROMPT = """
{whole_document}

Here is the chunk we want to situate within the whole document:
{chunk_content}

Give a short succinct context to situate this chunk within the overall
document for improving search retrieval. Answer only with the context.
"""
```

Example transformation:
- **Before**: "The company's revenue grew by 3% over the previous quarter."
- **After**: "This chunk is from an SEC filing on ACME corp's Q2 2023 performance; previous quarter revenue was $314M. The company's revenue grew by 3% over the previous quarter."

## Reranker call shapes (sanity reference)

```python
# Cohere
import cohere
co = cohere.Client("API_KEY")
co.rerank(model="rerank-v3.5", query="...", documents=docs, top_n=5)

# Voyage (instruction-aware)
import voyageai
vo = voyageai.Client()
vo.rerank(model="rerank-2.5", query="...", documents=docs, top_k=5,
          instruction="Prefer documents that cite primary sources.")
```

## Official docs

- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval (cookbook: https://github.com/anthropics/anthropic-cookbook/blob/main/skills/contextual-embeddings/guide.ipynb)
- RRF original paper (Cormack et al.): https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
- Cohere Rerank: https://docs.cohere.com/docs/rerank
- Voyage rerank: https://docs.voyageai.com/docs/reranker
- Jina Reranker: https://jina.ai/reranker/
- Mixedbread mxbai-rerank: https://huggingface.co/mixedbread-ai (model cards)
- ColBERT (RAGatouille): https://github.com/bclavie/RAGatouille
- HyDE paper: https://arxiv.org/abs/2212.10496

## Related

- `chunking-strategies.md` -- what feeds this stage
- `advanced-rag-patterns.md` -- agentic retrieval, GraphRAG, CRAG, Self-RAG
- `vector-databases.md` -- the storage layer
- `embedding-models.md` -- the dense-side input to hybrid search
- `production-guide.md` -- semantic caching, observability, security
