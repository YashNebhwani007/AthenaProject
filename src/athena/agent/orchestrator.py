"""Core orchestrator executing the autonomous analytical tool-calling loop."""

import argparse
import asyncio
import json
import re
import uuid
from pathlib import Path
from typing import Any

from athena.agent.budget import Budget, BudgetExhausted
from athena.agent.prompts import (
    SYSTEM_PROMPT,
    build_context_message,
    build_tool_schemas,
)
from athena.config import Settings
from athena.config import settings as global_settings
from athena.data import DatasetRegistry, default_registry
from athena.llm import LLMClient, create_llm_client
from athena.logging import get_logger
from athena.render.renderer import resolve_placeholders
from athena.schemas import (
    EventType,
    Report,
    RunResult,
    ToolResult,
    ToolStatus,
)
from athena.tools import TOOL_REGISTRY
from athena.tools.profile import profile_dataset
from athena.verify.verifier import Verifier

logger = get_logger(__name__)


def parse_report_from_text(content: str | None, question: str) -> Report:
    """Extract and validate Report JSON from raw LLM output text."""
    if not content or not content.strip():
        return Report(
            question=question,
            answerable=False,
            tldr="No final analytical response was provided by the agent.",
            findings=[],
            caveats=["LLM produced empty content."],
            recommendations=[],
        )

    text = content.strip()
    # Strip markdown json codeblock if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()

    try:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start_brace = text.find("{")
            end_brace = text.rfind("}")
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                data = json.loads(text[start_brace : end_brace + 1])
            else:
                raise
        rep = Report.model_validate(data)
        if not rep.question:
            rep.question = question
        return rep
    except Exception as exc:
        logger.warning("report_json_parse_fallback", error=str(exc))
        return Report(
            question=question,
            answerable=True,
            tldr=content[:300].strip(),
            findings=[],
            caveats=[f"Final report draft did not conform strictly to JSON schema: {exc}"],
            recommendations=[],
        )


