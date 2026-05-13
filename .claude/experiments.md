# Experimentation Protocol for Retrieval System

This document outlines our approach to running, interpreting, and iterating on retrieval experiments. It captures lessons learned from previous experiment cycles to prevent common diagnostic mistakes.

## Red Flags to Investigate

**Stop and investigate if you see:**
- Strategies show 0 disagreements across all test cases
- Scores are suspiciously identical (e.g., 91.2% = 91.2%)
- All scores are very high (>90%) across all strategies
- All scores are very low (<40%) across all strategies

These patterns suggest problems with test case quality or corpus adequacy, not legitimate findings.

## Analysis Steps

Run this analysis before making changes to documents or test cases.

### Check Results

**Disagreement rate:** Should see some disagreements between strategies
- 0 disagreements + identical scores: Test cases likely too easy
- Some disagreements (even 5-10%): Indicates test cases are working
- Note: Good strategies may differ by only 2-5 percentage points

**Score distribution:**
- Identical scores (91.2% = 91.2%): Red flag, test cases don't differentiate
- Small spread (2-5pp): Normal for good strategies
- Large spread (>20pp): Investigate if one strategy is broken

**Absolute accuracy:**
- Over 95% all strategies: Test cases likely too easy
- Under 40% all strategies: Corpus too small or test cases broken
- Wide range acceptable depending on task difficulty

### Review Failures

Export failed cases and check:
- Is the answer in the corpus?
- Does the failure make sense given chunking strategy?
- Do failures cluster by category or document type?

### Audit Test Case Quality

```bash
# Distribution check
grep -c '"difficulty": "easy"' eval/tier1_test_cases.json
grep -c '"difficulty": "medium"' eval/tier1_test_cases.json
grep -c '"difficulty": "hard"' eval/tier1_test_cases.json
```

**Target distribution:**
- Under 30% simple lookups ("What is X?")
- Over 30% synthesis questions (combine multiple sections)
- Over 20% edge cases (policy intersections)

### Check Corpus

**Document count:** 4-8 docs for initial experiments, <4 likely too small

**Section length:** 400-800 tokens forces interesting chunking decisions

**Format:** Should use bullets, tables, short paragraphs (not wall-of-text prose)

## Diagnostic Decision Tree

### Scenario A: No differentiation + High accuracy
Identical scores, 0 disagreements, all strategies >90%

**Diagnosis**: Test cases too easy

**Action**: Keep documents as-is, create challenging test cases requiring multi-section synthesis or edge cases

### Scenario B: No differentiation + Low accuracy
Identical scores, 0 disagreements, all strategies <50%

**Diagnosis**: Corpus too small or test cases broken

**Action**: Check if answers exist in corpus. Add documents if missing, investigate retrieval if present.

### Scenario C: Some differentiation + Poor results
Strategies differ slightly, but accuracy disappointing

**Diagnosis**: Depends on failure analysis

**Action**: Review failed cases. If failures make sense (hard questions), accept results. If failures seem retrievable, improve corpus.

### Scenario D: Some differentiation + Good results
Strategies differ (even by 2-5pp), results reasonable for task

**Diagnosis**: Success

**Action**: Document findings, analyze patterns, make recommendations

## Iteration Protocol

Make one change at a time to isolate effects.

### Standard Cycle

1. Hypothesize the problem with evidence
2. Predict expected outcome if hypothesis is correct
3. Change one thing (documents or test cases, not both)
4. Re-run experiments
5. Analyze results against prediction
6. Document findings

### Key Principles

- Run analysis before every iteration
- Never change documents and test cases simultaneously
- Check test case distribution before modifying documents
- Investigate "no differentiation" before making changes
- Use realistic complexity, not artificial difficulty

## Test Case Design

**Ineffective:** Direct lookups don't test chunking
```json
{"query": "What is the standard return window?"}
```
Answer appears in any chunk mentioning returns.

**Effective:** Multi-section synthesis tests chunking
```json
{"query": "VIP customer with 6 years tenure wants $600 refund in December. Who approves?"}
```
Requires combining rules across chunks (base thresholds + VIP elevation + seasonal adjustment).

### Target Distribution (40-50 cases)

- 30% simple lookups (baseline)
- 40% moderate complexity (2-3 pieces of info)
- 30% high complexity (edge cases, multi-step reasoning)

## Lessons Learned

- **Format matters as much as length**: Dense paragraph prose doesn't reflect real business docs. Use bullets, tables, short paragraphs.

- **Avoid artificial complexity**: Run-on sentences force differentiation but results don't generalize. Use realistic complexity.

- **Zero disagreements = investigate test quality first**: Perfect score equality (91.2% = 91.2%) with 0 disagreements means test cases don't differentiate strategies.

## Before Finalizing Results

Verify before considering results complete:

- Test cases represent realistic operational queries
- Document format matches real business style
- Results show some differentiation (not identical scores)
- Accuracy appropriate for task difficulty (not all >95% or all <40%)
- Failed cases manually reviewed
- Findings are explainable and actionable
