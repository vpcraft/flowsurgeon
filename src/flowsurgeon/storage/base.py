from __future__ import annotations

from abc import ABC, abstractmethod

from flowsurgeon.core.records import RequestRecord


class StorageBackend(ABC):
    """Abstract base class for FlowSurgeon storage backends."""

    @abstractmethod
    def save(self, record: RequestRecord) -> None:
        """Persist a request record."""

    @abstractmethod
    def get(self, request_id: str) -> RequestRecord | None:
        """Retrieve a single record by its ID, or None if not found."""

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[RequestRecord]:
        """Return up to *limit* most recent records, newest first."""

    @abstractmethod
    def prune(self, keep: int) -> None:
        """Delete oldest records so that at most *keep* records remain."""

    @abstractmethod
    def close(self) -> None:
        """Release any resources held by this backend."""
