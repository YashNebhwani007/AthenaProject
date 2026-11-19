# Data Leakage Audit Specification

Athena's `check_leakage` tool audits candidate features against the target column using six independent heuristic checks:

## Six Independent Leakage Checks

| Check Name | Detection Heuristic | Severity |
|---|---|:---:|
| **1. Suspicious Names** | Regex matching post-event keywords (`cancellation`, `refund`, `churn_reason`, `exit_date`). | High |
| **2. Unique ID Memorization** | Column with 100% distinct values and ID-like naming (`id`, `uuid`, `key`). | High |
| **3. Perfect Target Correlation** | Numeric correlation $|r| > 0.95$ with continuous target or binary label. | High |
| **4. Single-Feature AUC** | A single univariate feature yielding ROC-AUC $> 0.95$ on classification target. | High |
| **5. Train/Test Duplicates** | Duplicate rows across candidate feature sets causing memorization leaks. | Medium |
| **6. Temporal Inconsistency** | Look-ahead timestamps occurring after target event observation window. | High |
