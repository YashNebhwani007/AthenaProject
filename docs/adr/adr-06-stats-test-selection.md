# ADR-06: Statistical Test Selection

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D6 — Statistical test selection: LLM-chosen with validation vs deterministic `recommend_test`.

## Context
The brief mentions both that the LLM selects statistical tests and that a `recommend_test` tool could deterministically pick the appropriate test. The risk: an LLM may choose inappropriate tests (e.g., t-test on non-normal data).

## Options

### Option A: Deterministic `recommend_test` Tool (Recommended)
A pure function that takes variable types, sample sizes, and assumption-check results to recommend the correct test.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — must encode decision logic for ~8 test types |
| Correctness | High — logic is auditable, deterministic, testable |
| Risk | Low — no LLM judgment involved in test selection |
| Interview showcase | Strong — demonstrates statistical rigor and software engineering |

### Option B: LLM-Chosen with Post-hoc Validation
The LLM picks a test; a validator checks assumptions after the fact and rejects inappropriate choices.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — must still implement assumption checking, plus retry logic |
| Correctness | Medium — depends on LLM's statistical knowledge; may waste retries |
| Risk | High — LLM may consistently choose wrong tests; retry loop burns budget |
| Interview showcase | Weaker — "the LLM picks" is less impressive than "deterministic logic picks" |

### Option C: Hybrid — `recommend_test` Suggests, LLM May Override
The tool recommends; the LLM can override with justification; the system validates either way.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | High — dual paths, override logic, justification parsing |
| Risk | Medium — override path is rarely useful and hard to test |

## Decision
**Option A: Deterministic `recommend_test` Tool.**

The LLM's role is to decide *what comparison to make* (which columns, what hypothesis). The `recommend_test` tool decides *which test to use* based on data characteristics.

### Decision Logic (encoded as a decision tree)

```
Input: variable_types (numeric/categorical), n_groups, sample_sizes, assumption_results

1. Compare two numeric groups?
   → Check normality (Shapiro-Wilk if n < 5000, else D'Agostino-Pearson)
   → Check equal variance (Levene's test)
   → Normal + equal variance → Independent t-test
   → Normal + unequal variance → Welch's t-test
   → Non-normal → Mann-Whitney U

2. Compare 3+ numeric groups?
   → Normal + equal variance → One-way ANOVA
   → Otherwise → Kruskal-Wallis
   → Post-hoc: Dunn's test with Bonferroni correction

3. Association between two categoricals?
   → Expected cell counts ≥ 5 → Chi-square test of independence
   → Otherwise → Fisher's exact test (if 2×2) or warn about low counts

4. Correlation between two numerics?
   → Normal bivariate → Pearson
   → Otherwise → Spearman
   → Always report both with interpretation

5. Paired data?
   → Not supported in v1 (flag and explain)
```

### Assumption Checks (always run, never left to LLM)
- Normality: Shapiro-Wilk (n < 5000) or D'Agostino-Pearson
- Equal variance: Levene's test
- Sample size adequacy: warn if any group < 20
- Multiple comparisons: Bonferroni correction applied automatically when >1 test per session

### Output
- `recommend_test` returns: recommended test name, reason string, assumption check results, warnings.
- `stats_test` then executes the recommended test and returns: test statistic, p-value, effect size (Cohen's d, Cramér's V, eta-squared, r as appropriate), confidence interval, interpretation guidelines.

## Consequences
- The LLM never decides which statistical test to run — it provides the comparison parameters, and the system handles the rest.
- New test types can be added to the decision tree without changing the LLM prompt.
- Benchmark must verify that the correct test is chosen for each scenario.
