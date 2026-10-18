"""B1 Baseline: Plain LLM given dataset schema + sample rows writing Python code."""

import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from athena.llm.base import LLMClient
from athena.logging import get_logger

logger = get_logger(__name__)


def _extract_code(text: str) -> str:
    """Extract Python code from markdown code block or plain text."""
    match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


async def run_b1_baseline(
    question: str,
    dataset_path: str,
    llm_client: LLMClient,
) -> dict[str, Any]:
    """Execute B1 baseline: LLM generates standalone code that is executed in sandbox."""
    start_time = time.time()
    path = Path(dataset_path)
    df = pd.read_csv(path)

    schema_info = {col: str(dtype) for col, dtype in df.dtypes.items()}
    sample_rows = df.head(3).to_dict(orient="records")

    prompt = (
        f"You are a Python data science assistant.\n"
        f"Dataset: '{path.name}'\n"
        f"Columns: {schema_info}\n"
        f"Sample rows:\n{sample_rows}\n\n"
        f"User Question: {question}\n\n"
        f"Write a Python script that loads dataset from variable `dataset_path`, "
        f"computes the exact answer, and assigns it to a global variable named `result`.\n"
        f"If the question asks for something missing or impossible to answer from this data, "
        f"assign `result = {{'answerable': False}}`.\n"
        f"Output ONLY executable Python code inside a ```python ``` block."
    )

    messages = [
        {"role": "system", "content": "You are an expert Python data analyst."},
        {"role": "user", "content": prompt},
    ]

    llm_res = await llm_client.chat(messages=messages)
    raw_code = _extract_code(llm_res.content or "")

    restricted_globals: dict[str, Any] = {
        "pd": pd,
        "np": np,
        "dataset_path": str(path.resolve()),
        "result": None,
    }

    execution_error = None
    try:
        # Execute code in restricted environment
        exec(raw_code, restricted_globals)  # noqa: S102
        raw_result = restricted_globals.get("result")
    except Exception as exc:
        execution_error = str(exc)
        raw_result = None

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "system": "B1",
        "question": question,
        "raw_result": raw_result,
        "error": execution_error,
        "tokens": llm_res.usage.total_tokens,
        "runtime_ms": round(elapsed_ms, 2),
    }
