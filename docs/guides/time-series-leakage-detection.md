# Time-Series Leakage Detection and Temporal Validation Splits

## Overview
When analyzing temporal or longitudinal tabular datasets (e.g. daily transactions, historical customer
events), standard random train/test splits introduce temporal lookahead leakage. Models trained with
future information achieve artificially inflated evaluation scores that collapse in production.

## Athena Temporal Audit Workflow

1. **Timestamp Column Identification:**
   Athena scans datetime columns (`created_at`, `timestamp`, `event_date`) to determine whether
   observations possess explicit chronological ordering.

2. **Temporal Split Enforcement:**
   Rather than random k-fold cross-validation, Athena applies `TimeSeriesSplit` or out-of-time (OOT) holdouts:
   - **Training Window:** $t_0 \to t_{\text{split}}$
   - **Validation Window:** $t_{\text{split}} \to t_{\text{end}}$

3. **Feature Leakage Scanning:**
   Athena flags features computed with aggregation windows spanning past $t_{\text{event}}$
   (e.g., computing a rolling 30-day average that includes the target day's outcome).
