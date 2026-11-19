# Hypothesis Testing Multiplicity Correction Guide

When conducting iterative exploratory data analysis, running multiple simultaneous hypothesis tests
dramatically inflates the Family-Wise Error Rate (FWER). This guide details Athena's automated
correction procedures.

---

## 1. The Multi-Testing Problem
If an analyst tests $m$ independent null hypotheses, each at significance level $\alpha = 0.05$:
$$\text{FWER} = 1 - (1 - \alpha)^m$$
- For $m = 10$, $\text{FWER} \approx 40.1\%$
- For $m = 20$, $\text{FWER} \approx 64.2\%$

Without correction, false positive conclusions are virtually guaranteed.

---

## 2. Implemented Correction Methods

### A. Bonferroni Correction (Conservative FWER)
Adjusts the significance threshold by dividing $\alpha$ by the number of tests executed within the session:
$$\alpha_{\text{corrected}} = \frac{\alpha}{m}$$
- **Recommended Use:** Critical business decisions, medical hypotheses, confirmatory claims.
- **Trigger:** Configured when `n_tests_in_session > 1`.

### B. Benjamini-Hochberg Procedure (FDR Control)
Controls the expected proportion of false discoveries among rejected hypotheses:
1. Sort raw $p$-values: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
2. Find the largest index $k$ such that $p_{(k)} \le \frac{k}{m} \cdot \alpha$.
3. Reject all $H_{(i)}$ for $i = 1, \dots, k$.
- **Recommended Use:** High-dimensional feature screening, cohort discovery scans ($m \ge 10$).
