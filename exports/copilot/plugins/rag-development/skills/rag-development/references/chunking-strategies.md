# Chunking Strategies for RAG

Recursive 512-token splitting is the right default. Everything else is a specialization with measurable tradeoffs.

## When to use

Picking the right splitter for an ingestion pipeline. For semantic-similarity-based parent/child patterns that interact with retrieval, see `retrieval-patterns.md`.

## Default: Recursive Character Splitting at 512 tokens

**Benchmark**: a Feb 2026 study of 7 strategies across 50 academic papers placed recursive 512-token splitting first at **69% accuracy**; semantic chunking scored **54%**. Use recursive 512 unless you have a specific reason not to.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,                                   # ~12% overlap
    separators=["\n\n", "\n", ". ", " ", ""],
)
```

## Optimal chunk sizes by use case

| Use case | Chunk size | Overlap | Notes |
|----------|-----------|---------|-------|
| General Q&A | 400-512 tok | 10-20% | Best default |
| Code search | 256-512 tok | 15-25% | Preserve function boundaries |
| Legal / compliance | 512-1024 tok | 20% | Larger context needed |
| Conversational | 128-256 tok | 10% | Precise, focused answers |
| Summarization | 1024-2048 tok | 10% | Broader context |

## Gotchas

- **Semantic chunking is rarely worth its compute cost.** NAACL 2025 Findings paper concluded computational costs aren't justified by consistent gains -- fixed 200-word chunks matched or beat semantic chunking across retrieval and generation tasks. Use only when documents have highly variable topic density AND budget allows it.
- **Overlap > 25% wastes index space without measurable recall gain.** 10-20% is the sweet spot.
- **Markdown-aware splitting** (`MarkdownHeaderTextSplitter` from LangChain) is much better for documentation than recursive char -- preserves header hierarchy as metadata.
- **Parent-child (small-to-big)**: index small chunks (128-256 tok) for precise retrieval, return parent chunks (1024-2048 tok) for LLM context. LlamaIndex has `SentenceWindowNodeParser` (sentence-level children with window) and `HierarchicalNodeParser` (multi-level).
- **Late chunking** (Jina, 2024): embed the full document with a long-context model first, THEN split (mean-pool token embeddings within chunk boundaries). Preserves cross-chunk context like pronouns, headers. Available in `jina-embeddings-v3`.
- **Agentic chunking** (LLM picks boundaries): expensive at indexing time but highest quality for heterogeneous documents -- worth it for small high-value corpora, not for wikipedia-scale.

## Document preprocessing tools (which one for what)

| Tool | Strength | License | Notes |
|------|----------|---------|-------|
| **Unstructured.io** | Element-level extraction (Title / NarrativeText / ListItem / Table / Image) | Apache 2.0 | Table extraction score 0.844, hallucination 0.036 |
| **LlamaParse** | PDF + LlamaIndex integration | Commercial | Best PDF accuracy in the LlamaIndex ecosystem |
| **Docling (IBM)** | Open-source, good accuracy | MIT | Strong on technical PDFs |
| **Apache Tika** | Broadest format support | Apache 2.0 | Lower extraction accuracy; use as fallback |

## Official docs

- LangChain text splitters: https://python.langchain.com/docs/concepts/text_splitters
- LlamaIndex node parsers (parent-child): https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/
- Jina late chunking: https://jina.ai/news/late-chunking-in-long-context-embedding-models/ (paper https://arxiv.org/pdf/2409.04701, code https://github.com/jina-ai/late-chunking)
- Unstructured.io: https://docs.unstructured.io/open-source/introduction/overview
- Docling: https://github.com/DS4SD/docling
- LlamaParse: https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/

## Related

- `retrieval-patterns.md` -- how chunk size interacts with reranker context windows
- `embedding-models.md` -- max-token limits per embedding model
- `advanced-rag-patterns.md` -- RAPTOR / contextual retrieval / parent-child interplay
