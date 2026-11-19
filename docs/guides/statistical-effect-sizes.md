# Statistical Effect Size Interpretation and Cohen Benchmarks

## Overview
P-values indicate whether an observed difference is statistically significant (unlikely under
the null hypothesis), but they do not measure practical significance or magnitude.
Athena's statistical analysis tools report effect sizes alongside p-values to prevent over-interpreting
statistically significant effects driven solely by large sample sizes.

## Effect Size Metrics Supported

### 1. Cohen's d (Two Independent Groups)
Used for two-sample independent t-tests:
$$d = \frac{\bar{x}_1 - \bar{x}_2}{s_{\text{pooled}}}$$

| Benchmark | Value | Practical Interpretation |
|---|---|---|
| Negligible | $d < 0.20$ | Statistically detectable but negligible real-world impact |
| Small | $0.20 \le d < 0.50$ | Noticeable with careful observation |
| Medium | $0.50 \le d < 0.80$ | Readily apparent difference between cohorts |
| Large | $d \ge 0.80$ | Substantial, dominant practical difference |

### 2. Cramér's V (Contingency Tables & Chi-Square)
Used for association between categorical variables:
$$V = \sqrt{\frac{\chi^2}{n \cdot \min(r-1, c-1)}}$$

- $V < 0.10$: Weak association
- $0.10 \le V < 0.30$: Moderate association
- $V \ge 0.30$: Strong association

### 3. Pearson's r / Spearman's rho (Correlations)
- $|r| < 0.30$: Weak correlation
- $0.30 \le |r| < 0.60$: Moderate correlation
- $|r| \ge 0.60$: Strong correlation

## Verifier Enforcement (Rule V2)
Athena's Verifier automatically cross-references narrative statements against effect size metrics.
Claims of "massive discrepancy" with $d = 0.12$ trigger a V2 verifier warning requiring calibration.
