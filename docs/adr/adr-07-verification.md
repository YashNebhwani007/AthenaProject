# ADR-07: Verification Mechanics

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D7 — Verification mechanics, thresholds, and repair strategy.

## Context
The verifier runs V1–V5 checks on the structured draft report. It must decide: pass, repair (send back to LLM), or degrade (mark unverified / strip claim). The key design questions are: what are the thresholds, how does repair work, and when to give up.

## Options

### Option A: Rule-Based Checker with Structured Repair Feedback (Recommended)
Each V-rule is a Python function that returns pass/fail with specific failure details. Failures are sent back to the LLM as structured repair instructions.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — one function per rule, structured feedback format |
| Correctness | High — deterministic, testable rules |
| Repair quality | High — LLM gets precise instructions ("Finding f2 says 'higher' but t3.mean_a < t3.mean_b") |
| Risk | Low — bounded retries prevent infinite loops |
| Interview showcase | Excellent — demonstrates systematic verification thinking |

### Option B: LLM-as-Verifier
A second LLM call reviews the draft report for consistency.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low — just another prompt |
| Correctness | Low — LLM may miss the same errors it made |
| Cost | High — doubles LLM calls |
| Risk | High — non-deterministic, hard to test |

### Option C: Hybrid (Rule-Based + LLM for Semantic Checks)
Rules for V1, V4, V5; LLM for V2, V3 (semantic matching).

| Dimension | Assessment |
|-----------|-----------|
| Complexity | High — two verification paths |
| Risk | Medium — semantic checks are still non-deterministic |

## Decision
**Option A: Rule-Based Checker with Structured Repair Feedback.**

All five verification rules are implemented as deterministic Python functions. No LLM is used in verification.

### Rule Implementations

#### V1: Numeric Grounding
- Scan all finding texts for literal numbers (regex: integers, decimals, percentages).
- For each literal number found:
  - Check if it matches any metric in the cited evidence (within tolerance).
  - Tolerance: `|extracted - metric| / |metric| < 0.01` (1% relative) OR `|extracted - metric| < 0.005` (absolute, for small values).
  - Check if it's in the allowed-literals list (config constants like alpha=0.05, k=5).
- Also verify all `{{...}}` placeholders resolve to existing metrics.

#### V2: Claim-Evidence Consistency
- "Significant" / "not significant": check p-value against `alpha` (default 0.05, after correction).
- Direction words ("higher", "lower", "more", "less"): check sign of difference or effect size.
- Strength words: map to thresholds:
  - Correlation: |r| > 0.7 = "strong", 0.3–0.7 = "moderate", <0.3 = "weak"
  - Effect size (Cohen's d): >0.8 = "large", 0.5–0.8 = "medium", <0.5 = "small"
- Performance claims: verify they cite held-out metrics (not train metrics).

#### V3: Causal Language
- Scan for causal keywords: "causes", "caused by", "leads to", "results in", "due to", "because of", "effect of" (configurable list).
- If found, check `claim_type` field. If not `causal` or if no experimental design evidence exists → flag.
- Action: downgrade to "associated with" suggestion in repair feedback, or mark unverified.

#### V4: Linkage
- Every finding must have at least one evidence entry.
- Every recommendation must link to at least one finding.
- Every evidence `tool_result_id` must exist in the trace.

#### V5: Data-Quality Propagation
- If any leakage check returned `severity: "high"` → report must contain a caveat mentioning leakage, and model metrics must be flagged as "potentially unreliable."
- If missingness > 30% in any column used in analysis → caveat required.

### Repair Strategy
1. Run all V-rules on draft report. Collect all failures.
2. If any failures: construct a structured repair message listing each failure:
   ```json
   {
     "verification_failures": [
       {"rule": "V2", "finding_id": "f2", "issue": "Says 'higher' but t3.mean_a (0.23) < t3.mean_b (0.45)", "suggestion": "Change 'higher' to 'lower' or swap the comparison"}
     ]
   }
   ```
3. Send repair message to LLM with instruction: "Fix ONLY the listed issues. Do not change anything else."
4. Max repair iterations: **2**. If still failing after 2 repairs → degrade: mark failing claims as `"unverified"` and append a note to the verification summary.

### Verification Summary (appended to final report)
```json
{
  "total_checks": 14,
  "passed": 13,
  "failed": 0,
  "unverified_claims": 1,
  "repairs_attempted": 1,
  "details": [...]
}
```

## Consequences
- The verifier is fully deterministic and testable — each rule can be unit-tested with crafted report JSON.
- Repair relies on the LLM's ability to follow precise correction instructions — this is generally reliable.
- The system honestly reports what was verified and what wasn't.
- No LLM cost for verification itself — only for repairs.
