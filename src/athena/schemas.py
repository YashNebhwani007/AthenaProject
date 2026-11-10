"""Core Pydantic schemas for Athena."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ToolStatus(str, Enum):
    """Execution status of a deterministic tool."""

    ok = "ok"
    error = "error"


class Metric(BaseModel):
    """Extracted numeric or categorical metric produced by a tool."""

    name: str
    value: float | int | str
    unit: str | None = None


class Artifact(BaseModel):
    """File, plot, or tabular artifact created by a tool."""

    type: str
    ref: str


class ToolResult(BaseModel):
    """Deterministic output and audit metadata for a single tool execution."""

    id: str
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    status: ToolStatus = ToolStatus.ok
    output: Any = None
    metrics: list[Metric] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    runtime_ms: float = 0.0


class ClaimType(str, Enum):
    """Analytical classification of a reported finding."""

    descriptive = "descriptive"
    comparative = "comparative"
    statistical = "statistical"
    predictive = "predictive"
    causal = "causal"


class EvidenceRef(BaseModel):
    """Link tying a finding claim directly to a tool result metric."""

    tool_result_id: str
    metric: str

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_ref(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "tool_result_id" not in d or not d["tool_result_id"]:
                for alias in ("result_id", "tool_id", "id", "step"):
                    if alias in d and d[alias]:
                        d["tool_result_id"] = str(d[alias])
                        break
            if "metric" not in d or not d["metric"]:
                for alias in ("metric_name", "name", "value", "key"):
                    if alias in d and d[alias]:
                        d["metric"] = str(d[alias])
                        break
            d.setdefault("tool_result_id", "")
            d.setdefault("metric", "")
            return d
        return data


class Finding(BaseModel):
    """Fact-based observation backed by tool evidence."""

    id: str = "f1"
    text: str
    claim_type: ClaimType = ClaimType.descriptive
    evidence: list[EvidenceRef] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_finding(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "id": "f1",
                "text": data,
                "claim_type": ClaimType.descriptive,
                "evidence": [],
            }
        if isinstance(data, dict):
            d = dict(data)
            if "id" not in d or not d["id"]:
                d["id"] = "f1"
            else:
                d["id"] = str(d["id"])

            if "text" not in d or not d["text"]:
                for alias in (
                    "statement",
                    "claim",
                    "finding",
                    "description",
                    "summary",
                    "content",
                    "observation",
                ):
                    if alias in d and d[alias]:
                        d["text"] = str(d[alias])
                        break
            if "text" not in d or not d["text"]:
                d["text"] = "Finding statement not provided."

            if "claim_type" not in d or not d["claim_type"]:
                d["claim_type"] = ClaimType.descriptive
            elif isinstance(d["claim_type"], str):
                val = d["claim_type"].lower().strip()
                valid_types = {ct.value: ct for ct in ClaimType}
                if val in valid_types:
                    d["claim_type"] = valid_types[val]
                elif "stat" in val:
                    d["claim_type"] = ClaimType.statistical
                elif "caus" in val:
                    d["claim_type"] = ClaimType.causal
                elif "pred" in val:
                    d["claim_type"] = ClaimType.predictive
                elif "comp" in val:
                    d["claim_type"] = ClaimType.comparative
                else:
                    d["claim_type"] = ClaimType.descriptive

            if "evidence" not in d or d["evidence"] is None:
                d["evidence"] = []
            elif not isinstance(d["evidence"], list):
                d["evidence"] = [d["evidence"]]
            return d
        return data


class Confidence(str, Enum):
    """Degree of confidence behind a recommendation."""

    low = "low"
    medium = "medium"
    high = "high"


class Recommendation(BaseModel):
    """Actionable business guidance supported by findings."""

    text: str
    supported_by: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.medium

    @model_validator(mode="before")
    @classmethod
    def normalize_recommendation(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "text": data,
                "supported_by": [],
                "confidence": Confidence.medium,
            }
        if isinstance(data, dict):
            d = dict(data)
            if "text" not in d or not d["text"]:
                for alias in (
                    "recommendation",
                    "action",
                    "guidance",
                    "description",
                    "advice",
                    "suggestion",
                ):
                    if alias in d and d[alias]:
                        d["text"] = str(d[alias])
                        break
            if "text" not in d or not d["text"]:
                d["text"] = "Recommendation not provided."

            if "supported_by" not in d or d["supported_by"] is None:
                d["supported_by"] = []
            elif isinstance(d["supported_by"], str):
                d["supported_by"] = [d["supported_by"]]

            if "confidence" not in d or not d["confidence"]:
                d["confidence"] = Confidence.medium
            elif isinstance(d["confidence"], str):
                c_val = d["confidence"].lower().strip()
                valid_conf = {c.value: c for c in Confidence}
                if c_val in valid_conf:
                    d["confidence"] = valid_conf[c_val]
                else:
                    d["confidence"] = Confidence.medium
            return d
        return data


class Report(BaseModel):
    """Final decision intelligence report produced by Athena."""

    question: str = ""
    answerable: bool = True
    tldr: str
    findings: list[Finding] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_report(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            # Unwrap nested {"report": {...}} if present
            if "report" in d and isinstance(d["report"], dict):
                inner = dict(d["report"])
                for k, v in d.items():
                    if k != "report" and k not in inner:
                        inner[k] = v
                d = inner

            if "question" not in d or not d["question"]:
                d["question"] = ""
            if "answerable" not in d or d["answerable"] is None:
                d["answerable"] = True
            if "tldr" not in d or not d["tldr"]:
                for alias in ("summary", "overview", "answer", "conclusion", "tl_dr"):
                    if alias in d and d[alias]:
                        d["tldr"] = str(d[alias])
                        break

            # If neither tldr nor findings are present, do not manufacture a fake report
            if ("tldr" not in d or not d["tldr"]) and not d.get("findings"):
                pass
            elif "tldr" not in d or not d["tldr"]:
                d["tldr"] = "Analysis completed."

            if "findings" not in d or d["findings"] is None:
                d["findings"] = []
            elif not isinstance(d["findings"], list):
                d["findings"] = [d["findings"]]

            if "caveats" not in d or d["caveats"] is None:
                d["caveats"] = []
            elif isinstance(d["caveats"], str):
                d["caveats"] = [d["caveats"]]

            if "recommendations" not in d or d["recommendations"] is None:
                d["recommendations"] = []
            elif not isinstance(d["recommendations"], list):
                d["recommendations"] = [d["recommendations"]]
            return d
        return data


class VerificationResult(BaseModel):
    """Result of validating an individual verification rule."""

    rule: str
    finding_id: str | None = None
    passed: bool
    issue: str | None = None
    suggestion: str | None = None


class VerificationSummary(BaseModel):
    """Aggregated verification results across all checks and repair loops."""

    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    unverified_claims: int = 0
    repairs_attempted: int = 0
    details: list[VerificationResult] = Field(default_factory=list)


class RunResult(BaseModel):
    """Complete trace, report, and telemetry for an analytical run."""

    run_id: str
    session_id: str
    question: str
    report: Report | None = None
    verification: VerificationSummary | None = None
    trace: list[ToolResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_steps: int = 0
    total_tokens: int = 0
    total_runtime_ms: float = 0.0


class EventType(str, Enum):
    """SSE streaming event types emitted during orchestration."""

    step_started = "step_started"
    tool_result = "tool_result"
    report_draft = "report_draft"
    verification = "verification"
    final = "final"
    error = "error"
    status = "status"
    clarification_needed = "clarification_needed"
