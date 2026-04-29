"""
Embedding model wrappers for document retrieval.

Provides unified interface for API-based (OpenAI) and self-hosted
(sentence-transformers) embedding models. Includes cost tracking,
batching, and caching for efficient experimentation.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    """
    Abstract base class for embedding models.

    Provides consistent interface for different embedding providers,
    enabling easy model comparison and swapping.
    """

    def __init__(self, cache: bool = False):
        """
        Initialize embedder.

        Args:
            cache: Whether to cache embeddings for repeated text
        """
        self.cache = cache
        self._cache_dict: Dict[str, List[float]] = {}
        self.total_tokens = 0
        self.total_cost = 0.0
        self.total_time = 0.0
        self.embed_count = 0

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Embed single text into vector.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats)
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts efficiently in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """
        Get embedding statistics.

        Returns:
            Dict with tokens, cost, time, count metrics
        """
        return {
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'total_time': self.total_time,
            'embed_count': self.embed_count,
            'avg_time_per_embed': self.total_time / max(self.embed_count, 1),
            'cache_size': len(self._cache_dict) if self.cache else 0
        }

    def _check_cache(self, text: str) -> Optional[List[float]]:
        """Check cache for existing embedding."""
        if self.cache and text in self._cache_dict:
            return self._cache_dict[text]
        return None

    def _update_cache(self, text: str, embedding: List[float]):
        """Update cache with new embedding."""
        if self.cache:
            self._cache_dict[text] = embedding


class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI embeddings via API.

    Fast, high-quality embeddings with per-token cost. Best for most use cases
    with moderate query volume. Supports batching for efficiency.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: Optional[int] = None,
        cache: bool = False
    ):
        """
        Initialize OpenAI embedder.

        Args:
            model: OpenAI model name (text-embedding-3-small or -large)
            dimensions: Optional dimension reduction (Matryoshka embeddings)
            cache: Whether to cache embeddings
        """
        super().__init__(cache)

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required. Install: pip install openai")

        self.client = OpenAI()
        self.model = model
        self.dimensions = dimensions

        # Pricing per 1k tokens (as of 2024)
        self.price_per_1k = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
        }.get(model, 0.00002)

        logger.info(f"Initialized OpenAI embedder: {model}")
        if dimensions:
            logger.info(f"  Using Matryoshka dimension reduction: {dimensions}")

    def embed(self, text: str) -> List[float]:
        """Embed single text using OpenAI API."""
        # Check cache
        cached = self._check_cache(text)
        if cached is not None:
            return cached

        start_time = time.time()

        # Call API
        kwargs = {"input": text, "model": self.model}
        if self.dimensions:
            kwargs["dimensions"] = self.dimensions

        response = self.client.embeddings.create(**kwargs)
        embedding = response.data[0].embedding

        # Track metrics
        elapsed = time.time() - start_time
        tokens = response.usage.total_tokens
        cost = (tokens / 1000) * self.price_per_1k

        self.total_tokens += tokens
        self.total_cost += cost
        self.total_time += elapsed
        self.embed_count += 1

        # Update cache
        self._update_cache(text, embedding)

        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in single API call (much faster).

        OpenAI supports batch embedding up to ~8k tokens total.
        This is 20-50x faster than individual embeds.
        """
        if not texts:
            return []

        # Filter out cached texts
        uncached_texts = []
        uncached_indices = []
        result = [None] * len(texts)

        for i, text in enumerate(texts):
            cached = self._check_cache(text)
            if cached is not None:
                result[i] = cached
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        if not uncached_texts:
            logger.info(f"All {len(texts)} embeddings retrieved from cache")
            return result

        logger.info(f"Embedding {len(uncached_texts)} texts (batch)")
        start_time = time.time()

        # Batch API call
        kwargs = {"input": uncached_texts, "model": self.model}
        if self.dimensions:
            kwargs["dimensions"] = self.dimensions

        response = self.client.embeddings.create(**kwargs)

        # Extract embeddings
        embeddings = [item.embedding for item in response.data]

        # Track metrics
        elapsed = time.time() - start_time
        tokens = response.usage.total_tokens
        cost = (tokens / 1000) * self.price_per_1k

        self.total_tokens += tokens
        self.total_cost += cost
        self.total_time += elapsed
        self.embed_count += len(uncached_texts)

        # Update cache and result
        for i, embedding in zip(uncached_indices, embeddings):
            result[i] = embedding
            self._update_cache(texts[i], embedding)

        logger.info(f"  Completed in {elapsed:.2f}s, cost: ${cost:.6f}")

        return result


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Self-hosted embeddings via sentence-transformers.

    Free, runs locally. Good quality with models like gte-large.
    Best for high query volume or privacy requirements.
    """

    def __init__(
        self,
        model_name: str = "thenlper/gte-large",
        cache: bool = False,
        device: str = "cpu"
    ):
        """
        Initialize sentence-transformers embedder.

        Args:
            model_name: HuggingFace model name
            cache: Whether to cache embeddings
            device: 'cpu' or 'cuda' for GPU acceleration
        """
        super().__init__(cache)

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers required. Install: pip install sentence-transformers"
            )

        logger.info(f"Loading sentence-transformers model: {model_name}")
        logger.info("  (First load downloads ~1GB model, may take 1-2 minutes)")

        start = time.time()
        self.model = SentenceTransformer(model_name, device=device)
        load_time = time.time() - start

        logger.info(f"  Model loaded in {load_time:.1f}s")
        logger.info(f"  Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

        self.model_name = model_name
        self.device = device

    def embed(self, text: str) -> List[float]:
        """Embed single text using local model."""
        # Check cache
        cached = self._check_cache(text)
        if cached is not None:
            return cached

        start_time = time.time()

        # Encode
        embedding = self.model.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()

        # Track metrics (no cost, just time)
        elapsed = time.time() - start_time
        self.total_time += elapsed
        self.embed_count += 1

        # Update cache
        self._update_cache(text, embedding_list)

        return embedding_list

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch (faster than individual).

        sentence-transformers batches internally for efficiency.
        """
        if not texts:
            return []

        # Filter out cached texts
        uncached_texts = []
        uncached_indices = []
        result = [None] * len(texts)

        for i, text in enumerate(texts):
            cached = self._check_cache(text)
            if cached is not None:
                result[i] = cached
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        if not uncached_texts:
            logger.info(f"All {len(texts)} embeddings retrieved from cache")
            return result

        logger.info(f"Embedding {len(uncached_texts)} texts (batch, local)")
        start_time = time.time()

        # Batch encode
        embeddings = self.model.encode(
            uncached_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        embeddings_list = embeddings.tolist()

        # Track metrics
        elapsed = time.time() - start_time
        self.total_time += elapsed
        self.embed_count += len(uncached_texts)

        # Update cache and result
        for i, embedding in zip(uncached_indices, embeddings_list):
            result[i] = embedding
            self._update_cache(texts[i], embedding)

        logger.info(f"  Completed in {elapsed:.2f}s (free, local)")

        return result


def compare_embedders(
    text: str,
    embedders: List[BaseEmbedder]
) -> Dict[str, Any]:
    """
    Compare multiple embedders on same text.

    Useful for evaluating speed, cost, and embedding quality differences.

    Args:
        text: Sample text to embed
        embedders: List of embedder instances to compare

    Returns:
        Comparison results with embeddings and stats
    """
    results = {}

    for embedder in embedders:
        embedder_name = embedder.__class__.__name__
        logger.info(f"\nTesting {embedder_name}...")

        # Reset stats
        embedder.total_time = 0.0
        embedder.total_cost = 0.0
        embedder.embed_count = 0

        # Embed
        embedding = embedder.embed(text)
        stats = embedder.get_stats()

        results[embedder_name] = {
            'embedding_dim': len(embedding),
            'embedding_sample': embedding[:5],  # First 5 values
            'time': stats['total_time'],
            'cost': stats['total_cost'],
        }

        logger.info(f"  Dimension: {len(embedding)}")
        logger.info(f"  Time: {stats['total_time']:.4f}s")
        logger.info(f"  Cost: ${stats['total_cost']:.6f}")

    return results


if __name__ == "__main__":
    """
    Example usage: Compare OpenAI and sentence-transformers embedders.

    Demonstrates API-based vs self-hosted tradeoffs: speed, cost, quality.
    """

    sample_text = "VIP customers receive a 60-day return window instead of the standard 30 days."

    logger.info("=" * 80)
    logger.info("EMBEDDER COMPARISON")
    logger.info("=" * 80)
    logger.info(f"\nSample text: {sample_text}\n")

    # Initialize embedders
    embedders = [
        OpenAIEmbedder(model="text-embedding-3-small", cache=True),
        SentenceTransformerEmbedder(model_name="thenlper/gte-large", cache=True),
    ]

    # Compare
    results = compare_embedders(sample_text, embedders)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    for name, stats in results.items():
        logger.info(f"\n{name}:")
        logger.info(f"  Dimensions: {stats['embedding_dim']}")
        logger.info(f"  Latency: {stats['time']:.4f}s")
        logger.info(f"  Cost: ${stats['cost']:.6f}")

    logger.info("\nBoth embedders provide similar quality for retrieval tasks.")
    logger.info("OpenAI: Faster API, small cost. Good for moderate volume.")
    logger.info("Sentence-transformers: Free, local. Good for high volume or privacy.")
