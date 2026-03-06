"""Integration tests for FlowSurgeonASGI (v0.2.0)."""

from __future__ import annotations

import pytest

from flowsurgeon import Config, FlowSurgeon, FlowSurgeonASGI
from flowsurgeon.storage.async_sqlite import AsyncSQLiteBackend


# ---------------------------------------------------------------------------
# Minimal ASGI helpers
# ---------------------------------------------------------------------------


def _make_scope(
    method: str = "GET",
    path: str = "/",
    qs: bytes = b"",
    client: tuple[str, int] = ("127.0.0.1", 12345),
    headers: list[tuple[bytes, bytes]] | None = None,
) -> dict:
    return {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": qs,
        "client": client,
        "headers": headers or [],
    }


async def _call_app(
    app: FlowSurgeonASGI, scope: dict
) -> tuple[int, list[tuple[bytes, bytes]], bytes]:
    """Call an ASGI app and return (status, headers, body)."""
    messages: list[dict] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    body_chunks = [m.get("body", b"") for m in messages if m["type"] == "http.response.body"]
    return start["status"], start.get("headers", []), b"".join(body_chunks)


async def _html_app(scope, receive, send) -> None:
    body = b"<html><body><h1>Hello</h1></body></html>"
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _json_app(scope, receive, send) -> None:
    body = b'{"ok": true}'
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _streaming_app(scope, receive, send) -> None:
    """Multi-chunk streaming response (non-HTML)."""
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"application/octet-stream")],
        }
    )
    for chunk in [b"chunk1", b"chunk2", b"chunk3"]:
        await send({"type": "http.response.body", "body": chunk, "more_body": True})
    await send({"type": "http.response.body", "body": b"", "more_body": False})


# ---------------------------------------------------------------------------
# Config helper
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


@pytest.mark.asyncio
class TestDisabledByDefault:
    async def test_passthrough_when_disabled(self, tmp_path):
        cfg = Config(enabled=False, db_path=str(tmp_path / "test.db"))
        app = FlowSurgeonASGI(_html_app, config=cfg)
        _, _, body = await _call_app(app, _make_scope())
        assert b"FlowSurgeon" not in body

    async def test_enabled_shows_panel(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_html_app, config=cfg)
        _, _, body = await _call_app(app, _make_scope())
        assert b"FlowSurgeon" in body


@pytest.mark.asyncio
class TestAllowedHosts:
    async def test_blocked_host_passthrough(self, tmp_path):
        cfg = Config(
            enabled=True,
            db_path=str(tmp_path / "test.db"),
            allowed_hosts=["127.0.0.1"],
        )
        app = FlowSurgeonASGI(_html_app, config=cfg)
        scope = _make_scope(client=("10.0.0.1", 9999))
        _, _, body = await _call_app(app, scope)
        assert b"FlowSurgeon" not in body

    async def test_allowed_host_gets_panel(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_html_app, config=cfg)
        _, _, body = await _call_app(app, _make_scope(client=("127.0.0.1", 9999)))
        assert b"FlowSurgeon" in body

    async def test_x_forwarded_for_respected(self, tmp_path):
        cfg = Config(
            enabled=True,
            db_path=str(tmp_path / "test.db"),
            allowed_hosts=["127.0.0.1"],
        )
        app = FlowSurgeonASGI(_html_app, config=cfg)
        # Real client is allowed, but X-Forwarded-For says a blocked IP
        scope = _make_scope(
            client=("127.0.0.1", 9999),
            headers=[(b"x-forwarded-for", b"10.0.0.1")],
        )
        _, _, body = await _call_app(app, scope)
        assert b"FlowSurgeon" not in body


@pytest.mark.asyncio
class TestPanelInjection:
    async def test_panel_injected_before_body_close(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_html_app, config=cfg)
        _, _, body = await _call_app(app, _make_scope())
        assert b"fs-root" in body
        assert body.index(b"fs-root") < body.index(b"</body>")

    async def test_panel_not_injected_into_json(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_json_app, config=cfg)
        _, _, body = await _call_app(app, _make_scope())
        assert b"fs-root" not in body
        assert body == b'{"ok": true}'

    async def test_content_length_updated_after_injection(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_html_app, config=cfg)
        _, headers, body = await _call_app(app, _make_scope())
        headers_dict = {k.lower(): v for k, v in headers}
        cl = headers_dict.get(b"content-length")
        assert cl is not None
        assert int(cl) == len(body)

    async def test_non_html_streaming_passes_through(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_streaming_app, config=cfg)
        _, _, body = await _call_app(app, _make_scope())
        assert body == b"chunk1chunk2chunk3"
        assert b"fs-root" not in body


