from __future__ import annotations

import time
import traceback
import threading
from typing import Any

from flowsurgeon.core.records import QueryRecord
from flowsurgeon.trackers.base import QueryTracker
from flowsurgeon.trackers.context import get_current_queries


class SQLAlchemyTracker(QueryTracker):
    """Query tracker that hooks into a SQLAlchemy engine via engine events.

    Uses ``before_cursor_execute`` / ``after_cursor_execute`` events to time
    every statement executed through the given engine.

    Parameters
    ----------
    engine:
        A ``sqlalchemy.engine.Engine`` instance.
    capture_stacktrace:
        When True, capture a stack trace for every query.

    Example
    -------
    ::

        from sqlalchemy import create_engine
        from flowsurgeon import FlowSurgeon, Config
        from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

        engine = create_engine("sqlite:///mydb.db")
        tracker = SQLAlchemyTracker(engine)

        app = FlowSurgeon(asgi_app, config=Config(enabled=True), trackers=[tracker])

    .. note::
        ``sqlalchemy`` is not a required dependency of FlowSurgeon.
        Install it separately: ``pip install sqlalchemy``.
    """

    def __init__(self, engine: Any, *, capture_stacktrace: bool = False) -> None:
        self._engine = engine
        self._capture_stacktrace = capture_stacktrace
        # Per-thread start-time storage (handles both sync and async via thread pool)
        self._t0: threading.local = threading.local()

    def install(self) -> None:
        try:
            from sqlalchemy import event
        except ImportError as exc:
            raise ImportError(
                "SQLAlchemyTracker requires sqlalchemy. Install it with: pip install sqlalchemy"
            ) from exc

        event.listen(self._engine, "before_cursor_execute", self._before_execute, retval=False)
        event.listen(self._engine, "after_cursor_execute", self._after_execute)

    def uninstall(self) -> None:
        try:
            from sqlalchemy import event
        except ImportError:
            return

        if event.contains(self._engine, "before_cursor_execute", self._before_execute):
            event.remove(self._engine, "before_cursor_execute", self._before_execute)
        if event.contains(self._engine, "after_cursor_execute", self._after_execute):
            event.remove(self._engine, "after_cursor_execute", self._after_execute)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _before_execute(
        self, conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        self._t0.value = time.perf_counter()

    def _after_execute(
        self, conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        t0 = getattr(self._t0, "value", None)
        duration_ms = (time.perf_counter() - t0) * 1000 if t0 is not None else 0.0

        queries = get_current_queries()
        if queries is None:
            return

        stack: str | None = None
        if self._capture_stacktrace:
            stack = "".join(traceback.format_stack()[:-2])

        queries.append(
            QueryRecord(
                sql=statement,
                params=repr(parameters) if parameters is not None else None,
                duration_ms=duration_ms,
                stack_trace=stack,
            )
        )
