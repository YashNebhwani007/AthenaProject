# Benchmark Evaluation Methodology & Scoring Rubrics

The Athena benchmark suite evaluates autonomous data science systems on 42 analytical questions.

## Scoring Dimensions

1. **Numeric Accuracy:** Claimed numbers match deterministic ground-truth within $\pm 1\%$ relative or 0.005 absolute tolerance.
2. **Hallucination Rate:** Proportion of reports containing $\ge 1$ unverified or ungrounded numeric claim.
3. **Causal Trap Catch Rate:** Proportion of observational questions where the system correctly refuses or avoids causal language.
4. **Target Leakage Detection:** Precision and recall on intentionally introduced leakage features across benchmark datasets.
5. **Multiplicity Correction:** Ensuring p-values are adjusted when family-wise testing is detected.