@pytest.mark.asyncio
class TestStorage:
    async def test_request_stored_after_call(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        app = FlowSurgeonASGI(_html_app, config=cfg, storage=storage)
        await _call_app(app, _make_scope(path="/hello"))
        # Drain writer queue before reading
        await storage._queue.join()
        records = await storage.list_recent()
        assert len(records) == 1
        assert records[0].path == "/hello"
        assert records[0].status_code == 200
        assert records[0].duration_ms > 0
        await storage.close()

    async def test_sensitive_headers_redacted(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        app = FlowSurgeonASGI(_html_app, config=cfg, storage=storage)
        scope = _make_scope(
            headers=[
                (b"authorization", b"Bearer secret"),
                (b"cookie", b"session=abc"),
            ]
        )
        await _call_app(app, scope)
        await storage._queue.join()
        record = (await storage.list_recent())[0]
        assert record.request_headers.get("authorization") == "[redacted]"
        assert record.request_headers.get("cookie") == "[redacted]"
        await storage.close()

    async def test_query_string_captured(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        app = FlowSurgeonASGI(_html_app, config=cfg, storage=storage)
        await _call_app(app, _make_scope(qs=b"foo=bar&baz=1"))
        await storage._queue.join()
        record = (await storage.list_recent())[0]
        assert record.query_string == "foo=bar&baz=1"
        await storage.close()


@pytest.mark.asyncio
class TestDebugRoutes:
    async def test_history_route_returns_html(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_html_app, config=cfg)
        status, _, body = await _call_app(app, _make_scope(path="/__flowsurgeon__"))
        assert status == 200
        assert b"Request History" in body

    async def test_history_route_trailing_slash(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_html_app, config=cfg)
        status, _, body = await _call_app(app, _make_scope(path="/__flowsurgeon__/"))
        assert status == 200
        assert b"Request History" in body

    async def test_detail_route_not_found(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeonASGI(_html_app, config=cfg)
        status, _, _ = await _call_app(app, _make_scope(path="/__flowsurgeon__/nonexistent-id"))
        assert status == 404

    async def test_detail_route_returns_record(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        app = FlowSurgeonASGI(_html_app, config=cfg, storage=storage)
        await _call_app(app, _make_scope(path="/my-page"))
        await storage._queue.join()
        records = await storage.list_recent()
        record = records[0]
        status, _, body = await _call_app(
            app, _make_scope(path=f"/__flowsurgeon__/{record.request_id}")
        )
        assert status == 200
        assert record.request_id.encode() in body
        await storage.close()


@pytest.mark.asyncio
class TestPruning:
    async def test_prune_keeps_max_records(self, tmp_path):
        cfg = Config(
            enabled=True,
            db_path=str(tmp_path / "test.db"),
            allowed_hosts=["127.0.0.1"],
            max_stored_requests=3,
        )
        storage = AsyncSQLiteBackend(cfg.db_path)
        app = FlowSurgeonASGI(_html_app, config=cfg, storage=storage)
        for i in range(5):
            await _call_app(app, _make_scope(path=f"/page-{i}"))
        await storage._queue.join()
        records = await storage.list_recent(limit=100)
        assert len(records) == 3
        await storage.close()


@pytest.mark.asyncio
class TestFactoryDetection:
    async def test_factory_returns_asgi_for_async_app(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        wrapped = FlowSurgeon(_html_app, config=cfg)
        assert isinstance(wrapped, FlowSurgeonASGI)

    async def test_factory_asgi_works_end_to_end(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        app = FlowSurgeon(_html_app, config=cfg)
        _, _, body = await _call_app(app, _make_scope())
        assert b"FlowSurgeon" in body


@pytest.mark.asyncio
class TestLifespan:
    async def test_lifespan_starts_and_stops_storage(self, tmp_path):
        cfg = _enabled_config(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        app = FlowSurgeonASGI(_html_app, config=cfg, storage=storage)

        lifespan_events = [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
        idx = 0
        sent: list[dict] = []

        async def receive() -> dict:
            nonlocal idx
            msg = lifespan_events[idx]
            idx += 1
            return msg

        async def send(msg: dict) -> None:
            sent.append(msg)

        # Minimal inner app that handles lifespan
        async def inner(scope, receive, send):
            while True:
                event = await receive()
                if event["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif event["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return

        app2 = FlowSurgeonASGI(inner, config=cfg, storage=storage)
        await app2({"type": "lifespan", "asgi": {}}, receive, send)
        types = [m["type"] for m in sent]
        assert "lifespan.startup.complete" in types
        assert "lifespan.shutdown.complete" in types
