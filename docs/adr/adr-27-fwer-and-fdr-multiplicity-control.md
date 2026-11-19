# ADR-27: Automated Family-Wise Error Rate and FDR Multiplicity Control

## Status
Accepted

## Context
When an analytical agent runs multiple hypothesis tests in a single exploration session,
the probability of at least one false positive (Type I error) escalates rapidly:
$P(\text{at least one false positive}) = 1 - (1 - \alpha)^k$.
Running 20 tests at $\alpha = 0.05$ yields a ~64% chance of falsely discovering a non-existent effect.

## Decision
1. Implement automated multiplicity adjustment in `stats_test` with two selectable policies:
   - **Bonferroni (FWER):** $\alpha_{\text{adjusted}} = \alpha / k$. Used when testing confirmatory claims or high-stakes business recommendations.
   - **Benjamini-Hochberg (FDR):** Sorts $p$-values and controls the false discovery proportion. Used during broad exploratory scans with $k > 10$.
2. Automatically track the cumulative test count $k$ within the session context.
3. Require the Verifier Rule V2 to check claimed significance against $\alpha_{\text{adjusted}}$ rather than the raw nominal $\alpha$.

## Consequences
- Eliminates specious "statistically significant" findings caused by multi-testing data dredge.
- Provides transparent reporting of both nominal and multiplicity-corrected $p$-values.
- Enforces rigorous statistical reporting aligned with modern epidemiological and econometrical standards.
