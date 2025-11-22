import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    """Represents a single trace event."""

    event_id: str
    timestamp: float = Field(default_factory=time.time)
    agent_id: str
    event_type: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class TraceLogger:
    """
    Simple logger for emitting trace events.
    For MVP, this prints to stdout or appends to a file.
    """

    def __init__(self, output_file: Optional[str] = None):
        self.output_file = output_file

    def log(
        self,
        agent_id: str,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        event = TraceEvent(
            event_id=f"{agent_id}-{time.time_ns()}",
            agent_id=agent_id,
            event_type=event_type,
            payload=payload,
            metadata=metadata,
        )

        json_str = event.model_dump_json()

        # Always print to stdout for MVP visibility
        print(f"[TRACE] {json_str}")

        if self.output_file:
            with open(self.output_file, "a") as f:
                f.write(json_str + "\n")
