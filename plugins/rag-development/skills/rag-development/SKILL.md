---
name: rag-development
description: >
  Knowledge base for production question-answering pipelines.
  TRIGGER WHEN: building, optimizing, or auditing RAG systems, including Graph RAG, CRAG, Self-RAG,
  and Agentic RAG.
---

# RAG Development

Comprehensive knowledge base for building production-grade Retrieval-Augmented Generation systems.

## When to Use

- Building a new RAG pipeline from scratch
- Choosing chunking strategy, embedding model, or vector database
- Implementing hybrid search, re-ranking, or contextual retrieval
- Evaluating RAG quality with RAGAS or DeepEval
- Optimizing production RAG for cost, latency, or accuracy
- Designing multi-tenant RAG with access control
- Upgrading from naive RAG to advanced patterns

## Quick Start Recommendation

For 80% of use cases, start with:
1. **Chunking**: Recursive character splitting at 512 tokens, 10-15% overlap
2. **Embedding**: OpenAI `text-embedding-3-small` (best value) or Cohere `embed-v4` (best accuracy)
3. **Vector DB**: Qdrant with scalar INT8 quantization
4. **Retrieval**: Hybrid search (dense + sparse + RRF)
5. **Evaluation**: RAGAS metrics from day one

Then upgrade incrementally based on measured failures:
- Keyword misses -> add sparse vectors (SPLADE/BM25)
- Ambiguous chunks -> add contextual retrieval (Anthropic pattern)
- Irrelevant results -> add cross-encoder re-ranking
- Multi-hop failures -> upgrade to agentic RAG

## Reference Materials

Detailed reference documents are in the `references/` directory:

- `chunking-strategies.md` -- all chunking approaches with code, benchmarks, and selection guide
- `embedding-models.md` -- model comparison, Matryoshka embeddings, fine-tuning, sparse/dense/multi-vector
- `retrieval-patterns.md` -- hybrid search, HyDE, contextual retrieval, re-ranking, MMR
- `advanced-rag-patterns.md` -- Graph RAG, RAPTOR, CRAG, Self-RAG, Agentic RAG, multi-modal RAG
- `vector-databases.md` -- Qdrant deep dive, database comparison, scaling strategies
- `production-guide.md` -- evaluation, observability, caching, security, cost optimization

## Pipeline Architecture

```
Document Ingestion:
  Raw Docs -> Preprocessing (Unstructured.io) -> Chunking -> Context Enrichment -> Embedding -> Vector DB

Query Pipeline:
  User Query -> Query Transform -> Encode (Dense + Sparse) -> Hybrid Search -> Re-rank -> LLM Generation

Evaluation Loop:
  Ground Truth + Predictions -> RAGAS/DeepEval -> Faithfulness, Relevancy, Precision, Recall
```

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Chunking | Recursive 512 tok | Structured docs -> markdown-aware; cross-refs -> late chunking |
| Embedding | text-embedding-3-small | Need accuracy -> embed-v4; self-hosted -> NV-Embed-v2 |
| Vector DB | Qdrant + INT8 | Already on Postgres -> pgvector; need managed -> Pinecone |
| Search | Dense only | Keyword misses -> add sparse hybrid; poor diversity -> add MMR |
| Re-ranking | None | Top-k results contain irrelevant items -> add Cohere Rerank |
| Caching | None | Production latency/cost concerns -> semantic cache |
| Evaluation | Manual spot checks | Any production use -> RAGAS automated metrics |
