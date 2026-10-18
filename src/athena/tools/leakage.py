"""Data leakage detection tool implementing 6 distinct checks per ADR-05 and Brief."""

import re

import numpy as np
import pandas as pd
from pydantic import BaseModel
from sklearn.metrics import roc_auc_score

from athena.data import DatasetRegistry, default_registry
from athena.logging import get_logger
from athena.schemas import Metric, ToolResult, ToolStatus
from athena.tools.base import register_tool, tool_fn

logger = get_logger(__name__)

SUSPICIOUS_NAME_PATTERNS = [
    r".*cancellation.*",
    r".*refund.*",
    r".*exit_.*",
    r".*churn_date.*",
    r".*churn_reason.*",
    r".*disconnection.*",
    r".*termination.*",
    r".*post_event.*",
    r".*target.*copy.*",
]


class LeakageFinding(BaseModel):
    """Detailed observation from an individual leakage check."""

    check_name: str
    column: str | None = None
    severity: str  # "high", "medium", "low", "none"
    detail: str
    value: float | None = None


def _check_suspicious_names(columns: list[str], target_col: str) -> list[LeakageFinding]:
    """Check 1: Flag column names strongly suggestive of future or post-event information."""
    findings = []
    for c in columns:
        if c == target_col:
            continue
        c_lower = c.lower()
        for pat in SUSPICIOUS_NAME_PATTERNS:
            if re.match(pat, c_lower):
                findings.append(
                    LeakageFinding(
                        check_name="suspicious_names",
                        column=c,
                        severity="high",
                        detail=(
                            f"Column name '{c}' suggests future/post-event knowledge of the target."
                        ),
                    )
                )
                break
    return findings


def _check_id_columns(df: pd.DataFrame, target_col: str) -> list[LeakageFinding]:
    """Check 2: Identify unique ID columns that could lead to trivial memorization."""
    findings = []
    n_rows = len(df)
    for c in df.columns:
        if c == target_col:
            continue
        c_lower = c.lower()
        is_unique = df[c].nunique() == n_rows
        is_id_name = (
            c_lower.endswith("_id")
            or c_lower.endswith("id")
            or c_lower.endswith("_key")
            or "uuid" in c_lower
        )
        if is_unique and is_id_name:
            findings.append(
                LeakageFinding(
                    check_name="id_columns",
                    column=c,
                    severity="medium",
                    detail=(
                        f"Column '{c}' is a 100% unique identifier "
                        "and should not be used as a feature."
                    ),
                )
            )
    return findings


def _check_correlations(df: pd.DataFrame, target_col: str) -> list[LeakageFinding]:
    """Check 3: High linear or monotonic correlation with target."""
    findings = []
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        return findings

    y = df[target_col].to_numpy()
    for c in df.columns:
        if c == target_col:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            x = df[c].dropna().to_numpy()
            if len(x) != len(y):
                continue
            corr = np.corrcoef(x, y)[0, 1]
            if not np.isnan(corr) and abs(corr) >= 0.90:
                severity = "high" if abs(corr) >= 0.95 else "medium"
                findings.append(
                    LeakageFinding(
                        check_name="correlation",
                        column=c,
                        severity=severity,
                        detail=(
                            f"Extreme correlation |r|={abs(corr):.4f} "
                            f"with target '{target_col}'."
                        ),
                        value=round(float(corr), 4),
                    )
                )
    return findings


def _check_single_feature_auc(df: pd.DataFrame, target_col: str) -> list[LeakageFinding]:
    """Check 4: Single-feature predictive power nearing 1.0 (AUC > 0.95)."""
    findings = []
    y = df[target_col]
    if y.nunique() != 2:
        return findings

    # Encode binary target to 0 and 1
    y_binary = (y == y.unique()[0]).astype(int).to_numpy()

    for c in df.columns:
        if c == target_col:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            clean_s = df[c].dropna()
            if len(clean_s) != len(y_binary) or clean_s.nunique() <= 1:
                continue
            try:
                auc = float(roc_auc_score(y_binary, clean_s.to_numpy()))
                auc_max = max(auc, 1.0 - auc)
                if auc_max >= 0.95:
                    findings.append(
                        LeakageFinding(
                            check_name="single_feature_auc",
                            column=c,
                            severity="high",
                            detail=(
                                f"Single feature '{c}' achieves "
                                f"near-perfect ROC-AUC={auc_max:.4f}."
                            ),
                            value=round(auc_max, 4),
                        )
                    )
            except Exception:
                continue
    return findings


