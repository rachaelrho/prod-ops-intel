"""
Retrieval module for operational decision support.

This module handles:
- Document chunking strategies (fixed-size, recursive, semantic)
- Embedding generation (API-based and self-hosted)
- Vector storage and retrieval (FAISS, optionally pgvector)
- Hybrid search (BM25 + dense retrieval)
- Reranking (optional)
"""
