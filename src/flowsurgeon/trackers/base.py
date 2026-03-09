from __future__ import annotations

from abc import ABC, abstractmethod


class QueryTracker(ABC):
    """Abstract base class for database query trackers.

    Implementations hook into a specific DB layer (DB-API 2.0, SQLAlchemy,
    etc.) and append :class:`~flowsurgeon.core.records.QueryRecord` objects
    to the current request's query list via the shared context variable.

    Lifecycle
    ---------
    ``install()`` is called once when the middleware starts up (or is
    instantiated).  ``uninstall()`` is called on shutdown / close.
    The tracker is active for the lifetime of the process; per-request
    scoping is handled by the context variable in
    :mod:`flowsurgeon.trackers.context`.
    """

    @abstractmethod
    def install(self) -> None:
        """Set up hooks (event listeners, monkey-patches, etc.)."""

    @abstractmethod
    def uninstall(self) -> None:
        """Remove all hooks installed by :meth:`install`."""
