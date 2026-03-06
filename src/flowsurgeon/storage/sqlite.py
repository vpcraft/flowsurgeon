from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone

from flowsurgeon.core.records import RequestRecord
from flowsurgeon.storage.base import StorageBackend

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS requests (
    request_id   TEXT PRIMARY KEY,
    timestamp    TEXT NOT NULL,
    method       TEXT NOT NULL,
    path         TEXT NOT NULL,
    query_string TEXT NOT NULL DEFAULT '',
    status_code  INTEGER NOT NULL DEFAULT 0,
    duration_ms  REAL NOT NULL DEFAULT 0.0,
    client_host  TEXT NOT NULL DEFAULT '',
    req_headers  TEXT NOT NULL DEFAULT '{}',
    resp_headers TEXT NOT NULL DEFAULT '{}'
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests (timestamp DESC);
"""


class SQLiteBackend(StorageBackend):
    """Thread-safe SQLite storage backend.

    Uses a per-thread connection and WAL journal mode for better
    concurrent read performance.
    """

    def __init__(self, db_path: str = "flowsurgeon.db") -> None:
        self._db_path = db_path
        self._local = threading.local()
        # Initialise the schema using a short-lived connection so the
        # tables exist before any thread starts writing.
        conn = self._connect()
        conn.execute(_CREATE_TABLE)
        conn.execute(_CREATE_INDEX)
        conn.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        if not getattr(self._local, "conn", None):
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn  # type: ignore[return-value]

    @property
    def _conn(self) -> sqlite3.Connection:
        return self._connect()

    # ------------------------------------------------------------------
    # StorageBackend interface
    # ------------------------------------------------------------------

    def save(self, record: RequestRecord) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO requests
                (request_id, timestamp, method, path, query_string,
                 status_code, duration_ms, client_host, req_headers, resp_headers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.request_id,
                record.timestamp.isoformat(),
                record.method,
                record.path,
                record.query_string,
                record.status_code,
                record.duration_ms,
                record.client_host,
                json.dumps(record.request_headers),
                json.dumps(record.response_headers),
            ),
        )
        self._conn.commit()

    def get(self, request_id: str) -> RequestRecord | None:
        row = self._conn.execute(
            "SELECT * FROM requests WHERE request_id = ?", (request_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def list_recent(self, limit: int = 50) -> list[RequestRecord]:
        rows = self._conn.execute(
            "SELECT * FROM requests ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_record(r) for r in rows]

    def prune(self, keep: int) -> None:
        self._conn.execute(
            """
            DELETE FROM requests
            WHERE request_id NOT IN (
                SELECT request_id FROM requests
                ORDER BY timestamp DESC
                LIMIT ?
            )
            """,
            (keep,),
        )
        self._conn.commit()

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None


def _row_to_record(row: sqlite3.Row) -> RequestRecord:
    return RequestRecord(
        request_id=row["request_id"],
        timestamp=datetime.fromisoformat(row["timestamp"]).replace(tzinfo=timezone.utc),
        method=row["method"],
        path=row["path"],
        query_string=row["query_string"],
        status_code=row["status_code"],
        duration_ms=row["duration_ms"],
        client_host=row["client_host"],
        request_headers=json.loads(row["req_headers"]),
        response_headers=json.loads(row["resp_headers"]),
    )
