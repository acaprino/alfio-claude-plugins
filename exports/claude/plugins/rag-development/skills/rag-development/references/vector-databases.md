# Vector Databases

## Comparison

| Database | Best For | Language | Hosting | Key Strength |
|----------|---------|---------|---------|-------------|
| **Qdrant** | Complex filtered search, production RAG | Rust | Self-host / Cloud | Payload filtering, quantization, hybrid search |
| **Pinecone** | Turnkey managed, enterprise | - | Managed only | Zero-ops, serverless, fastest time-to-production |
| **Weaviate** | Knowledge graph + vectors, GraphQL | Go | Self-host / Cloud | Schema-aware, built-in vectorizers, multi-modal |
| **Milvus** | Billion-scale, GPU-accelerated | Go/C++ | Self-host / Zilliz Cloud | Most index types (IVF, HNSW, DiskANN), GPU support |
| **ChromaDB** | Prototyping, small projects | Python | Self-host | Simplest API, in-process mode, fast setup |
| **pgvector** | Existing Postgres stack, mixed workloads | C | Self-host (ext) | SQL integration, no new infra, ACID transactions |

## Decision Framework

- **Prototyping**: ChromaDB (simplest) or pgvector (if already using Postgres)
- **Production RAG with filtering**: Qdrant or Weaviate
- **Managed/zero-ops**: Pinecone
- **Billion-scale**: Milvus with GPU
- **Existing Postgres**: pgvector
- **Knowledge graphs + vectors**: Weaviate

## Qdrant Deep Dive

See the `qdrant-expert` agent for comprehensive Qdrant configuration. Key highlights:

### Quantization Options
- **Scalar INT8**: 75% memory reduction, ~1% accuracy loss. Best default.
- **Binary**: 32x compression, 40x speedup. Best for >1024 dim models (OpenAI, Cohere).
- **Product Quantization**: Highest compression, higher accuracy trade-off.

### HNSW Parameters
- `m=16` (default) -- connections per node; 16-32 for text
- `ef_construct=100` (default) -- build quality; higher = better index
- `ef` (search-time) -- tune for recall/speed trade-off

### 2025 Features
- GPU-accelerated HNSW indexing
- Inline storage (quantized vectors embedded in graph)
- ACORN algorithm for filtered HNSW
- Score-Boosting Reranking
- Native MMR support

## Scaling Strategies

### Sharding
Distribute vectors across nodes by collection or hash. Milvus and Qdrant support automatic sharding.

### Replication
Read replicas for high-throughput scenarios. Qdrant supports configurable replication factor.

### Tiered Storage
- Hot: RAM (quantized vectors + HNSW graph)
- Warm: SSD with mmap (on-disk vectors)
- Cold: Disk with quantization (archive)

### Index-on-Disk
For cost-sensitive deployments: on-disk HNSW with quantized vectors in RAM for rescoring.

## pgvector Notes

Best for teams already running Postgres who want to avoid new infrastructure:
- `ivfflat` index: faster build, lower recall
- `hnsw` index: slower build, better recall (recommended)
- Limitations: no native sparse vectors, no built-in hybrid search, no quantization
- Use with `pgvector-scale` or `pgvectorscale` for improved performance

## References
- https://qdrant.tech/documentation/
- https://qdrant.tech/documentation/guides/optimize/
- https://qdrant.tech/articles/vector-search-resource-optimization/
- https://liquidmetal.ai/casesAndBlogs/vector-comparison/
- https://www.firecrawl.dev/blog/best-vector-databases
