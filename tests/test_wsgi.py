"""Integration tests for FlowSurgeonWSGI (v0.1.0)."""

from __future__ import annotations

import io
from flowsurgeon import Config, FlowSurgeonWSGI
from flowsurgeon.storage.sqlite import SQLiteBackend


# ---------------------------------------------------------------------------
# Minimal WSGI helpers
# ---------------------------------------------------------------------------


def _make_environ(
    method: str = "GET",
    path: str = "/",
    qs: str = "",
    remote_addr: str = "127.0.0.1",
) -> dict:
    return {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": qs,
        "REMOTE_ADDR": remote_addr,
        "HTTP_HOST": "localhost",
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.BytesIO(),
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.url_scheme": "http",
    }


def _call_app(app: FlowSurgeonWSGI, environ: dict) -> tuple[str, list[tuple[str, str]], bytes]:
    """Call the WSGI app and return (status, headers, body)."""
    response: list = []

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        response.append((status, headers))

    chunks = list(app(environ, start_response))
    status, headers = response[0]
    return status, headers, b"".join(chunks)


def _json_app(environ: dict, start_response) -> list[bytes]:
    body = b'{"ok": true}'
    start_response(
        "200 OK",
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def _enabled_config(tmp_path) -> Config:
    return Config(
        enabled=True,
        db_path=str(tmp_path / "test.db"),
        allowed_hosts=["127.0.0.1"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDisabledByDefault:
    def test_passthrough_when_disabled(self, tmp_path):
        cfg = Config(enabled=False, db_path=str(tmp_path / "test.db"))
        app = FlowSurgeonWSGI(_json_app, config=cfg)
        _, _, body = _call_app(app, _make_environ())
        assert body == b'{"ok": true}'


class TestAllowedHosts:
    def test_blocked_host_passes_through_unmodified(self, tmp_path):
        cfg = Config(enabled=True, db_path=str(tmp_path / "test.db"), allowed_hosts=["127.0.0.1"])
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)
        environ = _make_environ(remote_addr="10.0.0.1")
        _, _, body = _call_app(app, environ)
        assert body == b'{"ok": true}'
        assert storage.list_recent() == []

    def test_allowed_host_request_is_profiled(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)
        _call_app(app, _make_environ(remote_addr="127.0.0.1", path="/items"))
        records = storage.list_recent()
        assert len(records) == 1
        assert records[0].path == "/items"


class TestStorage:
    def test_request_stored_after_call(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)
        _call_app(app, _make_environ(path="/hello"))
        records = storage.list_recent()
        assert len(records) == 1
        assert records[0].path == "/hello"
        assert records[0].status_code == 200
        assert records[0].duration_ms > 0

    def test_sensitive_headers_redacted(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)
        environ = _make_environ()
        environ["HTTP_AUTHORIZATION"] = "Bearer secret"
        environ["HTTP_COOKIE"] = "session=abc"
        _call_app(app, environ)
        record = storage.list_recent()[0]
        assert record.request_headers.get("authorization") == "[redacted]"
        assert record.request_headers.get("cookie") == "[redacted]"


class TestDebugRoutes:
    def test_history_route_returns_html(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg)
        status, headers, body = _call_app(app, _make_environ(path="/flowsurgeon"))
        assert status == "200 OK"
        assert b"FlowSurgeon" in body

    def test_detail_route_not_found(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg)
        status, _, _ = _call_app(app, _make_environ(path="/flowsurgeon/nonexistent-id"))
        assert status == "404 Not Found"

    def test_detail_route_returns_record(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)
        _call_app(app, _make_environ(path="/my-endpoint"))
        record = storage.list_recent()[0]
        status, _, body = _call_app(app, _make_environ(path=f"/flowsurgeon/{record.request_id}"))
        assert status == "200 OK"
        assert record.request_id.encode() in body


class TestRouteDetail:
    def test_routes_home_wsgi(self, tmp_path):
        """WSGI home page returns route list HTML."""
        cfg = Config(
            enabled=True,
            db_path=str(tmp_path / "test.db"),
            allowed_hosts=["127.0.0.1"],
            known_routes=[("GET", "/api/users")],
        )
        app = FlowSurgeonWSGI(_json_app, config=cfg)
        status, _, body = _call_app(app, _make_environ(path="/flowsurgeon"))
        assert status == "200 OK"
        assert b"FlowSurgeon" in body
        assert b"/api/users" in body

    def test_route_detail_wsgi(self, tmp_path):
        """WSGI route detail page with method+path params returns filtered list."""
        cfg = _enabled_config(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)

        # Record a request for /api/users
        _call_app(app, _make_environ(path="/api/users"))
        records = storage.list_recent()
        users_id = records[0].request_id

        status, _, body = _call_app(
            app,
            _make_environ(path="/flowsurgeon", qs="method=GET&path=/api/users"),
        )
        assert status == "200 OK"
        assert b"breadcrumb" in body
        assert b"FlowSurgeon" in body
        assert b"/api/users" in body
        assert users_id[:8].encode() in body

    def test_route_detail_breadcrumb_wsgi(self, tmp_path):
        """WSGI route detail breadcrumb contains method and path."""
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg)
        status, _, body = _call_app(
            app, _make_environ(path="/flowsurgeon", qs="method=GET&path=/api/items")
        )
        assert status == "200 OK"
        assert b"m-GET" in body
        assert b"/api/items" in body

    def test_detail_page_has_profile_tab_wsgi(self, tmp_path):
        """WSGI detail page has all 4 tabs including Profile."""
        cfg = _enabled_config(tmp_path)
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)
        _call_app(app, _make_environ(path="/api/items"))
        record = storage.list_recent()[0]

        status, _, body = _call_app(app, _make_environ(path=f"/flowsurgeon/{record.request_id}"))
        assert status == "200 OK"
        assert b"Details" in body
        assert b"SQL" in body
        assert b"Traceback" in body
        assert b"Profile" in body


class TestPruning:
    def test_prune_keeps_max_records(self, tmp_path):
        cfg = Config(
            enabled=True,
            db_path=str(tmp_path / "test.db"),
            allowed_hosts=["127.0.0.1"],
            max_stored_requests=3,
        )
        storage = SQLiteBackend(cfg.db_path)
        app = FlowSurgeonWSGI(_json_app, config=cfg, storage=storage)
        for i in range(5):
            _call_app(app, _make_environ(path=f"/endpoint-{i}"))
        assert len(storage.list_recent(limit=100)) == 3
