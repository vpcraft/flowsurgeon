"""FlowSurgeon — framework-agnostic profiling middleware for Python."""

from __future__ import annotations

import inspect

from flowsurgeon.core.config import Config
from flowsurgeon.core.records import RequestRecord
from flowsurgeon.middleware.asgi import FlowSurgeonASGI
from flowsurgeon.middleware.wsgi import FlowSurgeonWSGI
from flowsurgeon.storage.async_sqlite import AsyncSQLiteBackend
from flowsurgeon.storage.base import StorageBackend
from flowsurgeon.storage.sqlite import SQLiteBackend


def FlowSurgeon(app, *, config: Config | None = None, storage=None):
    """Auto-detect WSGI vs ASGI and wrap *app* with the appropriate middleware.

    Detection is based on whether ``app.__call__`` is a coroutine function.
    FastAPI / Starlette apps are detected as ASGI; plain WSGI callables
    (Flask, Django, etc.) are wrapped with :class:`FlowSurgeonWSGI`.
    """
    if inspect.iscoroutinefunction(app) or inspect.iscoroutinefunction(
        getattr(app, "__call__", None)
    ):
        return FlowSurgeonASGI(app, config=config, storage=storage)
    return FlowSurgeonWSGI(app, config=config, storage=storage)


__all__ = [
    "AsyncSQLiteBackend",
    "Config",
    "FlowSurgeon",
    "FlowSurgeonASGI",
    "FlowSurgeonWSGI",
    "RequestRecord",
    "SQLiteBackend",
    "StorageBackend",
]

__version__ = "0.2.0"
