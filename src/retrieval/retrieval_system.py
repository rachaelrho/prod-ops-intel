"""
Production retrieval system for operational policy documents.

Uses validated configuration from Day 1 experiments:
- Chunking: Recursive strategy (respects document structure)
- Embeddings: GTE-Large (self-hosted, equivalent accuracy, better latency)
- Indexing: FAISS flat L2 search

This system provides document ingestion, indexing, and semantic search
for operational decision support queries.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss

from .chunking import DocumentChunker
from .embeddings import SentenceTransformerEmbedder

logger = logging.getLogger(__name__)


class RetrievalSystem:
    """
    Production retrieval system for operational policy documents.

    Handles document ingestion, chunking, embedding, indexing, and querying
    using validated configuration from experiments.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        embedding_model: str = "thenlper/gte-large",
        cache_embeddings: bool = True
    ):
        """
        Initialize retrieval system with validated configuration.

        Args:
            chunk_size: Token size for chunks (default: 512, validated in experiments)
            chunk_overlap: Token overlap between chunks (default: 50)
            embedding_model: Model for embeddings (default: gte-large, validated)
            cache_embeddings: Cache embeddings for efficiency (default: True)
        """
        logger.info("Initializing production retrieval system...")
        logger.info(f"  Chunking: recursive strategy, size={chunk_size}, overlap={chunk_overlap}")
        logger.info(f"  Embeddings: {embedding_model}")

        # Initialize components
        self.chunker = DocumentChunker()
        self.embedder = SentenceTransformerEmbedder(
            model_name=embedding_model,
            cache=cache_embeddings
        )

        # Configuration
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Storage
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.Index] = None

        logger.info("✓ Retrieval system initialized")

    def ingest_document(
        self,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Ingest a single document into the retrieval system.

        Args:
            content: Document text content
            source: Document source identifier (filename, URL, etc.)
            metadata: Additional metadata to attach to chunks

        Returns:
            Number of chunks created from this document
        """
        logger.info(f"Ingesting document: {source}")

        # Chunk document using recursive strategy (validated in Exp 1)
        doc_chunks = self.chunker.chunk_document(
            content,
            strategy='recursive',
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        # Add source and metadata
        for chunk_dict in doc_chunks:
            chunk_dict['source'] = source
            if metadata:
                chunk_dict['metadata'] = metadata
            self.chunks.append(chunk_dict)

        logger.info(f"  ✓ Created {len(doc_chunks)} chunks")
        return len(doc_chunks)

    def ingest_documents_from_directory(
        self,
        directory: Path,
        pattern: str = "*.md",
        metadata_fn: Optional[callable] = None
    ) -> Dict[str, int]:
        """
        Ingest all documents from a directory.

        Args:
            directory: Path to directory containing documents
            pattern: Glob pattern for files to ingest (default: *.md)
            metadata_fn: Optional function to generate metadata from filename

        Returns:
            Dictionary mapping source names to chunk counts
        """
        logger.info(f"Ingesting documents from: {directory}")
        logger.info(f"  Pattern: {pattern}")

        directory = Path(directory)
        doc_files = sorted(directory.glob(pattern))

        if not doc_files:
            logger.warning(f"No files found matching pattern: {pattern}")
            return {}

        chunk_counts = {}
        for doc_path in doc_files:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = metadata_fn(doc_path.name) if metadata_fn else None
            chunk_count = self.ingest_document(
                content=content,
                source=doc_path.name,
                metadata=metadata
            )
            chunk_counts[doc_path.name] = chunk_count

        logger.info(f"✓ Ingested {len(doc_files)} documents, {len(self.chunks)} total chunks")
        return chunk_counts

    def build_index(self) -> None:
        """
        Build FAISS index from ingested documents.

        Embeds all chunks using GTE-Large and creates flat L2 index for
        efficient similarity search.
        """
        if not self.chunks:
            raise ValueError("No documents ingested. Call ingest_document() first.")

        logger.info(f"Building index from {len(self.chunks)} chunks...")

        # Extract chunk texts
        chunk_texts = [chunk['text'] for chunk in self.chunks]

        # Embed using validated model (GTE-Large from Exp 2)
        logger.info("  Embedding chunks...")
        embeddings_list = self.embedder.embed_batch(chunk_texts)
        self.embeddings = np.array(embeddings_list).astype('float32')

        # Build FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings)

        # Log stats
        stats = self.embedder.get_stats()
        logger.info(f"✓ Index built: {len(self.chunks)} chunks, {dimension} dimensions")
        logger.info(f"  Embedding time: {stats['total_time']:.2f}s")
        logger.info(f"  Avg time per chunk: {stats['avg_time']*1000:.1f}ms")

    def search(
        self,
        query: str,
        k: int = 3,
        return_scores: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using semantic similarity.

        Args:
            query: Search query text
            k: Number of results to return (default: 3)
            return_scores: Include similarity scores in results (default: False)

        Returns:
            List of chunk dictionaries with metadata, optionally including scores
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Embed query
        query_embedding = self.embedder.embed(query)
        query_vector = np.array([query_embedding]).astype('float32')

        # Search
        distances, indices = self.index.search(query_vector, k)

        # Compile results
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
            chunk = self.chunks[idx].copy()
            chunk['rank'] = rank

            if return_scores:
                # Convert L2 distance to similarity score (lower distance = higher similarity)
                chunk['distance'] = float(dist)
                chunk['similarity_score'] = 1 / (1 + float(dist))

            results.append(chunk)

        return results

    def get_context_window(
        self,
        query: str,
        k: int = 3,
        max_tokens: int = 2000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get concatenated context window for LLM prompting.

        Retrieves top-k chunks and concatenates them into a context string,
        respecting max_tokens limit. Useful for RAG applications.

        Args:
            query: Search query text
            k: Number of chunks to retrieve
            max_tokens: Maximum tokens in context window

        Returns:
            Tuple of (context_string, source_chunks)
        """
        results = self.search(query, k=k, return_scores=True)

        # Build context respecting token limit
        context_parts = []
        total_tokens = 0
        included_chunks = []

        for result in results:
            chunk_tokens = result['token_count']
            if total_tokens + chunk_tokens > max_tokens:
                logger.debug(f"Context window limit reached: {total_tokens}/{max_tokens} tokens")
                break

            context_parts.append(f"[Source: {result['source']}]\n{result['text']}")
            total_tokens += chunk_tokens
            included_chunks.append(result)

        context = "\n\n---\n\n".join(context_parts)

        logger.debug(f"Context window: {len(included_chunks)} chunks, {total_tokens} tokens")
        return context, included_chunks

    def get_stats(self) -> Dict[str, Any]:
        """
        Get retrieval system statistics.

        Returns:
            Dictionary with system stats (chunks, embeddings, index info)
        """
        stats = {
            'total_chunks': len(self.chunks),
            'indexed': self.index is not None,
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else None,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
        }

        if self.chunks:
            sources = set(chunk['source'] for chunk in self.chunks)
            stats['unique_sources'] = len(sources)
            stats['sources'] = sorted(sources)

            token_counts = [chunk['token_count'] for chunk in self.chunks]
            stats['avg_chunk_tokens'] = np.mean(token_counts)
            stats['min_chunk_tokens'] = np.min(token_counts)
            stats['max_chunk_tokens'] = np.max(token_counts)

        # Add embedding stats
        if self.embedder:
            stats['embedding_stats'] = self.embedder.get_stats()

        return stats

    def clear(self) -> None:
        """Clear all ingested documents and index."""
        self.chunks = []
        self.embeddings = None
        self.index = None
        logger.info("Retrieval system cleared")
