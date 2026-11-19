# ADR-34: Automated Target Inference Heuristic Weighting

## Status
Accepted

## Context
When training tabular ML models or running causal inference without explicit target specifications,
Athena's auto-target heuristic must select the optimal target variable from tabular metadata.
Simple keyword matching (e.g., matching "churn" or "survived") fails on ambiguous datasets or
non-English column names.

## Decision
1. Implement a weighted multi-factor heuristic scoring function for target column identification:
   - Keyword relevance (e.g., "churn", "target", "label", "outcome", "survived"): weight 0.40
   - Question token semantic similarity (cosine similarity with user prompt keywords): weight 0.35
   - Cardinality and distribution (binary 0/1 or discrete categories with imbalance ratio < 20:1): weight 0.25
2. If top scoring candidate does not exceed a confidence threshold of 0.60, require explicit LLM prompt disambiguation.

## Consequences
- Accurate automatic target selection across benchmark tabular datasets.
- Eliminates erroneous target assignments on multi-binary column datasets.
- Transparent explainability for why an outcome variable was selected.
