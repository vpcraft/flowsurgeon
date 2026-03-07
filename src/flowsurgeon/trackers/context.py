from __future__ import annotations

from contextvars import ContextVar, Token

from flowsurgeon.core.records import QueryRecord

# One ContextVar is enough for both ASGI (per-task) and WSGI (per-thread copy).
# When set to None no queries are collected; the middleware sets it to a fresh
# list at the start of every profiled request.
_current_queries: ContextVar[list[QueryRecord] | None] = ContextVar(
    "flowsurgeon_current_queries", default=None
)


def begin_query_collection() -> tuple[list[QueryRecord], Token]:
    """Start collecting queries for the current request.

    Returns the new list and the reset token so the caller can restore the
    previous state afterwards.
    """
    queries: list[QueryRecord] = []
    token = _current_queries.set(queries)
    return queries, token


def end_query_collection(token: Token) -> None:
    """Restore the context var to its previous state (always call in finally)."""
    _current_queries.reset(token)


def get_current_queries() -> list[QueryRecord] | None:
    """Return the active query list, or None if outside a profiled request."""
    return _current_queries.get()
