# RAG Development Plugin

> Design, build, and audit Retrieval-Augmented Generation systems. Covers the full pipeline from document chunking to answer generation, with deep Qdrant expertise and advanced patterns.

## Agents

### `rag-architect`

Expert in RAG system design covering the full pipeline -- ingestion, chunking, embeddings, vector storage, retrieval, re-ranking, and answer generation.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Pipeline design, chunking strategy selection, hybrid search, production optimization |

**Invocation:**
```
Use the rag-architect to design a RAG pipeline for our knowledge base
```

**Expertise:**
- Chunking strategies (recursive, semantic, markdown-aware, parent-child, agentic)
- Embedding model selection (OpenAI, Cohere, open-source)
- Advanced patterns: Graph RAG, CRAG, Self-RAG, Agentic RAG
- Evaluation with RAGAS and DeepEval
- Cost/latency/accuracy trade-offs

---

### `qdrant-expert`

Qdrant vector database specialist for collection configuration, HNSW tuning, quantization, and production deployment.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Qdrant setup, HNSW parameter tuning, quantization, hybrid search, multi-tenancy |

**Invocation:**
```
Use the qdrant-expert to optimize our collection for 10M documents
```

**Expertise:**
- Collection configuration (named vectors, distance metrics, sharding, WAL)
- HNSW index tuning (`m`, `ef_construct`, `ef`, `full_scan_threshold`)
- Scalar INT8 quantization (75% memory reduction)
- GPU-accelerated indexing and ACORN algorithm
- Payload indexing and filtering

---

## Skills

### `rag-development`

Knowledge base covering every stage of RAG development.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Building RAG pipelines, choosing components, implementing advanced patterns |

**Quick start recipe:**
1. Chunking: recursive character splitting at 512 tokens, 10-15% overlap
2. Embedding: OpenAI `text-embedding-3-small` or Cohere `embed-v4`
3. Vector DB: Qdrant with scalar INT8 quantization
4. Retrieval: hybrid search (dense + sparse + RRF)
5. Evaluation: RAGAS from day one

**Reference docs:**
- `references/chunking-strategies.md` - Splitting approaches by document type
- `references/embedding-models.md` - Model comparison and selection
- `references/retrieval-patterns.md` - Search, re-ranking, and fusion
- `references/advanced-rag-patterns.md` - Graph RAG, CRAG, Self-RAG, Agentic RAG
- `references/vector-databases.md` - DB comparison and selection
- `references/production-guide.md` - Deployment, monitoring, scaling

---

## Commands

### `/rag-audit`

Audit a RAG implementation for quality, performance, and best practices.

```
/rag-audit src/rag/
/rag-audit "our customer support chatbot pipeline"
```

**Audit covers:** chunking quality, embedding model fit, vector DB configuration, retrieval/search logic, re-ranking setup, prompt construction, and evaluation coverage. Produces an actionable report with prioritized improvements.

---

**Related:** [research](research.md) (web fetching for knowledge ingestion) | [python-development](python-development.md) (Python implementation)
