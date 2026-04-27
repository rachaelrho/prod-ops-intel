# Evaluation Test Cases

Ground truth test cases for measuring retrieval and decision quality.

## Structure

### Tier 1: Hand-Written Cases (40 cases)
`tier1_test_cases.json` - Manually authored test cases grounded in actual database records and policy documents.

**Categories:**
- **Database Lookups** (10 cases): Query structured data (inventory levels, customer history, order status)
- **Policy/SOP** (10 cases): Retrieve and apply internal policies, escalation thresholds, procedures
- **Product Knowledge** (10 cases): Ingredient compatibility, usage guidance, safety information
- **Multi-Source** (10 cases): Require synthesis across database + documents for decision-making

**Difficulty Levels:**
- **Easy**: Single-source lookup with straightforward answer
- **Medium**: Requires aggregation, filtering, or policy interpretation
- **Hard**: Multi-hop reasoning, exception handling, cross-document synthesis

### Test Case Format

```json
{
  "id": "unique_identifier",
  "category": "database_lookup|policy_sop|product_knowledge|multi_source",
  "difficulty": "easy|medium|hard",
  "query": "The actual operational question",
  "expected_sources": ["which tables/documents should be retrieved"],
  "expected_data": {"key data points that inform the decision"},
  "expected_decision": "The actionable recommendation with reasoning",
  "reasoning": "Why this is the correct decision"
}
```

## Usage

These cases serve as:
1. **Ground truth** for evaluation metrics (RAGAS context recall/precision)
2. **Decision quality validation** (DeepEval policy compliance, factual accuracy)
3. **Architecture comparison** (measure retrieval quality across embedding models, chunking strategies)
4. **Regression testing** (ensure changes don't degrade performance)

## Planned Tiers

- **Tier 2** (100-150 cases): LLM-generated, human-reviewed synthetic cases
- **Tier 3** (20-30 cases): Complex chained reasoning scenarios

## Metrics

Each test case will be evaluated on:
- **Retrieval Quality**: Did the system retrieve the correct sources? (precision@k, recall@k)
- **Decision Quality**: Is the recommendation correct and complete? (LLM-as-judge with rubric)
- **Policy Compliance**: Does the decision follow documented policies?
- **Factual Accuracy**: Are data points correctly retrieved and applied?
