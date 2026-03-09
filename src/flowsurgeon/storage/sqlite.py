from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone

from flowsurgeon.core.records import ProfileStat, QueryRecord, RequestRecord
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
    resp_headers TEXT NOT NULL DEFAULT '{}',
    queries      TEXT NOT NULL DEFAULT '[]',
    resp_body    TEXT,
    profile_stats TEXT
);
"""

# Migrations for databases created before current version
_ADD_QUERIES_COLUMN = "ALTER TABLE requests ADD COLUMN queries TEXT NOT NULL DEFAULT '[]'"
_ADD_RESP_BODY_COLUMN = "ALTER TABLE requests ADD COLUMN resp_body TEXT"
_ADD_PROFILE_STATS_COLUMN = "ALTER TABLE requests ADD COLUMN profile_stats TEXT"

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
        for migration in (_ADD_QUERIES_COLUMN, _ADD_RESP_BODY_COLUMN, _ADD_PROFILE_STATS_COLUMN):
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass  # column already exists
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
        queries_json = json.dumps(
            [
                {
                    "sql": q.sql,
                    "params": q.params,
                    "duration_ms": q.duration_ms,
                    "stack_trace": q.stack_trace,
                }
                for q in record.queries
            ]
        )
        profile_json = (
            json.dumps(
                [
                    {
                        "file": s.file,
                        "line": s.line,
                        "func": s.func,
                        "prim_calls": s.prim_calls,
                        "calls": s.calls,
                        "tt_ms": s.tt_ms,
                        "ct_ms": s.ct_ms,
                        "callers": s.callers,
                    }
                    for s in record.profile_stats
                ]
            )
            if record.profile_stats is not None
            else None
        )
        self._conn.execute(
            """
            INSERT OR REPLACE INTO requests
                (request_id, timestamp, method, path, query_string,
                 status_code, duration_ms, client_host, req_headers, resp_headers, queries,
                 resp_body, profile_stats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                queries_json,
                record.response_body,
                profile_json,
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
    raw_queries = json.loads(row["queries"]) if row["queries"] else []
    queries = [
        QueryRecord(
            sql=q["sql"],
            params=q.get("params"),
            duration_ms=q.get("duration_ms", 0.0),
            stack_trace=q.get("stack_trace"),
        )
        for q in raw_queries
    ]
    raw_profile = row["profile_stats"] if "profile_stats" in row.keys() else None
    profile_stats: list[ProfileStat] | None = None
    if raw_profile:
        profile_stats = [
            ProfileStat(
                file=p.get("file", ""),
                line=p.get("line", 0),
                func=p.get("func", ""),
                prim_calls=p.get("prim_calls", 0),
                calls=p.get("calls", 0),
                tt_ms=p.get("tt_ms", 0.0),
                ct_ms=p.get("ct_ms", 0.0),
                callers=p.get("callers", []),
            )
            for p in json.loads(raw_profile)
        ]
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
        queries=queries,
        response_body=row["resp_body"],
        profile_stats=profile_stats,
    )
