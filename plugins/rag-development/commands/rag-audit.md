---
description: >
  Audit an existing RAG implementation for quality, performance, and best practices.
  TRIGGER WHEN: the user asks to review, audit, or validate a RAG pipeline -- chunking, embeddings, retrieval, reranking, or production readiness.
  DO NOT TRIGGER WHEN: building a new RAG system from scratch (use rag-architect agent) or auditing a pure vector DB (use qdrant-expert).
argument-hint: "[path-or-description]"
---

# RAG Audit

Analyze an existing RAG implementation and produce an actionable audit report.

## Instructions

1. **Identify RAG components** in the codebase:
   - Document ingestion/chunking code
   - Embedding model usage
   - Vector database configuration
   - Retrieval/search logic
   - Re-ranking (if any)
   - Prompt construction for LLM generation
   - Evaluation setup (if any)

2. **Audit each component** against best practices:

### Chunking
- [ ] Chunk size appropriate for use case (400-512 tokens default)
- [ ] Overlap configured (10-20%)
- [ ] Document preprocessing handles tables, images, headers
- [ ] Chunking strategy matches document structure

### Embeddings
- [ ] Model is current (not deprecated)
- [ ] Dimensions appropriate (not over-provisioned)
- [ ] Embeddings cached at ingestion (not re-computed)

### Vector Database
- [ ] Payload indexes created on filtered fields
- [ ] Quantization enabled (INT8 minimum for production)
- [ ] HNSW parameters tuned (m >= 16, ef_construct >= 100)
- [ ] On-disk storage configured for large collections

### Retrieval
- [ ] Hybrid search implemented (dense + sparse)
- [ ] Re-ranking applied (cross-encoder or Cohere Rerank)
- [ ] Metadata filtering for multi-tenancy/access control
- [ ] MMR or diversity mechanism to avoid duplicate results

### Generation
- [ ] Context window usage efficient (not stuffing irrelevant chunks)
- [ ] Source attribution in responses
- [ ] Streaming enabled for user experience

### Production
- [ ] Evaluation metrics in place (RAGAS or equivalent)
- [ ] Observability/tracing configured
- [ ] Semantic caching for repeat queries
- [ ] Error handling for embedding API failures
- [ ] Rate limiting and cost controls

### Security
- [ ] Tenant isolation enforced via mandatory filters
- [ ] PII filtering at ingestion
- [ ] Input sanitization for prompt injection
- [ ] Output validation

3. **Generate report** with:
   - Current state assessment (what's implemented)
   - Risk areas (what's missing or misconfigured)
   - Priority improvements (ordered by impact)
   - Code examples for each recommendation
