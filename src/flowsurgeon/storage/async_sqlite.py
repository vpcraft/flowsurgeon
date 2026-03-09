from __future__ import annotations

import asyncio
import logging

from flowsurgeon.core.records import RequestRecord
from flowsurgeon.storage.sqlite import SQLiteBackend

_log = logging.getLogger(__name__)


class AsyncSQLiteBackend:
    """Async-safe SQLite backend using an asyncio queue + background writer task.

    Reads (``get``, ``list_recent``) are executed in a thread pool via
    ``asyncio.to_thread`` so they never block the event loop.  Writes are
    enqueued and flushed by a single background coroutine, which serialises
    all mutations and avoids write contention.
    """

    def __init__(self, db_path: str = "flowsurgeon.db") -> None:
        self._sync = SQLiteBackend(db_path)
        self._queue: asyncio.Queue[tuple[RequestRecord, int]] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background writer task (idempotent)."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._writer_loop(), name="flowsurgeon-writer")

    async def close(self) -> None:
        """Drain the queue and shut down the background writer."""
        if self._task is not None and not self._task.done():
            # Wait for every already-enqueued item to be processed, then cancel
            # the idle writer. Using queue.join() is race-free: new items
            # enqueued concurrently will be counted and waited for too.
            await self._queue.join()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await asyncio.to_thread(self._sync.close)

    # ------------------------------------------------------------------
    # Write path (async, non-blocking)
    # ------------------------------------------------------------------

    async def enqueue(self, record: RequestRecord, max_stored: int) -> None:
        """Enqueue a write; returns immediately without blocking the event loop."""
        await self._ensure_started()
        await self._queue.put((record, max_stored))

    # ------------------------------------------------------------------
    # Read path (offloaded to thread pool)
    # ------------------------------------------------------------------

    async def get(self, request_id: str) -> RequestRecord | None:
        return await asyncio.to_thread(self._sync.get, request_id)

    async def list_recent(self, limit: int = 50) -> list[RequestRecord]:
        return await asyncio.to_thread(self._sync.list_recent, limit)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _ensure_started(self) -> None:
        if self._task is None or self._task.done():
            await self.start()

    async def _writer_loop(self) -> None:
        while True:
            item = await self._queue.get()
            record, max_stored = item
            try:
                await asyncio.to_thread(self._sync.save, record)
                await asyncio.to_thread(self._sync.prune, max_stored)
            except Exception:
                _log.exception("FlowSurgeon: error writing request record to storage")
            finally:
                self._queue.task_done()
