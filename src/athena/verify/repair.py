"""Verifier repair loop helpers per Task 4.2."""

import json
import re

from athena.logging import get_logger
from athena.schemas import Report, VerificationResult

logger = get_logger(__name__)


def build_repair_message(failures: list[VerificationResult]) -> str:
    """Construct structured instruction message asking LLM to correct report violations."""
    lines = [
        "The automated verification engine found the following issues in your draft report:",
    ]
    for idx, f in enumerate(failures, start=1):
        target = f"Finding '{f.finding_id}'" if f.finding_id else "Report structure"
        lines.append(f"{idx}. [{f.rule}] {target}: {f.issue}")
        if f.suggestion:
            lines.append(f"   Suggestion: {f.suggestion}")

    lines.append(
        "\nPlease provide a corrected, complete Report JSON conforming strictly "
        "to the Report schema. Ensure all cited metrics, directions, causal claims, "
        "and data caveats are properly addressed."
    )
    return "\n".join(lines)


def parse_repaired_report(content: str) -> Report:
    """Extract and validate corrected Report JSON from LLM response content."""
    text = content.strip()
    # Extract JSON code fence if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()

    data = json.loads(text)
    return Report.model_validate(data)
