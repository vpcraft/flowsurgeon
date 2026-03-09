from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """FlowSurgeon configuration.

    Parameters
    ----------
    enabled:
        Master switch. Defaults to False; can be overridden by the
        FLOWSURGEON_ENABLED environment variable.
    allowed_hosts:
        Only serve the debug panel to requests from these hosts/IPs.
        Defaults to localhost addresses only.
    db_path:
        Path to the SQLite database file used for persistence.
    max_stored_requests:
        Maximum number of request records to keep in the database.
        Older records are pruned automatically.
    debug_route:
        URL prefix for the built-in debug UI.
    strip_sensitive_headers:
        Header names whose values will be redacted before storage.
    """

    enabled: bool = field(default_factory=lambda: _env_bool("FLOWSURGEON_ENABLED", False))
    allowed_hosts: list[str] = field(default_factory=lambda: ["127.0.0.1", "::1", "localhost"])
    db_path: str = "flowsurgeon.db"
    max_stored_requests: int = 1000
    debug_route: str = "/flowsurgeon"
    strip_sensitive_headers: list[str] = field(
        default_factory=lambda: ["authorization", "cookie", "set-cookie"]
    )
    track_queries: bool = True
    capture_query_stacktrace: bool = False
    slow_query_threshold_ms: float = 100.0
    # (METHOD, path) pairs shown in the APIs view before any traffic is recorded.
    # Auto-populated by the middleware via Flask/FastAPI/Starlette route discovery.
    known_routes: list[tuple[str, str]] = field(default_factory=list)
    # Call-stack profiling (cProfile). Off by default; adds ~1-10% overhead.
    enable_profiling: bool = field(
        default_factory=lambda: _env_bool("FLOWSURGEON_PROFILING", False)
    )
    profile_top_n: int = 50  # keep top N functions by cumulative time
    profile_user_code_only: bool = True  # filter out stdlib + third-party frames


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes")
