# Prompt Engineering & Tool Calling Best Practices

Athena employs a system prompt that guides LLMs to act as an evidence-driven data science assistant.

## Core Directives

1. **Deterministic Execution First:** The agent never computes statistics mentally. Every calculation is performed by a registered tool.
2. **Untrusted Data Isolation:** Column names and table cells are treated as raw values, preventing prompt injection through data contents.
3. **Subgroup Analysis Protocol:** Multi-variable comparisons and conditional distributions must be executed via `run_sql` rather than approximated from univariate profiles.
4. **Tool Chain Workflow:**
   - Exploratory / Descriptive $\to$ `profile` and `run_sql`.
   - Comparative / Associative $\to$ `recommend_test` $\to$ `stats_test`.
   - Predictive / Machine Learning $\to$ `check_leakage` $\to$ `train_model` $\to$ `explain_model`.
   - Out-of-sample Scoring $\to$ `predict_model`.
