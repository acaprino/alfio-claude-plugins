# Embedding Models & Strategies

MTEB scores drift as leaderboard versions change; prefer linking the [live MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) over hardcoding numbers. Snapshot dates noted per row.

## Commercial Models (2025-2026)

| Model | Released | Dims (Matryoshka) | Max Tokens | Price / 1M tokens | Notes |
|-------|----------|-------------------|------------|-------------------|-------|
| Voyage voyage-4-large | 2026-01-15 | 1024 (256/512/1024/2048) | 32,000 | See vendor pricing | Flagship; MoE; shared embedding space with v4 family |
| Voyage voyage-4 | 2026-01-15 | 1024 (256/512/1024/2048) | 32,000 | See vendor pricing | General balance cost / accuracy |
| Voyage voyage-4-lite | 2026-01-15 | 1024 (256/512/1024/2048) | 32,000 | See vendor pricing | Latency / cost optimized |
| Voyage voyage-3-large | 2025-01-07 | 1024 (256/512/1024/2048) | 32,000 | See vendor pricing | Pre-v4 flagship; beat OpenAI v3-large by 9.74% avg over 100 datasets |
| Voyage voyage-3.5 | 2025-05-20 | 1024 (256/512/1024/2048) | 32,000 | $0.06 | Cost / quality sweet spot; +8.26% vs OpenAI v3-large |
| Voyage voyage-3.5-lite | 2025-05-20 | 1024 (256/512/1024/2048) | 32,000 | $0.02 | Cheapest Voyage tier; +6.34% vs OpenAI v3-large at 6.5x lower cost |
| Voyage voyage-code-3 | 2024-12 | 1024 (256/512/1024/2048) | 32,000 | $0.22 | Code retrieval; +13.8% vs OpenAI v3-large on 238 code datasets |
| Voyage voyage-law-2 | 2024 | 1024 | 16,000 | See vendor pricing | Legal domain-tuned |
| Voyage voyage-finance-2 | 2024-06 | 1024 | 32,000 | See vendor pricing | Finance domain-tuned |
| OpenAI text-embedding-3-large | 2024-01 | 3072 (Matryoshka truncatable) | 8,191 | $0.13 | OpenAI stack default |
| OpenAI text-embedding-3-small | 2024-01 | 1536 | 8,191 | $0.02 | Budget option |
| Cohere embed-v4 | 2025-04-15 | 256 / 512 / 1024 / 1536 | 128,000 | $0.12 text ($0.47 per 1M image tokens) | Multimodal (text + image), long context |
| Google gemini-embedding-001 | 2025-03 (GA from exp-03-07) | 3072 (MRL-truncatable to 1536 / 768) | 2,048 | $0.15 ($0.075 batch) | 100+ languages |
| Google gemini-embedding-2-preview | 2026 | [UNVERIFIED] | 8,192 (text) | $0.20 text | First natively multimodal Gemini embedding (text / image / audio / video) |

Note: **OpenAI `text-embedding-4` does not exist as of April 2026.** Use `text-embedding-3-large` for OpenAI stacks.

## Open-Source Models

