"""Server-Sent Events (SSE) serialization and streaming helpers per Task 6.1."""

import json
from typing import Any

from athena.schemas import EventType


def format_sse_message(event_type: EventType | str, data: dict[str, Any]) -> dict[str, Any]:
    """Format dictionary into an SSE event source dict payload."""
    event_name = event_type.value if isinstance(event_type, EventType) else str(event_type)
    return {
        "event": event_name,
        "data": json.dumps(data, default=str),
    }
