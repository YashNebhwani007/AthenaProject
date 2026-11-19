# ADR-18: Multi-Model Benchmark Evaluation Strategy

**Status:** Accepted  
**Date:** 2026-10-18  
**Decision:** D18 — Ground-truth evaluation harness across deterministic and unverified systems.

## Context
Evaluating AI agents for data science requires deterministic ground-truth benchmarks rather than subjective LLM-as-a-judge scoring. Athena requires comparing three architectural paradigms:
- **System A1:** Athena Full (Tool Calling + Adversarial Verifier + Repair Loop).
- **System A2:** Athena Unverified (Tool Calling with Raw Draft Generation).
- **System B1:** Baseline LLM + Python Interpreter.

## Decision
1. Standardize 42 benchmark questions across 4 domains (Telco Churn, Adult Income, California Housing, Titanic).
2. Compute reference values deterministically using DuckDB and pandas (`benchmark/ground_truth/`).
3. Evaluate 7 quantitative metrics: Numeric Accuracy (within tolerance), Hallucination Rate, Causal Trap Catch Rate, Leakage Precision/Recall, and Verifier Pass Rate.