| Model | Released | Dims | Context | MTEB (snapshot) | License | Notes |
|-------|----------|------|---------|------------------|---------|-------|
| NVIDIA NV-Embed-v2 | 2024-05-27 | 4096 | 32,768 | 72.31 (Aug 2024, #1 English) | CC-BY-NC-4.0 | Non-commercial license; use NVIDIA NeMo NIMs for commercial deployment |
| BAAI BGE-M3 | 2024-02 | 1024 | 8,192 | Strong multilingual | Open | One model produces dense + sparse + ColBERT-style multi-vector outputs; 100+ languages |
| BAAI BGE-EN-ICL | 2024 | [UNVERIFIED] | [UNVERIFIED] | High English | Open | English retrieval with in-context-learning few-shot examples |
| Alibaba gte-Qwen2-7B-instruct | 2024-06 | ~3584 (Qwen2-7B) | [UNVERIFIED] | 70.72 | Open | 7.6B params; #1 EN+ZH MTEB as of June 2024 |
| Stella stella_en_1.5B_v5 | 2024 | [UNVERIFIED] | [UNVERIFIED] | 69.43 | Open | Compact English-only (1.5B params) |
| Mixedbread mxbai-embed-large-v1 | 2024 | 1024 | 512 | [UNVERIFIED] | Apache 2.0 | Matryoshka-capable |
| Mixedbread mxbai-embed-2d-large-v1 | 2024 | [UNVERIFIED] | [UNVERIFIED] | [UNVERIFIED] | Open | 2D Matryoshka (dim + layer reduction) |
| Nomic embed v1.5 | 2024 | 768 (Matryoshka) | 8,192 | ~62 | Open | Reproducible, long-context, English |
| Nomic embed v2 (MoE) | 2025 | 768 (down to 256 via MRL) | 8,192 | Multilingual MoE | Open | First MoE text-embedding, 100+ languages |
| Jina embeddings v3 | 2024-09 | 1024 (Matryoshka to any lower dim) | 8,192 | Top multilingual | CC-BY-NC | Task-specific LoRA adapters (retrieval.query / retrieval.passage / separation / classification / text-matching) |

## Embedding Types

### Dense Vectors (Semantic Meaning)
Single fixed-size vector per chunk. Models like Voyage, OpenAI, Cohere, Gemini produce vectors capturing semantic meaning. Standard approach.

### Sparse Vectors (Keyword / Lexical)
High-dimensional vectors where each dimension = vocabulary term. BM25 or neural sparse models (SPLADE, BGE-M3 sparse output). Best for exact keyword matching, domain terminology, IDs, acronyms.

### Multi-Vector / ColBERT (Late Interaction)
One vector per token. At search time, MaxSim operator finds passages with contextually matching tokens. More nuanced than single-vector but higher storage cost.

```python
# Note: ragatouille (0.1.x) is no longer actively maintained. For production
# ColBERT, consider the colbert-ir reference implementation or a managed late-interaction stack.
from ragatouille import RAGPretrainedModel

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
RAG.index(
    collection=documents,
    index_name="my_index",
    max_document_length=256,
    split_documents=True,
)
results = RAG.search(query="search query", k=5)
```

BGE-M3 produces dense + sparse + ColBERT outputs from a single forward pass -- useful when storage allows hybrid indexing without running three separate models.

## Matryoshka Embeddings

Trained so the first N dimensions form a valid (lower-quality) embedding. Enables:
- **Adaptive retrieval**: 256-dim for fast candidate selection, full-dim for re-ranking
- **Storage optimization**: store smaller embeddings, expand when needed

Supported by: **Voyage 3.x / 4.x family** (256 / 512 / 1024 / 2048), **OpenAI text-embedding-3-\***, **Cohere embed-v4** (256 / 512 / 1024 / 1536), **Gemini embedding-001** (3072 -> 1536 / 768), **Nomic embed v1.5 / v2**, **Jina embeddings v3**, **Mixedbread mxbai-embed-large-v1**.

**Two-stage pattern**:
```python
# Stage 1: fast candidate retrieval with small embeddings
candidates = vector_db.search(query_embedding[:256], limit=100)

# Stage 2: rerank with full embeddings
reranked = rerank_by_full_similarity(query_embedding, candidates)
```

## Fine-Tuning Embeddings

Domain-specific fine-tuning improves retrieval by 5-15% on specialized corpora.

**Approaches**:
- Contrastive learning on (query, positive_doc, negative_doc) triplets
- Synthetic data: use LLM to generate questions from your documents
- `sentence-transformers` library for training
- Cohere and Voyage offer fine-tuning APIs

## Embedding Caching

- Cache embeddings at ingestion time (never re-embed unchanged documents)
- Content hashing to detect document changes
- Store embeddings alongside metadata in vector DB
- Query embedding cache with TTL for frequent queries

## Selection Guide

- **Highest-accuracy commercial, general-purpose** -> Voyage voyage-4-large or voyage-4
- **Cost-optimized commercial (~50x cheaper than flagship)** -> Voyage voyage-3.5-lite ($0.02 / 1M)
- **Multimodal (text + image)** -> Cohere embed-v4 or Gemini embedding-2-preview
- **Long-context (>=32K tokens per doc)** -> Voyage v4 family, Cohere embed-v4 (128K), OpenAI v3-\* (8K)
- **Code retrieval** -> Voyage voyage-code-3
- **Legal / finance domains** -> voyage-law-2 / voyage-finance-2
- **OpenAI stack** -> text-embedding-3-large ($0.13) or text-embedding-3-small ($0.02)
- **Self-hosted, highest English MTEB, research only** -> NV-Embed-v2 (CC-BY-NC)
- **Self-hosted, commercial-safe** -> Mixedbread mxbai-embed-large-v1 (Apache 2.0), BGE-M3, gte-Qwen2-7B-instruct
- **Multilingual self-hosted** -> BGE-M3, Nomic embed v2, Jina embeddings v3
- **Compact / edge deployment** -> stella_en_1.5B_v5 (English), Nomic embed v1.5 (768 dim)
- **Storage efficiency via dimension truncation** -> any Matryoshka-trained model above

## References
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
- [Voyage 4 family announcement](https://blog.voyageai.com/2026/01/15/voyage-4/)
- [Voyage 3.5 announcement](https://blog.voyageai.com/2025/05/20/voyage-3-5/)
- [Voyage 3-large announcement](https://blog.voyageai.com/2025/01/07/voyage-3-large/)
- [Voyage Pricing](https://docs.voyageai.com/docs/pricing)
- [OpenAI Pricing](https://openai.com/api/pricing/)
- [OpenAI New embedding models (2024-01)](https://openai.com/index/new-embedding-models-and-api-updates/)
- [Cohere Embed v4 docs](https://docs.cohere.com/docs/cohere-embed)
- [Gemini Embedding GA](https://developers.googleblog.com/gemini-embedding-available-gemini-api/)
- [Gemini Embedding 2 Preview](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-embedding-2/)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [NV-Embed-v2 HuggingFace](https://huggingface.co/nvidia/NV-Embed-v2)
- [BGE-M3 HuggingFace](https://huggingface.co/BAAI/bge-m3)
- [gte-Qwen2-7B HuggingFace](https://huggingface.co/Alibaba-NLP/gte-Qwen2-7B-instruct)
- [Nomic Embed v2 MoE](https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe)
- [Jina embeddings v3 paper](https://arxiv.org/pdf/2409.10173)
- [ColBERTv2 via RAGatouille](https://github.com/AnswerDotAI/RAGatouille)
