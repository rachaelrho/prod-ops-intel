"""
Hybrid search combining BM25 (lexical) and dense (semantic) retrieval.

Alpha controls the blend:
  alpha=1.0  -> pure dense (semantic similarity only)
  alpha=0.0  -> pure BM25 (keyword overlap only)
  alpha=0.5  -> equal blend (default)

Keyword-heavy queries (order IDs, SKU names) favor low alpha.
Semantic queries (policy interpretation, "what are the conditions for X") favor high alpha.
"""

import logging
from typing import List, Dict, Any

import numpy as np
from rank_bm25 import BM25Okapi

from .retrieval_system import RetrievalSystem

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid BM25 + dense retriever built on top of RetrievalSystem.

    Maintains a BM25 index over the same chunk corpus as the FAISS index.
    At query time, scores from both are normalized to [0,1] and blended
    via alpha before ranking.
    """

    def __init__(self, retrieval_system: RetrievalSystem):
        """
        Args:
            retrieval_system: A RetrievalSystem with documents ingested and index built.
        """
        self.rs = retrieval_system
        self.bm25: BM25Okapi | None = None

    def build_bm25_index(self) -> None:
        """Build BM25 index over the same chunks already in RetrievalSystem."""
        if not self.rs.chunks:
            raise ValueError("RetrievalSystem has no chunks. Ingest documents first.")

        logger.info(f"Building BM25 index over {len(self.rs.chunks)} chunks...")
        tokenized = [chunk["text"].lower().split() for chunk in self.rs.chunks]
        self.bm25 = BM25Okapi(tokenized)
        logger.info("BM25 index built.")

    def search(
        self,
        query: str,
        k: int = 3,
        alpha: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k chunks using hybrid BM25 + dense scoring.

        Args:
            query: Search query text.
            k: Number of results to return.
            alpha: Dense weight. 1.0 = dense only, 0.0 = BM25 only.

        Returns:
            List of chunk dicts ordered by combined score, each augmented with
            bm25_score, dense_score, and combined_score (all normalized to [0,1]).
        """
        if self.bm25 is None:
            raise ValueError("BM25 index not built. Call build_bm25_index() first.")
        if self.rs.index is None:
            raise ValueError("FAISS index not built. Call RetrievalSystem.build_index() first.")

        n = len(self.rs.chunks)

        # --- BM25 scores ---
        bm25_raw = self.bm25.get_scores(query.lower().split())  # shape (n,)
        bm25_max = bm25_raw.max()
        bm25_norm = bm25_raw / bm25_max if bm25_max > 0 else bm25_raw

        # --- Dense scores (all chunks) ---
        query_vec = np.array([self.rs.embedder.embed(query)]).astype("float32")
        distances, indices = self.rs.index.search(query_vec, n)

        dense_raw = np.zeros(n, dtype=np.float32)
        for dist, idx in zip(distances[0], indices[0]):
            dense_raw[idx] = 1.0 / (1.0 + dist)  # lower L2 distance -> higher score

        dense_max = dense_raw.max()
        dense_norm = dense_raw / dense_max if dense_max > 0 else dense_raw

        # --- Combine ---
        combined = alpha * dense_norm + (1.0 - alpha) * bm25_norm
        top_indices = np.argsort(combined)[::-1][:k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            chunk = self.rs.chunks[idx].copy()
            chunk["rank"] = rank
            chunk["bm25_score"] = float(bm25_norm[idx])
            chunk["dense_score"] = float(dense_norm[idx])
            chunk["combined_score"] = float(combined[idx])
            results.append(chunk)

        return results

    def compare_alphas(
        self,
        query: str,
        alphas: List[float],
        k: int = 3,
    ) -> Dict[float, List[Dict[str, Any]]]:
        """
        Run the same query at multiple alpha values for comparison.

        Useful for identifying where keyword retrieval overtakes semantic retrieval
        (or vice versa) for a given query type.

        Args:
            query: Search query text.
            alphas: List of alpha values to try, e.g. [0.0, 0.25, 0.5, 0.75, 1.0].
            k: Results per alpha.

        Returns:
            Dict mapping alpha -> search results.
        """
        return {alpha: self.search(query, k=k, alpha=alpha) for alpha in alphas}
