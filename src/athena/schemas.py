"""Core Pydantic schemas for Athena."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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


class Finding(BaseModel):
    """Fact-based observation backed by tool evidence."""

    id: str
    text: str
    claim_type: ClaimType
    evidence: list[EvidenceRef] = Field(default_factory=list)


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


class Report(BaseModel):
    """Final decision intelligence report produced by Athena."""

    question: str
    answerable: bool = True
    tldr: str
    findings: list[Finding] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)


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
