from __future__ import annotations

import asyncio

from flowsurgeon.core.records import RequestRecord
from flowsurgeon.storage.sqlite import SQLiteBackend


class AsyncSQLiteBackend:
    """Async-safe SQLite backend using an asyncio queue + background writer task.

    Reads (``get``, ``list_recent``) are executed in a thread pool via
    ``asyncio.to_thread`` so they never block the event loop.  Writes are
    enqueued and flushed by a single background coroutine, which serialises
    all mutations and avoids write contention.
    """

    def __init__(self, db_path: str = "flowsurgeon.db") -> None:
        self._sync = SQLiteBackend(db_path)
        self._queue: asyncio.Queue[tuple[RequestRecord, int] | None] = asyncio.Queue()
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
        if self._task and not self._task.done():
            await self._queue.put(None)  # sentinel
            await self._task
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
            if item is None:
                self._queue.task_done()
                break
            record, max_stored = item
            try:
                await asyncio.to_thread(self._sync.save, record)
                await asyncio.to_thread(self._sync.prune, max_stored)
            except Exception:
                pass  # don't crash the writer; errors logged by caller if needed
            finally:
                self._queue.task_done()
