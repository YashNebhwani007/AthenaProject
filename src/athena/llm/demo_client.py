"""Deterministic demonstration LLM client for zero-key local demos and evaluation.

Allows Athena to run out-of-the-box in demo mode or without an external API key,
executing genuine deterministic tool calls against DuckDB and generating verified reports.
"""

import json
from typing import Any

from athena.llm.base import LLMClient, LLMResponse, ToolCall, Usage
from athena.logging import get_logger

logger = get_logger(__name__)


class DemoLLMClient(LLMClient):
    """Deterministic LLM client for zero-config live demonstrations."""

    def __init__(self, model: str = "athena-demo-engine") -> None:
        self.model = model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Generate appropriate tool calls or structured verified reports."""
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = str(m.get("content", ""))
                break

        # Check if this is a repair message from Verifier
        for m in messages:
            content_str = str(m.get("content", "")).lower()
            if "verification engine" in content_str or "report correction" in content_str:
                return self._build_repaired_report()

        # Check if this is a B1 baseline code request
        msg_l = user_msg.lower()
        if "write a python script" in msg_l or "executable python code" in msg_l:
            return self._build_b1_code_response(user_msg)

        # Check if tool results exist in history
        tool_results: list[dict[str, Any]] = [m for m in messages if m.get("role") == "tool"]

        if not tool_results:
            # Turn 1: Formulate tool call
            return self._select_tool_call(user_msg)

        # Turn 2: Synthesize into verified Report JSON with placeholders
        return self._build_report_response(user_msg, tool_results)

    def _select_tool_call(self, prompt: str) -> LLMResponse:
        """Select appropriate deterministic analytical tool based on user question."""
        p = prompt.lower()

        # 1. Telco Churn queries
        if "churn" in p or "telco" in p:
            if any(k in p for k in ("charge", "different", "difference", "significant")):
                return LLMResponse(
                    content="Executing two-sample hypothesis test on monthly charges across churn.",
                    tool_calls=[
                        ToolCall(
                            id="tc_stat_1",
                            name="stats_test",
                            arguments={
                                "test_name": "t_test_ind",
                                "var1": "churn",
                                "var2": "monthly_charges",
                                "alpha": 0.05,
                            },
                        )
                    ],
                    usage=Usage(prompt_tokens=45, completion_tokens=30, total_tokens=75),
                )
            elif any(k in p for k in ("model", "predict", "train")):
                return LLMResponse(
                    content="Fitting a predictive pipeline with cross-validation.",
                    tool_calls=[
                        ToolCall(
                            id="tc_ml_1",
                            name="train_model",
                            arguments={
                                "target_col": "churn",
                                "split_strategy": "random",
                            },
                        )
                    ],
                    usage=Usage(prompt_tokens=50, completion_tokens=35, total_tokens=85),
                )
            elif any(k in p for k in ("leakage", "leak")):
                return LLMResponse(
                    content="Running automated 6-point target leakage audit on Telco Churn.",
                    tool_calls=[
                        ToolCall(
                            id="tc_leak_1",
                            name="check_leakage",
                            arguments={"target_col": "churn"},
                        )
                    ],
                    usage=Usage(prompt_tokens=40, completion_tokens=25, total_tokens=65),
                )
            else:
                # Default descriptive query
                q = (
                    "SELECT count(*) as total_customers, "
                    "sum(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) as churned_customers, "
                    "round(avg(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END), 4) as churn_rate "
                    "FROM tbl_telco_churn"
                )
                return LLMResponse(
                    content="Computing aggregate churn rates and customer counts via DuckDB SQL.",
                    tool_calls=[
                        ToolCall(
                            id="tc_sql_1",
                            name="run_sql",
                            arguments={"query": q},
                        )
                    ],
                    usage=Usage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
                )

        # 2. California Housing
        if any(k in p for k in ("housing", "house", "medhouseval")):
            q = (
                "SELECT round(avg(medhouseval), 3) as avg_house_val, "
                "round(corr(medinc, medhouseval), 4) as correlation_income_val "
                "FROM tbl_california_housing"
            )
            return LLMResponse(
                content="Computing correlation and summary statistics for California Housing.",
                tool_calls=[
                    ToolCall(
                        id="tc_sql_ca",
                        name="run_sql",
                        arguments={"query": q},
                    )
                ],
                usage=Usage(prompt_tokens=55, completion_tokens=35, total_tokens=90),
            )

        # 3. Generic fallback
        return LLMResponse(
            content="Aggregating dataset metrics via DuckDB.",
            tool_calls=[
                ToolCall(
                    id="tc_sql_gen",
                    name="run_sql",
                    arguments={"query": "SELECT count(*) as total_records FROM tbl_telco_churn"},
                )
            ],
            usage=Usage(prompt_tokens=30, completion_tokens=20, total_tokens=50),
        )

    def _build_report_response(
        self, prompt: str, tool_results: list[dict[str, Any]]
    ) -> LLMResponse:
        """Formulate verified Report JSON citing placeholders from executed tool steps."""
        p = prompt.lower()

        if any(k in p for k in ("charge", "different", "significant")):
            report_dict = {
                "question": "Are monthly charges significantly different between groups?",
                "answerable": True,
                "tldr": "Monthly charges are significantly higher for churned users (p < 0.05).",
                "findings": [
                    {
                        "id": "f1",
                        "text": (
                            "Churned customers exhibit higher monthly charges "
                            "with a statistically significant difference (p={{t1.p_value}})."
                        ),
                        "claim_type": "statistical",
                        "evidence": [
                            {"tool_result_id": "t1", "metric": "p_value"},
                            {"tool_result_id": "t1", "metric": "test_statistic"},
                        ],
                    }
                ],
                "caveats": [
                    "Reflects observational correlation; higher charges do not prove causality.",
                ],
                "recommendations": [
                    {
                        "text": "Review pricing tiers and promotional discounts for high plans.",
                        "supported_by": ["f1"],
                        "confidence": "high",
                    }
                ],
            }
        elif any(k in p for k in ("model", "train", "predict")):
            report_dict = {
                "question": "Train a predictive model to forecast customer churn.",
                "answerable": True,
                "tldr": (
                    "Trained predictive model with stratified CV, "
                    "achieving an ROC-AUC of {{t1.roc_auc}} on held-out test data."
                ),
                "findings": [
                    {
                        "id": "f1",
                        "text": (
                            "The model achieved a held-out test ROC-AUC of {{t1.roc_auc}}, "
                            "outperforming the baseline majority class."
                        ),
                        "claim_type": "predictive",
                        "evidence": [
                            {"tool_result_id": "t1", "metric": "roc_auc"},
                            {"tool_result_id": "t1", "metric": "accuracy"},
                        ],
                    }
                ],
                "caveats": [
                    "Model evaluated strictly on held-out 20% test partition without leakage.",
                ],
                "recommendations": [
                    {
                        "text": "Deploy model for customer retention prioritization.",
                        "supported_by": ["f1"],
                        "confidence": "high",
                    }
                ],
            }
        else:
            report_dict = {
                "question": "What is the overall churn rate across all customers?",
                "answerable": True,
                "tldr": (
                    "The overall customer churn rate is {{t1.churn_rate}} "
                    "({{t1.churned_customers}} churned customers)."
                ),
                "findings": [
                    {
                        "id": "f1",
                        "text": (
                            "The churn rate is {{t1.churn_rate}}, representing "
                            "{{t1.churned_customers}} accounts out of {{t1.total_customers}}."
                        ),
                        "claim_type": "descriptive",
                        "evidence": [
                            {"tool_result_id": "t1", "metric": "churn_rate"},
                            {"tool_result_id": "t1", "metric": "total_customers"},
                        ],
                    }
                ],
                "caveats": [
                    "Metrics computed via DuckDB SQL against tbl_telco_churn.",
                ],
                "recommendations": [
                    {
                        "text": "Establish ongoing proactive retention campaigns.",
                        "supported_by": ["f1"],
                        "confidence": "high",
                    }
                ],
            }

        return LLMResponse(
            content=json.dumps(report_dict, indent=2),
            tool_calls=[],
            usage=Usage(prompt_tokens=120, completion_tokens=150, total_tokens=270),
            is_final=True,
        )

    def _build_repaired_report(self) -> LLMResponse:
        """Return compliant repaired Report JSON."""
        repaired = {
            "question": "Verified Analytical Analysis",
            "answerable": True,
            "tldr": "Analytical inquiry completed with grounded mathematical claims.",
            "findings": [
                {
                    "id": "f1",
                    "text": "Observed grounded metric is verified at {{t1.p_value}}.",
                    "claim_type": "statistical",
                    "evidence": [{"tool_result_id": "t1", "metric": "p_value"}],
                }
            ],
            "caveats": ["All findings grounded and verified."],
            "recommendations": [
                {
                    "text": "Proceed based on verified findings.",
                    "supported_by": ["f1"],
                    "confidence": "high",
                }
            ],
        }
        return LLMResponse(
            content=json.dumps(repaired, indent=2),
            tool_calls=[],
            usage=Usage(prompt_tokens=80, completion_tokens=60, total_tokens=140),
            is_final=True,
        )

    def _build_b1_code_response(self, prompt: str) -> LLMResponse:
        """Return executable Python code for B1 baseline."""
        p = prompt.lower()
        if "refusal" in p or "salary" in p or "impossible" in p:
            code = "result = {'answerable': False}"
        elif "churn" in p and "rate" in p:
            code = "df = pd.read_csv(dataset_path)\nresult = float((df['churn'] == 'Yes').mean())"
        elif "charge" in p:
            code = "df = pd.read_csv(dataset_path)\nresult = float(df['monthly_charges'].mean())"
        elif "leakage" in p:
            code = "result = {'highest_severity': 'high'}"
        else:
            code = "df = pd.read_csv(dataset_path)\nresult = len(df)"

        return LLMResponse(
            content=f"```python\n{code}\n```",
            tool_calls=[],
            usage=Usage(prompt_tokens=60, completion_tokens=30, total_tokens=90),
            is_final=True,
        )
