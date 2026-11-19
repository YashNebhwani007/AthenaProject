# Verifier Rules Reference and Grounding Specification

Athena executes a 5-point deterministic verification pipeline on draft reports.

## Rule Definitions

### V1: Numeric Grounding
Every numerical value in findings must either match an allowed mathematical literal (`{0, 1, 2, 3, 4, 5, 10, 20, 50, 100, 0.05, 0.01, 0.001}`) or resolve against cited tool result metrics.
- **Relative Tolerance:** 1.0% (`ATHENA_NUMERIC_TOLERANCE_RELATIVE = 0.01`)
- **Absolute Tolerance:** 0.005 (`ATHENA_NUMERIC_TOLERANCE_ABSOLUTE = 0.005`)
- Supports template placeholder syntax: `{{t1.metric_name}}`.

### V2: Claim-Evidence Consistency
- Claims stating "statistically significant" require $p < \alpha / k$ (Bonferroni adjusted).
- Directional assertions ("higher", "lower", "positive", "negative") must match mathematical sign.
- Strength qualifiers ("strong", "moderate", "weak") must obey effect size boundaries.

### V3: Causal Language Trap Check
Detects causal phrasing (*causes*, *leads to*, *results in*, *due to*, *because of*) in observational analyses.

### V4: Structural Trace Linkage
- Every finding must cite $\ge 1$ executed tool result ID (`t1`, `t2`, etc.).
- Every recommendation must link to valid finding IDs (`f1`, `f2`, etc.).

### V5: Data Quality & Leakage Propagation
Ensures warnings from leakage checks or high missingness are propagated as explicit caveats.
