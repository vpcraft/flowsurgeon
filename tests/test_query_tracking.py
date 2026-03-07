"""Tests for v0.3.0 query tracking (DBAPITracker, SQLAlchemyTracker, context)."""

from __future__ import annotations

import asyncio
import io
import sqlite3

import pytest

from flowsurgeon import Config, FlowSurgeonASGI, FlowSurgeonWSGI
from flowsurgeon.core.records import QueryRecord
from flowsurgeon.storage.async_sqlite import AsyncSQLiteBackend
from flowsurgeon.storage.sqlite import SQLiteBackend
from flowsurgeon.trackers.context import begin_query_collection, end_query_collection, get_current_queries
from flowsurgeon.trackers.dbapi import DBAPITracker


# ---------------------------------------------------------------------------
# Minimal WSGI/ASGI JSON app helpers
# ---------------------------------------------------------------------------


def _make_wsgi_environ(path: str = "/", remote_addr: str = "127.0.0.1") -> dict:
    return {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "REMOTE_ADDR": remote_addr,
        "HTTP_HOST": "localhost",
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.BytesIO(),
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.url_scheme": "http",
    }


def _wsgi_json_app(environ, start_response):
    body = b'{"ok": true}'
    start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
    return [body]


def _call_wsgi(app, environ):
    responses = []
    def sr(status, headers):
        responses.append((status, headers))
    chunks = list(app(environ, sr))
    return responses[0][0], b"".join(chunks)


async def _asgi_json_app(scope, receive, send):
    body = b'{"ok": true}'
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
    })
    await send({"type": "http.response.body", "body": body})


async def _call_asgi(app, path: str = "/", client: tuple = ("127.0.0.1", 9000)):
    messages = []
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    async def send(msg):
        messages.append(msg)
    scope = {"type": "http", "method": "GET", "path": path,
             "query_string": b"", "headers": [], "client": client}
    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], body


def _enabled_cfg(tmp_path):
    return Config(enabled=True, db_path=str(tmp_path / "t.db"), allowed_hosts=["127.0.0.1"])


# ---------------------------------------------------------------------------
# Context variable tests
# ---------------------------------------------------------------------------


class TestQueryContext:
    def test_default_is_none(self):
        assert get_current_queries() is None

    def test_begin_returns_empty_list_and_token(self):
        queries, token = begin_query_collection()
        assert queries == []
        assert get_current_queries() is queries
        end_query_collection(token)
        assert get_current_queries() is None

    def test_append_visible_within_scope(self):
        queries, token = begin_query_collection()
        get_current_queries().append(QueryRecord(sql="SELECT 1"))
        assert len(queries) == 1
        end_query_collection(token)

    def test_nested_scopes_are_isolated(self):
        outer, t_outer = begin_query_collection()
        outer.append(QueryRecord(sql="outer"))
        inner, t_inner = begin_query_collection()
        inner.append(QueryRecord(sql="inner"))
        end_query_collection(t_inner)
        assert get_current_queries() is outer
        assert len(outer) == 1
        end_query_collection(t_outer)


# ---------------------------------------------------------------------------
# DBAPITracker unit tests
# ---------------------------------------------------------------------------


