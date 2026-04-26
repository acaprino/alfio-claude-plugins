# Production RAG Guide

Evaluation, observability, semantic caching, security, and the framework-overhead matrix that drives "build vs adopt" decisions.

## When to use

Hardening a RAG pipeline for production -- adding evaluation cadence, observability, caching, security boundaries, or picking between LangChain/LlamaIndex/Haystack/DSPy/from-scratch.

## Evaluation cadence (the operational rule)

- **Baseline scoring**: weekly minimum.
- **Regression evaluation triggers**: model updates, embedding refreshes, corpus changes, reranker swaps.
- **Stack**: RAGAS during design → DeepEval gates in CI → TruLens / Langfuse in production. Detail: see `advanced-rag-patterns.md` § Evaluation frameworks.

Core metrics worth scoring: Faithfulness (answer grounded in context), Answer Relevancy, Context Precision (chunks relevant), Context Recall (chunks cover ground truth), Hallucination rate.

## Semantic caching (high-leverage local pattern)

Recognize semantically equivalent queries (cosine > 0.95) and serve cached answers.

**Reported impact** (the numbers worth keeping):
- p95 response time: **2.1s → 450ms**
- API cost reduction: **50-80%**
- Hit rate: **45-65% first week, 60-80% over time** as the cache warms.

**RAGCache** (advanced): caches intermediate KV-cache states in a knowledge tree across GPU/host memory; up to **4× TTFT reduction**.

## Cost optimization checklist

- Matryoshka embeddings for two-stage retrieval (cheap broad, expensive narrow)
- Vector quantization (INT8 = ~75% memory savings vs fp32)
- Semantic caching for repeats / near-duplicates
- Batch embedding requests at ingestion
- Smaller models for evaluator/grader roles
- Anthropic prompt caching for contextual retrieval (the contextual prompt has heavy doc reuse)

## Latency optimization checklist

- Pre-compute embeddings at ingestion, never at query time
- Scalar quantization + in-memory index for sub-ms vector search
- Cap retrieval at top-k 5-10 (diminishing returns past that)
- Stream LLM responses
- Async parallel retrieval across indexes
- Two-stage Matryoshka retrieval to skip the expensive embedding for early filtering

Target: see `retrieval-patterns.md` (< 200ms total for retrieve + rerank + fetch).

## Security

### Prompt injection

- Strict context adherence -- responses limited to specific tasks.
- Specify output format, **require source citations**.
- Input sanitization: strip control characters, detect known injection patterns.
- Multi-layer defense: input filters + structured templates + output validation.

### Data access control

- **Mandatory `tenant_id` filter on every query in multi-tenant systems** -- omitting this is the #1 security incident in production RAG. Make it impossible to skip at the framework / wrapper layer.
- Namespace boundaries scoped by role / purpose.
- Per-user / per-query namespace restrictions via payload filtering.
- Principle of least privilege for the RAG application's data permissions.

### PII

- Filter / redact PII at ingestion **before embedding** (embeddings can leak training data otherwise).
- NER (Named Entity Recognition) for names, emails, addresses, financial data.
- Sanitize both user prompts and final responses.
- Audit logging for all data access.

## Framework matrix (build vs adopt)

| Framework | Best for | Overhead | Connectors |
|-----------|----------|----------|-----------|
| **LlamaIndex** | Pure RAG, document Q&A | ~6 ms | 150+ data connectors |
| **LangChain** | Complex agentic workflows | ~10 ms | Broadest integrations |
| **LangGraph** | Stateful agent orchestration | ~14 ms | LangChain ecosystem |
| **Haystack** | Production NLP, regulated workloads | ~5.9 ms | Modular pipeline components |
| **DSPy** | Prompt optimization | ~3.5 ms | Programmatic prompt tuning |
| **From scratch** | Maximum control | 0 ms | Whatever you wire |

### When to build from scratch (the local heuristic)

- Maximum control over latency / cost is a hard requirement.
- Highly specialized retrieval pattern that doesn't fit framework abstractions.
- Avoiding framework lock-in is strategically important.
- You have a strong ML engineering team to maintain it.
- Pipeline is fundamentally simple (embed → search → generate).

A minimal RAG pipeline is **~50-100 lines of Python**. If your pipeline is genuinely simple, the framework adds more friction than value.

## Observability tooling (the production triad)

| Tool | Type | Key feature |
|------|------|-------------|
| **LangSmith** | Commercial | Deep LangChain integration, multi-step tracing |
| **Langfuse** | Open-source | Tracing + prompt versioning + dataset creation |
| **Arize Phoenix** | Open-source | Real-time observability + drift detection |

Pragmatic choice for new builds: **RAGAS / DeepEval for metrics + Langfuse for observability.**

## Official docs

- RAGAS: https://docs.ragas.io/
- DeepEval: https://docs.confident-ai.com/ (RAG metrics: https://deepeval.com/docs/metrics-ragas)
- Langfuse: https://langfuse.com/ (RAG eval cookbook: https://langfuse.com/guides/cookbook/evaluation_of_rag_with_ragas)
- TruLens: https://www.trulens.org/
- Arize Phoenix: https://phoenix.arize.com/
- LangSmith: https://docs.smith.langchain.com/
- LlamaIndex: https://docs.llamaindex.ai/
- LangChain: https://python.langchain.com/
- Haystack: https://haystack.deepset.ai/
- DSPy: https://dspy.ai/
- OWASP LLM Top 10: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OWASP LLM Prompt Injection Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- AWS securing RAG ingestion: https://aws.amazon.com/blogs/security/securing-the-rag-ingestion-pipeline-filtering-mechanisms/

## Related

- `advanced-rag-patterns.md` -- evaluation framework details
- `retrieval-patterns.md` -- the latency target this guide assumes
- `vector-databases.md` -- the storage layer's quantization options
- `embedding-models.md` -- the cost driver this guide caches
