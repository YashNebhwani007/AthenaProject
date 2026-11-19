"""Unit tests for verifier rules V1 through V5 per Task 4.1."""

from athena.schemas import (
    ClaimType,
    Confidence,
    EvidenceRef,
    Finding,
    Metric,
    Recommendation,
    Report,
    ToolResult,
    ToolStatus,
)
from athena.verify.rules import (
    check_v1_numeric_grounding,
    check_v2_claim_evidence_consistency,
    check_v3_causal_language,
    check_v4_linkage,
    check_v5_data_quality_propagation,
)


def make_tool_result(
    tid: str,
    tool: str,
    metrics: list[Metric],
    output: dict | None = None,
) -> ToolResult:
    return ToolResult(
        id=tid,
        tool=tool,
        status=ToolStatus.ok,
        metrics=metrics,
        output=output or {},
    )


# -------------------------------------------------------------
# Rule V1 Tests: Numeric Grounding
# -------------------------------------------------------------


def test_v1_empty_findings_passes():
    rep = Report(question="Q", tldr="tl", findings=[])
    res = check_v1_numeric_grounding(rep, [])
    assert all(r.passed for r in res)


def test_v1_valid_placeholder_passes():
    tr = make_tool_result("t1", "profile", [Metric(name="churn_rate", value=0.25, unit="")])
    finding = Finding(
        id="f1",
        text="The overall churn rate is {{t1.churn_rate}}.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="churn_rate")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [tr])
    assert all(r.passed for r in res)


def test_v1_grounded_literal_number_passes():
    tr = make_tool_result("t1", "profile", [Metric(name="churn_rate", value=25.0, unit="%")])
    finding = Finding(
        id="f1",
        text="The churn rate is 25.0%.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="churn_rate")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [tr])
    assert all(r.passed for r in res)


def test_v1_allowed_literal_number_passes():
    finding = Finding(
        id="f1",
        text="Top 5 customer segments were analyzed with alpha=0.05.",
        claim_type=ClaimType.descriptive,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [])
    assert all(r.passed for r in res)


def test_v1_unresolved_placeholder_fails():
    finding = Finding(
        id="f1",
        text="Churn rate is {{t1.unknown_metric}}.",
        claim_type=ClaimType.descriptive,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [])
    assert any(not r.passed for r in res)


def test_v1_ungrounded_literal_number_fails():
    finding = Finding(
        id="f1",
        text="Revenue jumped by 78.43% without proof.",
        claim_type=ClaimType.descriptive,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [])
    assert any(not r.passed for r in res)


def test_v1_malformed_placeholder_fails():
    finding = Finding(
        id="f1",
        text="Rate is {{invalid_syntax}}.",
        claim_type=ClaimType.descriptive,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [])
    assert any(not r.passed for r in res)


def test_v1_percentage_conversion_and_relative_tolerance_passes():
    tr = make_tool_result("t1", "profile", [Metric(name="rate", value=0.684, unit="")])
    finding = Finding(
        id="f1",
        text="The computed retention rate was 68.4% across the cohort.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="rate")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [tr])
    assert all(r.passed for r in res)


def test_v1_multiple_grounded_numbers_in_single_finding_passes():
    tr = make_tool_result(
        "t1",
        "profile",
        [
            Metric(name="metric_a", value=42.5, unit=""),
            Metric(name="metric_b", value=18.2, unit=""),
        ],
    )
    finding = Finding(
        id="f1",
        text="Metric A reached 42.5 while Metric B recorded 18.2.",
        claim_type=ClaimType.descriptive,
        evidence=[
            EvidenceRef(tool_result_id="t1", metric="metric_a"),
            EvidenceRef(tool_result_id="t1", metric="metric_b"),
        ],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v1_numeric_grounding(rep, [tr])
    assert all(r.passed for r in res)


# -------------------------------------------------------------
# Rule V2 Tests: Claim-Evidence Consistency
# -------------------------------------------------------------


def test_v2_empty_findings_passes():
    rep = Report(question="Q", tldr="tl", findings=[])
    res = check_v2_claim_evidence_consistency(rep, [])
    assert all(r.passed for r in res)


def test_v2_valid_significant_claim_passes():
    tr = make_tool_result("t1", "stats_test", [Metric(name="p_value", value=0.001, unit="")])
    finding = Finding(
        id="f1",
        text="There is a statistically significant difference in charges.",
        claim_type=ClaimType.statistical,
        evidence=[EvidenceRef(tool_result_id="t1", metric="p_value")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v2_claim_evidence_consistency(rep, [tr])
    assert all(r.passed for r in res)


def test_v2_valid_direction_claim_passes():
    tr = make_tool_result("t1", "stats_test", [Metric(name="mean_diff", value=15.2, unit="")])
    finding = Finding(
        id="f1",
        text="Group A had a higher average monthly charge.",
        claim_type=ClaimType.comparative,
        evidence=[EvidenceRef(tool_result_id="t1", metric="mean_diff")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v2_claim_evidence_consistency(rep, [tr])
    assert all(r.passed for r in res)


def test_v2_insignificant_p_value_fails():
    tr = make_tool_result("t1", "stats_test", [Metric(name="p_value", value=0.45, unit="")])
    finding = Finding(
        id="f1",
        text="There is a statistically significant difference between groups.",
        claim_type=ClaimType.statistical,
        evidence=[EvidenceRef(tool_result_id="t1", metric="p_value")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v2_claim_evidence_consistency(rep, [tr])
    assert any(not r.passed for r in res)


def test_v2_mismatched_direction_fails():
    tr = make_tool_result("t1", "stats_test", [Metric(name="mean_diff", value=-12.5, unit="")])
    finding = Finding(
        id="f1",
        text="Senior citizens had higher monthly charges.",
        claim_type=ClaimType.comparative,
        evidence=[EvidenceRef(tool_result_id="t1", metric="mean_diff")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v2_claim_evidence_consistency(rep, [tr])
    assert any(not r.passed for r in res)


def test_v2_weak_correlation_claiming_strong_fails():
    tr = make_tool_result("t1", "stats_test", [Metric(name="pearson_r", value=0.15, unit="")])
    finding = Finding(
        id="f1",
        text="There is a strong correlation between age and income.",
        claim_type=ClaimType.statistical,
        evidence=[EvidenceRef(tool_result_id="t1", metric="pearson_r")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v2_claim_evidence_consistency(rep, [tr])
    assert any(not r.passed for r in res)


def test_v2_predictive_claim_missing_metrics_fails():
    tr = make_tool_result("t1", "predict_model", [Metric(name="samples", value=100, unit="")])
    finding = Finding(
        id="f1",
        text="Model predicts customer churn with high fidelity.",
        claim_type=ClaimType.predictive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="samples")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v2_claim_evidence_consistency(rep, [tr])
    assert any(not r.passed for r in res)


def test_v2_predictive_claim_with_auc_metric_passes():
    tr = make_tool_result("t1", "predict_model", [Metric(name="roc_auc", value=0.88, unit="")])
    finding = Finding(
        id="f1",
        text="Model achieved strong discriminative power on test split.",
        claim_type=ClaimType.predictive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="roc_auc")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v2_claim_evidence_consistency(rep, [tr])
    assert all(r.passed for r in res)


# -------------------------------------------------------------
# Rule V3 Tests: Causal Language
# -------------------------------------------------------------


def test_v3_empty_findings_passes():
    rep = Report(question="Q", tldr="tl", findings=[])
    res = check_v3_causal_language(rep)
    assert all(r.passed for r in res)


def test_v3_associational_language_passes():
    finding = Finding(
        id="f1",
        text="Higher fiber optic usage is associated with increased churn.",
        claim_type=ClaimType.comparative,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v3_causal_language(rep)
    assert all(r.passed for r in res)


def test_v3_legitimate_causal_claim_type_passes():
    finding = Finding(
        id="f1",
        text="Treatment A causes reduced latency.",
        claim_type=ClaimType.causal,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v3_causal_language(rep)
    assert all(r.passed for r in res)


def test_v3_causal_keyword_causes_fails():
    finding = Finding(
        id="f1",
        text="Signing a month-to-month contract causes customers to churn.",
        claim_type=ClaimType.comparative,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v3_causal_language(rep)
    assert any(not r.passed for r in res)


def test_v3_causal_keyword_leads_to_fails():
    finding = Finding(
        id="f1",
        text="Higher monthly charges leads to dissatisfaction.",
        claim_type=ClaimType.descriptive,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v3_causal_language(rep)
    assert any(not r.passed for r in res)


def test_v3_causal_keyword_due_to_fails():
    finding = Finding(
        id="f1",
        text="Low tenure churn is due to price spikes.",
        claim_type=ClaimType.comparative,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v3_causal_language(rep)
    assert any(not r.passed for r in res)


def test_v3_causal_keyword_caused_by_fails():
    finding = Finding(
        id="f1",
        text="The decrease in user churn was caused by plan revisions.",
        claim_type=ClaimType.descriptive,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v3_causal_language(rep)
    assert any(not r.passed for r in res)


def test_v3_causal_keyword_results_in_fails():
    finding = Finding(
        id="f1",
        text="Higher contract duration results in superior customer retention.",
        claim_type=ClaimType.comparative,
        evidence=[],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding])
    res = check_v3_causal_language(rep)
    assert any(not r.passed for r in res)


# -------------------------------------------------------------
# Rule V4 Tests: Linkage
# -------------------------------------------------------------


def test_v4_empty_report_passes():
    rep = Report(question="Q", tldr="tl", findings=[], recommendations=[])
    res = check_v4_linkage(rep, [])
    assert all(r.passed for r in res)


def test_v4_valid_linkage_passes():
    tr = make_tool_result("t1", "profile", [Metric(name="m", value=1, unit="")])
    finding = Finding(
        id="f1",
        text="Finding text.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="m")],
    )
    rec = Recommendation(text="Take action.", supported_by=["f1"], confidence=Confidence.high)
    rep = Report(question="Q", tldr="tl", findings=[finding], recommendations=[rec])
    res = check_v4_linkage(rep, [tr])
    assert all(r.passed for r in res)


def test_v4_finding_missing_evidence_fails():
    finding = Finding(id="f1", text="No evidence.", claim_type=ClaimType.descriptive, evidence=[])
    rep = Report(question="Q", tldr="tl", findings=[finding], recommendations=[])
    res = check_v4_linkage(rep, [])
    assert any(not r.passed for r in res)


def test_v4_nonexistent_tool_id_fails():
    finding = Finding(
        id="f1",
        text="Invalid tool.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t99", metric="m")],
    )
    rep = Report(question="Q", tldr="tl", findings=[finding], recommendations=[])
    res = check_v4_linkage(rep, [])
    assert any(not r.passed for r in res)


def test_v4_recommendation_missing_findings_fails():
    tr = make_tool_result("t1", "profile", [Metric(name="m", value=1, unit="")])
    finding = Finding(
        id="f1",
        text="Valid finding.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="m")],
    )
    rec = Recommendation(text="Unsupported action.", supported_by=[], confidence=Confidence.low)
    rep = Report(question="Q", tldr="tl", findings=[finding], recommendations=[rec])
    res = check_v4_linkage(rep, [tr])
    assert any(not r.passed for r in res)


def test_v4_recommendation_citing_unknown_finding_fails():
    tr = make_tool_result("t1", "profile", [Metric(name="m", value=1, unit="")])
    finding = Finding(
        id="f1",
        text="Valid finding.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="m")],
    )
    rec = Recommendation(text="Action.", supported_by=["f99"], confidence=Confidence.low)
    rep = Report(question="Q", tldr="tl", findings=[finding], recommendations=[rec])
    res = check_v4_linkage(rep, [tr])
    assert any(not r.passed for r in res)


def test_v4_multiple_recommendations_all_valid_passes():
    tr = make_tool_result("t1", "profile", [Metric(name="m", value=1, unit="")])
    f1 = Finding(
        id="f1",
        text="Finding one.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="m")],
    )
    f2 = Finding(
        id="f2",
        text="Finding two.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="m")],
    )
    r1 = Recommendation(text="Action A.", supported_by=["f1"], confidence=Confidence.high)
    r2 = Recommendation(text="Action B.", supported_by=["f1", "f2"], confidence=Confidence.medium)
    rep = Report(question="Q", tldr="tl", findings=[f1, f2], recommendations=[r1, r2])
    res = check_v4_linkage(rep, [tr])
    assert all(r.passed for r in res)


def test_v4_multiple_recommendations_one_invalid_fails():
    tr = make_tool_result("t1", "profile", [Metric(name="m", value=1, unit="")])
    f1 = Finding(
        id="f1",
        text="Finding one.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="m")],
    )
    r1 = Recommendation(text="Valid rec.", supported_by=["f1"], confidence=Confidence.high)
    r2 = Recommendation(
        text="Invalid rec.", supported_by=["non_existent"], confidence=Confidence.low
    )
    rep = Report(question="Q", tldr="tl", findings=[f1], recommendations=[r1, r2])
    res = check_v4_linkage(rep, [tr])
    assert any(not r.passed for r in res)


# -------------------------------------------------------------
# Rule V5 Tests: Data Quality Propagation
# -------------------------------------------------------------


def test_v5_clean_data_passes():
    rep = Report(question="Q", tldr="tl", findings=[], caveats=[])
    res = check_v5_data_quality_propagation(rep, [])
    assert all(r.passed for r in res)


def test_v5_leakage_with_caveat_passes():
    tr = make_tool_result("t1", "leakage_check", [], output={"highest_severity": "high"})
    rep = Report(
        question="Q",
        tldr="tl",
        findings=[],
        caveats=["Model metrics may be inflated due to target leakage."],
    )
    res = check_v5_data_quality_propagation(rep, [tr])
    assert all(r.passed for r in res)


def test_v5_missingness_with_caveat_passes():
    tr = make_tool_result(
        "t1",
        "profile_dataset",
        [],
        output={"columns": {"notes": {"null_percent": 65.0}}},
    )
    rep = Report(
        question="Q",
        tldr="tl",
        findings=[],
        caveats=["Column notes had high missingness (>60% null values)."],
    )
    res = check_v5_data_quality_propagation(rep, [tr])
    assert all(r.passed for r in res)


def test_v5_leakage_without_caveat_fails():
    tr = make_tool_result("t1", "leakage_check", [], output={"highest_severity": "high"})
    rep = Report(question="Q", tldr="tl", findings=[], caveats=["Everything is fine."])
    res = check_v5_data_quality_propagation(rep, [tr])
    assert any(not r.passed for r in res)


def test_v5_high_missingness_without_caveat_fails():
    tr = make_tool_result(
        "t1",
        "profile_dataset",
        [],
        output={"columns": {"notes": {"null_percent": 45.0}}},
    )
    rep = Report(question="Q", tldr="tl", findings=[], caveats=[])
    res = check_v5_data_quality_propagation(rep, [tr])
    assert any(not r.passed for r in res)
