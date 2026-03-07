from __future__ import annotations

import time
import traceback
from typing import Any

from flowsurgeon.core.records import QueryRecord
from flowsurgeon.trackers.base import QueryTracker
from flowsurgeon.trackers.context import get_current_queries


class DBAPITracker(QueryTracker):
    """Query tracker for DB-API 2.0 connections.

    Because many DB-API connection types (including ``sqlite3.Connection``)
    are C-extension objects whose attributes are read-only, this tracker does
    **not** monkey-patch the connection object.  Instead it exposes a
    transparent proxy via :attr:`connection` that you use in place of the
    original connection.  Every ``cursor().execute(...)`` call through the
    proxy is timed and recorded into the active request context.

    ``install()`` / ``uninstall()`` are no-ops; tracking is always active
    through the proxy (but only recorded when a request context is active).

    Parameters
    ----------
    connection:
        A DB-API 2.0 connection object (e.g. ``sqlite3.connect(...)``).
    capture_stacktrace:
        When True, attach a stack trace to every :class:`QueryRecord`.

    Example
    -------
    ::

        import sqlite3
        from flowsurgeon import FlowSurgeon, Config
        from flowsurgeon.trackers import DBAPITracker

        _raw = sqlite3.connect("mydb.db")
        tracker = DBAPITracker(_raw)
        # Use tracker.connection everywhere instead of _raw.

        app = FlowSurgeon(wsgi_app, config=Config(enabled=True), trackers=[tracker])
    """

    def __init__(self, connection: Any, *, capture_stacktrace: bool = False) -> None:
        self.connection: _TrackedConnection = _TrackedConnection(
            connection, capture_stacktrace=capture_stacktrace
        )

    def install(self) -> None:
        pass  # tracking is via self.connection; no global hooks needed

    def uninstall(self) -> None:
        pass


class _TrackedConnection:
    """Transparent proxy around a DB-API 2.0 connection that yields instrumented cursors."""

    __slots__ = ("_conn", "_capture_stacktrace")

    def __init__(self, conn: Any, *, capture_stacktrace: bool = False) -> None:
        object.__setattr__(self, "_conn", conn)
        object.__setattr__(self, "_capture_stacktrace", capture_stacktrace)

    def cursor(self, *args: Any, **kwargs: Any) -> _InstrumentedCursor:
        conn = object.__getattribute__(self, "_conn")
        capture = object.__getattribute__(self, "_capture_stacktrace")
        return _InstrumentedCursor(conn.cursor(*args, **kwargs), capture_stacktrace=capture)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_conn"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, "_conn"), name, value)


class _InstrumentedCursor:
    """Thin wrapper around a DB-API 2.0 cursor that records queries."""

    __slots__ = ("_cursor", "_capture_stacktrace")

    def __init__(self, cursor: Any, *, capture_stacktrace: bool = False) -> None:
        object.__setattr__(self, "_cursor", cursor)
        object.__setattr__(self, "_capture_stacktrace", capture_stacktrace)

    # ------------------------------------------------------------------
    # Instrumented methods
    # ------------------------------------------------------------------

    def execute(self, sql: str, parameters: Any = None) -> Any:
        return self._run(sql, parameters, many=False)

    def executemany(self, sql: str, parameters: Any = None) -> Any:
        return self._run(sql, parameters, many=True)

    def _run(self, sql: str, parameters: Any, *, many: bool) -> Any:
        queries = get_current_queries()
        t0 = time.perf_counter()
        try:
            cursor = object.__getattribute__(self, "_cursor")
            if parameters is None:
                return cursor.executemany(sql) if many else cursor.execute(sql)
            return cursor.executemany(sql, parameters) if many else cursor.execute(sql, parameters)
        finally:
            duration_ms = (time.perf_counter() - t0) * 1000
            if queries is not None:
                stack: str | None = None
                if object.__getattribute__(self, "_capture_stacktrace"):
                    stack = "".join(traceback.format_stack()[:-2])
                queries.append(
                    QueryRecord(
                        sql=sql,
                        params=repr(parameters) if parameters is not None else None,
                        duration_ms=duration_ms,
                        stack_trace=stack,
                    )
                )

    # ------------------------------------------------------------------
    # Transparent delegation for everything else
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_cursor"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, "_cursor"), name, value)

    def __iter__(self):
        return iter(object.__getattribute__(self, "_cursor"))
