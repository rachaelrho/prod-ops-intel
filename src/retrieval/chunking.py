"""
Document chunking strategies for retrieval.

Recursive chunking used for structured policy documents. Preserves paragraph
boundaries and maintains rule-exception relationships. Fixed-size and semantic
strategies available for comparison.
"""

import re
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
import tiktoken

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DocumentChunker:
    """Handles multiple chunking strategies for comparison."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize chunker with token counter.

        Args:
            model_name: Model name for tiktoken encoding (for token counting)
        """
        self.encoding = tiktoken.encoding_for_model(model_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def fixed_size_chunking(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split text into fixed-size chunks with overlap.

        Simple and predictable, but may break mid-sentence or mid-clause.
        Good baseline for comparison.

        Args:
            text: Document text to chunk
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens

        Returns:
            List of dicts with chunk text, metadata
        """
        splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n\n"  # Try to break on paragraphs when possible
        )

        chunks = splitter.split_text(text)

        return [
            {
                "text": chunk,
                "token_count": self.count_tokens(chunk),
                "strategy": "fixed_size",
                "chunk_index": idx,
                "metadata": {
                    "chunk_size": chunk_size,
                    "overlap": chunk_overlap
                }
            }
            for idx, chunk in enumerate(chunks)
        ]

    def recursive_chunking(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split text recursively by document structure.

        Tries to split on natural boundaries in this order:
        1. Double newlines (paragraphs)
        2. Single newlines (lines)
        3. Sentences (periods)
        4. Words (spaces)

        Better at preserving logical units (like policy clauses with exceptions).

        Args:
            text: Document text to chunk
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens

        Returns:
            List of dicts with chunk text, metadata
        """
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",  # Paragraphs
                "\n",    # Lines
                ". ",    # Sentences
                " ",     # Words
                ""       # Characters (fallback)
            ]
        )

        chunks = splitter.split_text(text)

        return [
            {
                "text": chunk,
                "token_count": self.count_tokens(chunk),
                "strategy": "recursive",
                "chunk_index": idx,
                "metadata": {
                    "chunk_size": chunk_size,
                    "overlap": chunk_overlap
                }
            }
            for idx, chunk in enumerate(chunks)
        ]

    def semantic_chunking(
        self,
        text: str,
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: float = 95
    ) -> List[Dict[str, Any]]:
        """
        Split text based on semantic similarity between sentences.

        Uses embeddings to detect when meaning/topic shifts. Keeps related
        sentences together even if they exceed target chunk size.

        Best for policy documents where rules and exceptions must stay together.
        More expensive (requires embedding each sentence).

        Args:
            text: Document text to chunk
            breakpoint_threshold_type: "percentile" or "standard_deviation"
            breakpoint_threshold_amount: How much similarity drop triggers split

        Returns:
            List of dicts with chunk text, metadata
        """
        # Initialize semantic chunker with OpenAI embeddings
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_amount=breakpoint_threshold_amount
        )

        chunks = splitter.split_text(text)

        return [
            {
                "text": chunk,
                "token_count": self.count_tokens(chunk),
                "strategy": "semantic",
                "chunk_index": idx,
                "metadata": {
                    "breakpoint_type": breakpoint_threshold_type,
                    "breakpoint_amount": breakpoint_threshold_amount
                }
            }
            for idx, chunk in enumerate(chunks)
        ]

    def chunk_document(
        self,
        text: str,
        strategy: str = "recursive",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Chunk document using specified strategy.

        Args:
            text: Document text to chunk
            strategy: "fixed_size", "recursive", or "semantic"
            **kwargs: Strategy-specific parameters

        Returns:
            List of chunk dicts
        """
        if strategy == "fixed_size":
            return self.fixed_size_chunking(text, **kwargs)
        elif strategy == "recursive":
            return self.recursive_chunking(text, **kwargs)
        elif strategy == "semantic":
            return self.semantic_chunking(text, **kwargs)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

    def compare_strategies(
        self,
        text: str,
        strategies: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run multiple chunking strategies on same text for comparison.

        Args:
            text: Document text to chunk
            strategies: List of strategies to compare (default: all)

        Returns:
            Dict mapping strategy name to list of chunks
        """
        if strategies is None:
            strategies = ["fixed_size", "recursive", "semantic"]

        results = {}
        for strategy in strategies:
            results[strategy] = self.chunk_document(text, strategy=strategy)

        return results

    def print_comparison(self, results: Dict[str, List[Dict[str, Any]]]):
        """
        Log comparison of chunking strategies.

        Shows chunk count, avg/min/max token counts, and first chunk preview.
        """
        logger.info("=" * 80)
        logger.info("CHUNKING STRATEGY COMPARISON")
        logger.info("=" * 80)

        for strategy, chunks in results.items():
            token_counts = [c["token_count"] for c in chunks]

            logger.info(f"\n{strategy.upper()}:")
            logger.info(f"  Total chunks: {len(chunks)}")
            logger.info(f"  Avg tokens/chunk: {sum(token_counts) / len(token_counts):.1f}")
            logger.info(f"  Min/Max tokens: {min(token_counts)} / {max(token_counts)}")
            logger.info(f"  First chunk preview:")
            logger.info(f"  {chunks[0]['text'][:200]}...")
            logger.info("-" * 80)


def load_document(file_path: str) -> str:
    """Load document text from markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"Document not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading document: {e}")
        raise

    # Remove markdown header (lines starting with #, *, etc. at top)
    # Keep main content only
    lines = content.split('\n')
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('#') and not line.startswith('*'):
            content_start = i
            break

    return '\n'.join(lines[content_start:])


if __name__ == "__main__":
    """
    Example usage: Compare chunking strategies on return policy document.

    Recursive chunking (500 tokens, 50 overlap) is best practice for structured
    policy documents. Maintains section coherence while enabling precise retrieval.
    """
    from pathlib import Path

    # Load return policy document
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    policy_path = docs_dir / "return_refund_policy.md"

    logger.info(f"Loading document: {policy_path}")
    text = load_document(policy_path)
    logger.info(f"Document length: {len(text)} characters")

    # Initialize chunker
    chunker = DocumentChunker()

    # Compare all strategies for demonstration
    # In production, would use recursive directly without comparison
    logger.info("Running chunking strategies...")
    results = chunker.compare_strategies(text)

    # Print comparison
    chunker.print_comparison(results)

    # Show example of rule-exception preservation
    logger.info("=" * 80)
    logger.info("RULE-EXCEPTION PRESERVATION TEST")
    logger.info("=" * 80)
    logger.info("Searching for 'VIP' mentions across strategies...")
    logger.info("(VIP policies are exceptions to standard rules)")

    for strategy, chunks in results.items():
        vip_chunks = [c for c in chunks if "VIP" in c["text"] or "vip" in c["text"]]
        logger.info(f"\n{strategy}: Found {len(vip_chunks)} chunks mentioning VIP")
        if vip_chunks:
            logger.info(f"  Example chunk ({vip_chunks[0]['token_count']} tokens):")
            logger.info(f"  {vip_chunks[0]['text'][:300]}...")
