from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class QueryRecord:
    """Captured data for a single database query."""

    sql: str = ""
    params: str | None = None  # str repr of original params tuple/dict
    duration_ms: float = 0.0
    stack_trace: str | None = None


@dataclass
class RequestRecord:
    """Captured data for a single HTTP request."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    method: str = ""
    path: str = ""
    query_string: str = ""
    status_code: int = 0
    duration_ms: float = 0.0
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    client_host: str = ""
    queries: list[QueryRecord] = field(default_factory=list)
