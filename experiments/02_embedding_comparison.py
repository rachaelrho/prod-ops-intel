"""
Experiment 2: Embedding Model Comparison

Goal: Determine the best embedding model for operational policy documents

Setup:
- Documents: Policy documents from docs/ directory
- Chunking strategy: RECURSIVE (best from Experiment 1)
- Embedding models: OpenAI text-embedding-3-small vs SentenceTransformer gte-large
- Evaluation: Test cases from eval/tier1_test_cases.json (document retrieval categories)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import time

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.retrieval.chunking import DocumentChunker
from src.retrieval.embeddings import OpenAIEmbedder, SentenceTransformerEmbedder

import faiss

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

logger.info("="*80)
logger.info("EXPERIMENT 2: EMBEDDING MODEL COMPARISON")
logger.info("="*80)

# Configuration
DOCS_DIR = Path(__file__).parent.parent / 'docs'
EVAL_DIR = Path(__file__).parent.parent / 'eval'
RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

CHUNK_STRATEGY = 'recursive'  # Best from Experiment 1
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# ============================================================================
# 1. Load Policy Documents
# ============================================================================
logger.info("\n[1/9] Loading policy documents...")

doc_files = [
    'return_refund_policy.md',
    'damaged_shipment_sop.md',
    'shipping_policy.md',
    'product_faq.md'
]

documents = {}
for doc_file in doc_files:
    doc_path = DOCS_DIR / doc_file
    with open(doc_path, 'r') as f:
        documents[doc_file] = f.read()

logger.info(f"✓ Loaded {len(documents)} documents")

# ============================================================================
# 2. Chunk Documents (Using Best Strategy from Exp 1)
# ============================================================================
logger.info(f"\n[2/9] Chunking documents with {CHUNK_STRATEGY} strategy...")

chunker = DocumentChunker()

chunks = []
for doc_name, doc_content in documents.items():
    doc_chunks = chunker.chunk_document(
        doc_content,
        strategy=CHUNK_STRATEGY,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Add source metadata
    for chunk_dict in doc_chunks:
        chunk_dict['source'] = doc_name
        chunks.append(chunk_dict)

    logger.info(f"  {doc_name}: {len(doc_chunks)} chunks")

logger.info(f"✓ Total chunks: {len(chunks)}")
avg_tokens = np.mean([c['token_count'] for c in chunks])
logger.info(f"  Avg tokens/chunk: {avg_tokens:.1f}")

# Get chunk texts
chunk_texts = [c['text'] for c in chunks]

# ============================================================================
# 3. Initialize Embedding Models
# ============================================================================
logger.info("\n[3/9] Initializing embedding models...")

embedders = {
    'openai_small': OpenAIEmbedder(
        model="text-embedding-3-small",
        cache=True
    ),
    'gte_large': SentenceTransformerEmbedder(
        model_name="thenlper/gte-large",
        cache=True
    )
}

logger.info("✓ Initialized 2 embedding models:")
logger.info("  - openai_small: text-embedding-3-small (API-based)")
logger.info("  - gte_large: thenlper/gte-large (self-hosted)")

# ============================================================================
# 4. Embed Chunks and Build FAISS Indexes
# ============================================================================
logger.info("\n[4/9] Embedding chunks and building FAISS indexes...")

indexes = {}

for model_name, embedder in embedders.items():
    logger.info(f"\n  Processing: {model_name}")

    # Track embedding time
    start_time = time.time()

    # Embed in batch
    logger.info(f"    Embedding {len(chunk_texts)} chunks...")
    embeddings = embedder.embed_batch(chunk_texts)
    embeddings_array = np.array(embeddings).astype('float32')

    embed_time = time.time() - start_time

    # Build FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)

    # Store stats
    stats = embedder.get_stats()

    indexes[model_name] = {
        'index': index,
        'chunks': chunks,
        'embeddings': embeddings_array,
        'dimension': dimension,
        'embed_time': embed_time,
        'stats': stats
    }

    logger.info(f"    ✓ Indexed {len(chunks)} chunks (dimension={dimension})")
    logger.info(f"    ✓ Embedding time: {embed_time:.2f}s")
    if 'total_cost' in stats and stats['total_cost'] > 0:
        logger.info(f"    ✓ Cost: ${stats['total_cost']:.4f}")

# ============================================================================
# 5. Load Evaluation Test Cases
# ============================================================================
logger.info("\n[5/9] Loading evaluation test cases...")

with open(EVAL_DIR / 'tier1_test_cases.json', 'r') as f:
    test_cases = json.load(f)

# Filter to document retrieval categories
doc_test_cases = [
    tc for tc in test_cases
    if tc['category'] in ['policy_sop', 'product_knowledge', 'multi_source']
]

logger.info(f"✓ Document retrieval test cases: {len(doc_test_cases)}")

# ============================================================================
# 6. Define Retrieval Function
# ============================================================================

def retrieve(query: str, embedder, index_info: Dict, k: int = 3) -> tuple:
    """Retrieve top-k chunks for a query and measure latency"""
    start_time = time.time()

    # Embed query
    query_embedding = embedder.embed(query)
    query_vector = np.array([query_embedding]).astype('float32')

    # Search
    distances, indices = index_info['index'].search(query_vector, k)

    latency = time.time() - start_time

    # Return results
    results = []
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        chunk_info = index_info['chunks'][idx]
        results.append({
            'rank': i + 1,
            'distance': float(dist),
            'source': chunk_info['source'],
            'text_preview': chunk_info['text'][:200] + '...' if len(chunk_info['text']) > 200 else chunk_info['text'],
            'full_text': chunk_info['text'],
            'token_count': chunk_info['token_count']
        })

    return results, latency

# ============================================================================
# 7. Run Retrieval Evaluation
# ============================================================================
logger.info("\n[6/9] Running retrieval evaluation...")

results = []
latencies = {model: [] for model in embedders.keys()}

for i, test_case in enumerate(doc_test_cases, 1):
    if i % 5 == 0 or i == 1:
        logger.info(f"  [{i}/{len(doc_test_cases)}] Processing...")

    for model_name, embedder in embedders.items():
        index_info = indexes[model_name]
        retrieved, latency = retrieve(test_case['query'], embedder, index_info, k=3)
        latencies[model_name].append(latency)

        # Check if expected sources were retrieved
        retrieved_sources = [r['source'] for r in retrieved]
        expected_sources = test_case.get('expected_sources', [])

        sources_match = any(
            any(exp_src in ret_src or ret_src in exp_src
                for exp_src in expected_sources)
            for ret_src in retrieved_sources
        ) if expected_sources else False

        results.append({
            'test_id': test_case['id'],
            'category': test_case['category'],
            'difficulty': test_case['difficulty'],
            'model': model_name,
            'query': test_case['query'],
            'expected_sources': expected_sources,
            'retrieved_sources': retrieved_sources,
            'sources_match': sources_match,
            'top_distance': retrieved[0]['distance'] if retrieved else None,
            'latency_ms': latency * 1000,
            'retrieved': retrieved
        })

logger.info(f"  ✓ Completed {len(results)} retrievals ({len(doc_test_cases)} queries × {len(embedders)} models)")

# Print cost summary
for model_name, embedder in embedders.items():
    stats = embedder.get_stats()
    if stats['total_cost'] > 0:
        logger.info(f"  {model_name}: ${stats['total_cost']:.4f}")

# ============================================================================
# 8. Analyze Results
# ============================================================================
logger.info("\n[7/9] Analyzing results...")
logger.info("="*80)

# Convert to DataFrame
df = pd.DataFrame([{
    'test_id': r['test_id'],
    'category': r['category'],
    'difficulty': r['difficulty'],
    'model': r['model'],
    'sources_match': r['sources_match'],
    'top_distance': r['top_distance'],
    'latency_ms': r['latency_ms']
} for r in results])

logger.info("\nOVERALL ACCURACY (retrieved expected source in top-3):")
logger.info("="*80)
accuracy_by_model = df.groupby('model')['sources_match'].mean().sort_values(ascending=False)
for model, acc in accuracy_by_model.items():
    logger.info(f"  {model:15s}: {acc*100:5.1f}%")

logger.info("\n\nACCURACY BY CATEGORY:")
logger.info("="*80)
accuracy_by_category = df.pivot_table(
    index='model',
    columns='category',
    values='sources_match',
    aggfunc='mean'
) * 100
logger.info(accuracy_by_category.round(1).to_string())

logger.info("\n\nACCURACY BY DIFFICULTY:")
logger.info("="*80)
accuracy_by_difficulty = df.pivot_table(
    index='model',
    columns='difficulty',
    values='sources_match',
    aggfunc='mean'
) * 100
logger.info(accuracy_by_difficulty.round(1).to_string())

logger.info("\n\nAVERAGE RETRIEVAL DISTANCE (lower is better):")
logger.info("="*80)
avg_distance = df.groupby('model')['top_distance'].mean().sort_values()
for model, dist in avg_distance.items():
    logger.info(f"  {model:15s}: {dist:.4f}")

logger.info("\n\nAVERAGE QUERY LATENCY:")
logger.info("="*80)
avg_latency = df.groupby('model')['latency_ms'].mean().sort_values()
for model, lat in avg_latency.items():
    logger.info(f"  {model:15s}: {lat:6.1f} ms")

logger.info("\n\nEMBEDDING TIME (batch embedding all chunks):")
logger.info("="*80)
for model_name, index_info in indexes.items():
    logger.info(f"  {model_name:15s}: {index_info['embed_time']:6.2f} s")

logger.info("\n\nCOST:")
logger.info("="*80)
for model_name, embedder in embedders.items():
    stats = embedder.get_stats()
    cost = stats.get('total_cost', 0)
    if cost > 0:
        logger.info(f"  {model_name:15s}: ${cost:.4f}")
    else:
        logger.info(f"  {model_name:15s}: FREE (self-hosted)")

# ============================================================================
# 9. Findings and Recommendation
# ============================================================================
logger.info("\n\n[8/9] Generating findings...")
logger.info("="*80)
logger.info("FINDINGS")
logger.info("="*80)

winner = accuracy_by_model.idxmax()
winner_accuracy = accuracy_by_model.max()

logger.info(f"\n✓ BEST EMBEDDING MODEL (by accuracy): {winner.upper()}")
logger.info(f"  - Accuracy: {winner_accuracy*100:.1f}%")
logger.info(f"  - Avg retrieval distance: {avg_distance[winner]:.4f}")
logger.info(f"  - Avg query latency: {avg_latency[winner]:.1f} ms")

# Cost comparison
openai_stats = embedders['openai_small'].get_stats()
gte_stats = embedders['gte_large'].get_stats()

logger.info(f"\n\nTRADEOFFS:")
logger.info(f"  OpenAI (text-embedding-3-small):")
logger.info(f"    + Accuracy: {accuracy_by_model['openai_small']*100:.1f}%")
logger.info(f"    + Query latency: {avg_latency['openai_small']:.1f} ms")
logger.info(f"    - Cost: ${openai_stats['total_cost']:.4f} for this experiment")
logger.info(f"    - Requires API key and internet connection")

logger.info(f"\n  GTE-Large (self-hosted):")
logger.info(f"    + Accuracy: {accuracy_by_model['gte_large']*100:.1f}%")
logger.info(f"    + Cost: FREE (self-hosted)")
logger.info(f"    + Privacy: no data sent to external APIs")
logger.info(f"    - Query latency: {avg_latency['gte_large']:.1f} ms")
logger.info(f"    - Initial model download required")

accuracy_diff = (accuracy_by_model['openai_small'] - accuracy_by_model['gte_large']) * 100
latency_diff = avg_latency['gte_large'] - avg_latency['openai_small']

logger.info(f"\n\nKEY OBSERVATIONS:")
logger.info(f"  1. Accuracy difference: {accuracy_diff:+.1f} percentage points (OpenAI vs GTE)")
logger.info(f"  2. Latency difference: {latency_diff:+.1f} ms (GTE slower)")
logger.info(f"  3. Cost difference: ${openai_stats['total_cost']:.4f} vs FREE")

# Make recommendation
logger.info(f"\n\nRECOMMENDATION:")
if abs(accuracy_diff) < 5:  # Within 5 percentage points
    logger.info(f"  → Use GTE-LARGE (self-hosted)")
    logger.info(f"     Accuracy is comparable ({abs(accuracy_diff):.1f}pp difference)")
    logger.info(f"     Zero cost and privacy benefits outweigh small latency difference")
else:
    if accuracy_by_model['openai_small'] > accuracy_by_model['gte_large']:
        logger.info(f"  → Use OPENAI TEXT-EMBEDDING-3-SMALL")
        logger.info(f"     {accuracy_diff:.1f}pp accuracy advantage worth the cost")
    else:
        logger.info(f"  → Use GTE-LARGE (self-hosted)")
        logger.info(f"     Better accuracy AND zero cost")

# ============================================================================
# 10. Save Results
# ============================================================================
logger.info("\n\n[9/9] Saving results...")

results_file = RESULTS_DIR / 'embedding_comparison_results.json'
with open(results_file, 'w') as f:
    json.dump({
        'experiment': 'embedding_comparison',
        'chunking_strategy': CHUNK_STRATEGY,
        'models': list(embedders.keys()),
        'winner': winner,
        'accuracy_by_model': {k: float(v) for k, v in accuracy_by_model.items()},
        'accuracy_by_category': accuracy_by_category.to_dict(),
        'accuracy_by_difficulty': accuracy_by_difficulty.to_dict(),
        'avg_distance': {k: float(v) for k, v in avg_distance.items()},
        'avg_latency_ms': {k: float(v) for k, v in avg_latency.items()},
        'costs': {
            'openai_small': openai_stats['total_cost'],
            'gte_large': 0.0
        },
        'detailed_results': results
    }, f, indent=2)

logger.info(f"✓ Results saved to {results_file}")

logger.info("\n" + "="*80)
logger.info("EXPERIMENT 2 COMPLETE")
logger.info("="*80)
logger.info(f"\nBest configuration: {CHUNK_STRATEGY} chunking + {winner} embeddings")
