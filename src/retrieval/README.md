# Retrieval Module

Core retrieval infrastructure for operational decision support.

## Architecture

```
retrieval/
├── __init__.py
├── chunking.py          # Document chunking strategies
├── embeddings.py        # Embedding model wrappers
├── vector_store.py      # FAISS/pgvector abstraction
├── hybrid_search.py     # BM25 + dense retrieval
└── reranking.py         # Optional reranking layer
```

## Design Decisions

### Chunking Strategy Selection
Different document types require different chunking approaches:
- **Policy documents**: Recursive chunking preserves rule-exception relationships
- **SOPs**: Semantic chunking maintains procedural step coherence
- **Product specs**: Fixed-size with overlap handles structured information

Implemented strategies measured on precision@k across document types.

### Embedding Model Tradeoffs
Two approaches tested with documented cost/latency/quality tradeoffs:
- **API-based** (text-embedding-3-small/large): Lower latency, Matryoshka dimension support
- **Self-hosted** (gte-large): No per-query cost, batch optimization

Selection depends on query volume and retrieval quality requirements.

### Hybrid Search Rationale
Operational queries span semantic similarity and exact matching:
- "What's our return policy for opened products?" → Dense retrieval (semantic)
- "Order #12345 status" → BM25 (keyword exact match)
- "Customer damaged shipment, what do we offer?" → Hybrid

Tunable alpha parameter balances retrieval strategies based on query type distribution.

### Vector Store Backend
- **Development**: FAISS for fast local iteration
- **Production consideration**: pgvector for metadata filtering when corpus grows
  - Filter by document type (policy/SOP/product-info)
  - Filter by last-updated date for version control
  - Filter by authority level for escalation routing

## Implementation Notes

All retrieval components expose unified interfaces to enable architecture comparisons without pipeline changes. Configuration-driven to support A/B testing across embedding models, chunk strategies, and hybrid search parameters.

Evaluation framework measures retrieval quality independently from decision quality, enabling targeted optimization.