def _check_train_test_duplicates(df: pd.DataFrame) -> list[LeakageFinding]:
    """Check 5: Data duplication that threatens train-test partition independence."""
    findings = []
    dup_count = int(df.duplicated().sum())
    dup_pct = dup_count / len(df) if len(df) > 0 else 0.0
    if dup_pct > 0.05:
        findings.append(
            LeakageFinding(
                check_name="train_test_duplicates",
                severity="medium" if dup_pct > 0.15 else "low",
                detail=(
                    f"High duplication ({dup_pct:.1%}, {dup_count} duplicate rows) "
                    "threatens train-test independence."
                ),
                value=round(dup_pct, 4),
            )
        )
    return findings


def _check_temporal_split(df: pd.DataFrame) -> list[LeakageFinding]:
    """Check 6: Detect date/timestamp columns indicating time-series structure."""
    findings = []
    date_cols = []
    for c in df.columns:
        c_lower = c.lower()
        if any(term in c_lower for term in ("date", "time", "year", "timestamp")):
            date_cols.append(c)

    if date_cols:
        findings.append(
            LeakageFinding(
                check_name="temporal_split",
                column=", ".join(date_cols),
                severity="low",
                detail=(
                    f"Temporal columns detected ({', '.join(date_cols)}). "
                    "Verify time-ordered splitting is applied."
                ),
            )
        )
    return findings


@register_tool("check_leakage")
@tool_fn("check_leakage")
async def check_leakage(
    target_col: str,
    dataset_id: str,
    registry: DatasetRegistry | None = None,
) -> ToolResult:
    """Run six comprehensive data leakage checks on candidate features against target."""
    reg = registry or default_registry
    conn = reg.get_connection(dataset_id)
    handle = reg.get(dataset_id)
    tbl = handle.table_name

    df = conn.execute(f"SELECT * FROM {tbl}").fetchdf()
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset '{dataset_id}'")

    columns = list(df.columns)
    all_findings: list[LeakageFinding] = []

    # Run the six named checks
    all_findings.extend(_check_suspicious_names(columns, target_col))
    all_findings.extend(_check_id_columns(df, target_col))
    all_findings.extend(_check_correlations(df, target_col))
    all_findings.extend(_check_single_feature_auc(df, target_col))
    all_findings.extend(_check_train_test_duplicates(df))
    all_findings.extend(_check_temporal_split(df))

    high_findings = [f for f in all_findings if f.severity == "high"]
    med_findings = [f for f in all_findings if f.severity == "medium"]

    has_leakage = len(high_findings) > 0 or len(med_findings) > 0
    if high_findings:
        max_severity = "high"
    elif med_findings:
        max_severity = "medium"
    elif all_findings:
        max_severity = "low"
    else:
        max_severity = "none"

    suspicious_cols = sorted(list({
        f.column for f in all_findings
        if f.column and f.severity in ("high", "medium")
    }))

    warnings = [
        f"[{f.severity.upper()}] {f.detail}"
        for f in all_findings
        if f.severity in ("high", "medium")
    ]

    output_payload = {
        "dataset_id": dataset_id,
        "target_col": target_col,
        "has_leakage": has_leakage,
        "max_severity": max_severity,
        "suspicious_columns": suspicious_cols,
        "findings": [f.model_dump() for f in all_findings],
        "quality_warnings": warnings,
    }

    metrics = [
        Metric(name="leakage_detected", value=1 if has_leakage else 0),
        Metric(name="high_severity_leak_count", value=len(high_findings)),
        Metric(name="total_leakage_findings", value=len(all_findings)),
    ]

    return ToolResult(
        id="",
        tool="check_leakage",
        args={"target_col": target_col, "dataset_id": dataset_id},
        status=ToolStatus.ok,
        output=output_payload,
        metrics=metrics,
        warnings=warnings,
    )
