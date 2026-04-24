# Operational Intelligence System

AI-powered decision support for e-commerce operations, built to handle real-world data quality issues and policy complexity.

## What This Does

This system automates operational decision-making by combining structured transaction data with unstructured policy documents. Built using a DTC skincare brand as the example domain, the architecture generalizes to any operational context with transactional data and internal policies (SaaS support ops, logistics, compliance, customer success).

Example queries handled:

- "Customer wants to return opened product after 25 days - approve or deny?"
- "Do we need to restock Vitamin C serum based on current sales velocity?"
- "How do we process this damaged shipment claim given the customer's order history?"

The system retrieves relevant context from multiple sources, applies policy logic, and produces actionable recommendations with reasoning.

## Why This Approach

Traditional business intelligence tools (Metabase, Mode) query structured data but can't interpret policies or handle operational edge cases. This system bridges that gap by:

1. **Handling messy data** - Built against realistic data quality issues (duplicates, missing values, format inconsistencies) with documented cleaning strategies
2. **Policy-aware decisions** - Retrieves and applies internal policies with escalation thresholds, exception handling, and cross-document reasoning
3. **Validated reliability** - Comprehensive evaluation framework measuring both retrieval accuracy and decision quality against ground truth

## Technical Architecture

### Data Layer
- **ETL pipeline** with configurable data quality handling
- **SQLite** for structured transaction data (products, orders, customers)
- **Feature engineering** for temporal patterns, customer segmentation, inventory status

### Retrieval System
- **Hybrid search** combining dense embeddings (semantic similarity) and sparse retrieval (keyword matching)
- **Multiple chunking strategies** optimized for different document types (policies vs SOPs vs product specs)
- **Embedding comparison** across API-based and self-hosted models with documented tradeoffs

### Decision Engine
- **Multi-source synthesis** combining database queries with document retrieval
- **Policy-compliant recommendations** with escalation routing and approval logic
- **Reasoning transparency** showing which documents and data points informed each decision

### Evaluation Framework
- **Retrieval metrics** (RAGAS: context relevance, faithfulness, precision/recall)
- **Decision quality metrics** (DeepEval: policy compliance, factual accuracy, completeness)
- **Human calibration** validating LLM-as-judge reliability with Cohen's kappa analysis

## Project Structure

```
prod-ops-intel/
├── data/                    # Generated databases (gitignored)
├── docs/                    # Operational policy documents
│   ├── return_refund_policy.md
│   ├── damaged_shipment_sop.md
│   ├── shipping_policy.md
│   └── product_faq.md
├── eval/                    # Evaluation test cases with ground truth
├── scripts/                 # Data generation and ETL
│   ├── config.py           # Centralized configuration
│   ├── generate_raw_data.py
│   └── clean_and_prep.py
├── src/                     # Core application code
│   └── retrieval/          # Retrieval infrastructure
└── notebooks/              # Architecture analysis and experiments
```

## Setup

### Prerequisites
- Python 3.10+
- OpenAI API key (for embeddings and LLM)

### Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your OpenAI API key

# Generate data
python scripts/generate_raw_data.py
python scripts/clean_and_prep.py
```

## Data Engineering

### Realistic Data Quality Simulation
The raw data generation simulates actual operational data issues:
- 3-5% duplicate order records (from payment retries)
- Mixed date formats across systems
- Missing values from guest checkouts
- Inconsistent state/email formatting
- Null order statuses from data collection gaps

### ETL Pipeline
Documented cleaning strategies for each issue type:
- Deduplication with configurable keep logic
- Date standardization across multiple formats
- State normalization to standard abbreviations
- Missing value imputation with business rules
- Feature engineering (customer tenure, return patterns, seasonality)

### Configuration-Driven Architecture
All mappings, thresholds, and parameters centralized in `scripts/config.py`:
- Eliminates hardcoded values and if/elif chains
- Single source of truth for data quality parameters
- Easy modification without touching pipeline logic

## Operational Documentation

Four policy documents totaling ~35KB, modeled on real DTC operations:

- **Return & Refund Policy** - Escalation thresholds ($50/$200), VIP customer rules, adverse reaction handling
- **Damaged Shipment SOP** - Decision tree with damage assessment categories, inventory checks, carrier claim filing
- **Shipping Policy** - Domestic/international procedures, timeline commitments, cost management
- **Product FAQ** - Ingredient compatibility matrix, usage guidance, pregnancy-safe alternatives

These documents include realistic operational complexity:
- Policy exceptions and special cases
- Cross-document dependencies (return policy references shipping procedures)
- Escalation criteria based on order value and customer history
- Approval authority matrices
- Multi-hop information retrieval requirements

## Status

**Completed:**
- ✓ Data generation with configurable quality issues
- ✓ ETL pipeline with documented cleaning strategies
- ✓ Operational policy documentation (4 documents, 35KB)
- ✓ Retrieval infrastructure setup

**In Progress:**
- Embedding model comparison and chunking optimization
- Evaluation framework implementation
- End-to-end pipeline integration

## Why This Matters

This project demonstrates the data and retrieval engineering skills that make operational AI systems reliable in production:

1. **Real-world data handling** - Not clean academic datasets, but messy operational data with documented cleaning
2. **Policy complexity** - Multi-document reasoning with exceptions, escalations, and cross-references
3. **Validated quality** - Comprehensive evaluation measuring both retrieval and decision accuracy
4. **Production thinking** - Configuration-driven, testable, with clear tradeoff documentation

Startups building internal operations tools need this foundation before deploying agent systems that make real business decisions.