class Orchestrator:
    """Autonomous agent orchestrator executing evidence-backed data science workflows."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        registry: DatasetRegistry | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        self.settings = app_settings or global_settings
        self.registry = registry or default_registry
        self.llm = llm_client or create_llm_client(self.settings)
        self.tool_schemas = build_tool_schemas()

    async def run(
        self,
        question: str,
        dataset_id: str,
        session_id: str | None = None,
        event_callback: Any = None,
    ) -> RunResult:
        """Run end-to-end analytical orchestration loop on dataset for a user question."""
        run_id = f"run_{uuid.uuid4().hex[:10]}"
        sess_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        budget = Budget(app_settings=self.settings)
        trace: list[ToolResult] = []
        total_tokens = 0

        async def _emit(ev_type: EventType, data: dict[str, Any]) -> None:
            if event_callback:
                payload = {"event": ev_type.value, "data": data}
                if asyncio.iscoroutinefunction(event_callback):
                    await event_callback(payload)
                elif callable(event_callback):
                    event_callback(payload)

        handle = self.registry.get(dataset_id)

        # 1. Automatic Initial Profiling
        logger.info("orchestrator_initial_profiling", dataset_id=dataset_id)
        profile_res = await profile_dataset(dataset_id=dataset_id, registry=self.registry)
        trace.append(profile_res)
        budget.record_tool_call(1)
        await _emit(EventType.tool_result, profile_res.model_dump())

        # 2. Build initial conversation prompt
        context_msg = build_context_message(handle, profile_res)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{context_msg}\n\n---\nUser Question: {question}",
            },
        ]

        recent_calls: list[str] = []
        final_content: str | None = None

        # 3. Autonomous Tool-Calling Loop
        while True:
            try:
                budget.record_step(1)
            except BudgetExhausted as exc:
                logger.warning("budget_exhausted_halting_loop", reason=str(exc))
                break

            response = await self.llm.chat(
                messages=messages,
                tools=self.tool_schemas,
                seed=self.settings.llm_seed,
            )

            total_tokens += response.usage.total_tokens
            try:
                budget.record_tokens(response.usage.total_tokens)
            except BudgetExhausted as exc:
                logger.warning("token_budget_exhausted", reason=str(exc))
                final_content = response.content
                break

            # If tool calls were made
            if response.tool_calls:
                # Append assistant message to chat history
                tool_calls_payload = []
                for tc in response.tool_calls:
                    tc_dict: dict[str, Any] = {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    if tc.extra_content:
                        tc_dict["extra_content"] = tc.extra_content
                    tool_calls_payload.append(tc_dict)

                asst_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": tool_calls_payload,
                }
                if response.extra_content:
                    asst_msg["extra_content"] = response.extra_content
                messages.append(asst_msg)

                for tc in response.tool_calls:
                    call_sig = f"{tc.name}:{json.dumps(tc.arguments, sort_keys=True)}"
                    recent_calls.append(call_sig)
                    # Loop detection: check if identical call was repeated 3+ times
                    if len(recent_calls) >= 3 and len(set(recent_calls[-3:])) == 1:
                        logger.warning("tool_loop_detected", call=call_sig)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps(
                                    {
                                        "error": (
                                            "Loop detected: Tool call repeated 3 times. "
                                            "Synthesize your findings and output final Report JSON."
                                        )
                                    }
                                ),
                            }
                        )
                        continue

                    try:
                        budget.record_tool_call(1)
                    except BudgetExhausted as exc:
                        logger.warning("tool_call_budget_exhausted", reason=str(exc))
                        break

                    # Dispatch tool
                    tool_func = TOOL_REGISTRY.get(tc.name)
                    if not tool_func:
                        err_res = ToolResult(
                            id=f"err_{tc.id}",
                            tool=tc.name,
                            status=ToolStatus.error,
                            warnings=[f"Tool '{tc.name}' not found in registry."],
                        )
                        trace.append(err_res)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps(
                                    {"error": f"Tool '{tc.name}' not recognized."}
                                ),
                            }
                        )
                        continue

                    kwargs = dict(tc.arguments)
                    # Robustly normalize dataset_id if model used table name or omitted it
                    if "dataset_id" in kwargs:
                        cand = kwargs["dataset_id"]
                        if cand not in self.registry:
                            if cand.startswith("tbl_") and cand[4:] in self.registry:
                                kwargs["dataset_id"] = cand[4:]
                            elif dataset_id in self.registry:
                                kwargs["dataset_id"] = dataset_id
                    else:
                        kwargs["dataset_id"] = dataset_id

                    # Inject registry
                    kwargs["registry"] = self.registry

                    try:
                        tool_res = await tool_func(**kwargs)
                    except Exception as exc:
                        tool_res = ToolResult(
                            id=f"err_{tc.id}",
                            tool=tc.name,
                            status=ToolStatus.error,
                            warnings=[f"Execution failed: {exc}"],
                        )

                    trace.append(tool_res)
                    await _emit(EventType.tool_result, tool_res.model_dump())
                    payload_out = (
                        tool_res.output if tool_res.output is not None else tool_res.warnings
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(payload_out),
                        }
                    )

            # Check if LLM produced final response
            if response.is_final or not response.tool_calls:
                final_content = response.content
                break

        # 4. Parse draft report
        draft_report = parse_report_from_text(final_content, question)
        await _emit(EventType.report_draft, {"report": draft_report.model_dump()})

        # 5. Full verifier execution with repair loop
        verifier = Verifier(app_settings=self.settings)
        verified_report, verification = await verifier.verify(
            report=draft_report,
            tool_results=trace,
            llm_client=self.llm,
        )
        await _emit(EventType.verification, {"summary": verification.model_dump()})

        # 6. Resolve placeholders in final report
        final_report = resolve_placeholders(verified_report, trace)

        run_result = RunResult(
            run_id=run_id,
            session_id=sess_id,
            question=question,
            report=final_report,
            verification=verification,
            trace=trace,
            total_steps=budget.steps,
            total_tokens=total_tokens,
            total_runtime_ms=round(budget.elapsed_seconds * 1000, 2),
        )
        await _emit(
            EventType.final,
            {
                "run_id": run_id,
                "report": final_report.model_dump(),
                "run_result": run_result.model_dump(),
            },
        )

        return run_result


async def main() -> None:
    """CLI entry point for Athena orchestrator."""
    parser = argparse.ArgumentParser(description="Athena Autonomous Data Science Agent")
    parser.add_argument("--dataset", required=True, help="Path to CSV/Parquet dataset file")
    parser.add_argument("--question", required=True, help="Analytical question in natural language")
    args = parser.parse_args()

    reg = DatasetRegistry()
    dataset_path = Path(args.dataset)
    handle = reg.register(dataset_id="cli_dataset", file_path=dataset_path)

    orchestrator = Orchestrator(registry=reg)
    result = await orchestrator.run(question=args.question, dataset_id=handle.dataset_id)

    print(json.dumps(result.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