class TestDBAPITracker:
    def test_install_uninstall_are_noop(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))
        tracker.install()
        tracker.uninstall()

    def test_connection_proxy_exposes_cursor(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))
        assert tracker.connection.cursor() is not None

    def test_execute_records_query_in_context(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        queries, token = begin_query_collection()
        tracker.connection.cursor().execute("SELECT 1")
        end_query_collection(token)

        assert len(queries) == 1
        assert queries[0].sql == "SELECT 1"
        assert queries[0].duration_ms >= 0

    def test_execute_with_params_captured(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        queries, token = begin_query_collection()
        tracker.connection.cursor().execute("SELECT ?", (42,))
        end_query_collection(token)

        assert queries[0].params == repr((42,))

    def test_no_recording_outside_context(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))
        tracker.connection.cursor().execute("SELECT 1")  # no context — must not raise

    def test_cursor_delegation(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))
        cur = tracker.connection.cursor()
        cur.execute("SELECT 42")
        assert cur.fetchone()[0] == 42

    def test_stacktrace_captured_when_enabled(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"), capture_stacktrace=True)

        queries, token = begin_query_collection()
        tracker.connection.cursor().execute("SELECT 1")
        end_query_collection(token)

        assert queries[0].stack_trace is not None

    def test_stacktrace_none_by_default(self):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        queries, token = begin_query_collection()
        tracker.connection.cursor().execute("SELECT 1")
        end_query_collection(token)

        assert queries[0].stack_trace is None


# ---------------------------------------------------------------------------
# WSGI middleware integration with DBAPITracker
# ---------------------------------------------------------------------------


class TestWSGIWithTracker:
    def test_queries_attached_to_record(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        def app_with_query(environ, start_response):
            tracker.connection.cursor().execute("SELECT 42")
            return _wsgi_json_app(environ, start_response)

        cfg = _enabled_cfg(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonWSGI(app_with_query, config=cfg, storage=storage, trackers=[tracker])

        _call_wsgi(middleware, _make_wsgi_environ())
        record = storage.list_recent()[0]
        assert len(record.queries) == 1
        assert record.queries[0].sql == "SELECT 42"
        middleware.close()

    def test_multiple_requests_isolated(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))
        call_count = [0]

        def counting_app(environ, start_response):
            call_count[0] += 1
            for _ in range(call_count[0]):
                tracker.connection.cursor().execute("SELECT 1")
            return _wsgi_json_app(environ, start_response)

        cfg = _enabled_cfg(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonWSGI(counting_app, config=cfg, storage=storage, trackers=[tracker])

        _call_wsgi(middleware, _make_wsgi_environ(path="/r1"))
        _call_wsgi(middleware, _make_wsgi_environ(path="/r2"))

        by_path = {r.path: r for r in storage.list_recent(limit=10)}
        assert len(by_path["/r1"].queries) == 1
        assert len(by_path["/r2"].queries) == 2
        middleware.close()

    def test_queries_persisted_and_retrieved(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        def app_with_queries(environ, start_response):
            tracker.connection.cursor().execute("SELECT 1")
            tracker.connection.cursor().execute("SELECT 2")
            return _wsgi_json_app(environ, start_response)

        cfg = _enabled_cfg(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonWSGI(app_with_queries, config=cfg, storage=storage, trackers=[tracker])

        _call_wsgi(middleware, _make_wsgi_environ())
        record = storage.list_recent()[0]
        fresh = storage.get(record.request_id)
        assert len(fresh.queries) == 2
        assert fresh.queries[0].sql == "SELECT 1"
        assert fresh.queries[1].sql == "SELECT 2"
        middleware.close()

    def test_track_queries_false_skips_collection(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        def app_with_query(environ, start_response):
            tracker.connection.cursor().execute("SELECT 99")
            return _wsgi_json_app(environ, start_response)

        cfg = Config(
            enabled=True, db_path=str(tmp_path / "t.db"),
            allowed_hosts=["127.0.0.1"], track_queries=False,
        )
        storage = SQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonWSGI(app_with_query, config=cfg, storage=storage, trackers=[tracker])

        _call_wsgi(middleware, _make_wsgi_environ())
        assert storage.list_recent()[0].queries == []
        middleware.close()


# ---------------------------------------------------------------------------
# ASGI middleware integration with DBAPITracker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestASGIWithTracker:
    async def test_queries_attached_to_record(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        async def app_with_query(scope, receive, send):
            tracker.connection.cursor().execute("SELECT 42")
            await _asgi_json_app(scope, receive, send)

        cfg = _enabled_cfg(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonASGI(app_with_query, config=cfg, storage=storage, trackers=[tracker])

        await _call_asgi(middleware)
        await storage._queue.join()
        records = await storage.list_recent()
        assert len(records[0].queries) == 1
        assert records[0].queries[0].sql == "SELECT 42"
        await storage.close()

    async def test_concurrent_requests_isolated(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        async def counting_app(scope, receive, send):
            n = int(scope["path"].lstrip("/"))
            for _ in range(n):
                tracker.connection.cursor().execute("SELECT 1")
            await _asgi_json_app(scope, receive, send)

        cfg = _enabled_cfg(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonASGI(counting_app, config=cfg, storage=storage, trackers=[tracker])

        await asyncio.gather(
            _call_asgi(middleware, path="/3"),
            _call_asgi(middleware, path="/1"),
            _call_asgi(middleware, path="/2"),
        )
        await storage._queue.join()
        by_path = {r.path: r for r in await storage.list_recent(limit=10)}
        assert len(by_path["/1"].queries) == 1
        assert len(by_path["/2"].queries) == 2
        assert len(by_path["/3"].queries) == 3
        await storage.close()


# ---------------------------------------------------------------------------
# SQLAlchemyTracker (requires sqlalchemy — skip if not installed)
# ---------------------------------------------------------------------------


@pytest.fixture
def sa_engine(tmp_path):
    pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, text
    from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

    engine = create_engine(f"sqlite:///{tmp_path}/sa.db")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.commit()
    return engine


class TestSQLAlchemyTracker:
    def test_records_query_in_context(self, sa_engine):
        from sqlalchemy import text
        from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

        tracker = SQLAlchemyTracker(sa_engine)
        tracker.install()

        queries, token = begin_query_collection()
        with sa_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        end_query_collection(token)

        assert len(queries) >= 1
        assert any("SELECT 1" in q.sql for q in queries)
        tracker.uninstall()

    def test_no_recording_outside_context(self, sa_engine):
        from sqlalchemy import text
        from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

        tracker = SQLAlchemyTracker(sa_engine)
        tracker.install()
        with sa_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        assert get_current_queries() is None
        tracker.uninstall()

    def test_uninstall_removes_listener(self, sa_engine):
        from sqlalchemy import text
        from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

        tracker = SQLAlchemyTracker(sa_engine)
        tracker.install()
        tracker.uninstall()

        queries, token = begin_query_collection()
        with sa_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        end_query_collection(token)

        assert len(queries) == 0

    def test_wsgi_integration(self, tmp_path, sa_engine):
        from sqlalchemy import text
        from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

        def app_with_sa_query(environ, start_response):
            with sa_engine.connect() as conn:
                conn.execute(text("SELECT 42"))
            return _wsgi_json_app(environ, start_response)

        cfg = _enabled_cfg(tmp_path)
        tracker = SQLAlchemyTracker(sa_engine)
        storage = SQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonWSGI(
            app_with_sa_query, config=cfg, storage=storage, trackers=[tracker]
        )

        _call_wsgi(middleware, _make_wsgi_environ())
        record = storage.list_recent()[0]
        assert any("SELECT 42" in q.sql for q in record.queries)
        middleware.close()
