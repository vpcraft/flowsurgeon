from __future__ import annotations

import time
from typing import Awaitable, Callable

from flowsurgeon.core.config import Config
from flowsurgeon.core.records import RequestRecord
from flowsurgeon.storage.async_sqlite import AsyncSQLiteBackend
from flowsurgeon.ui.panel import render_detail_page, render_history_page, render_panel

# ASGI type aliases
Scope = dict
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_HTML_CONTENT_TYPES = ("text/html",)


class FlowSurgeonASGI:
    """ASGI middleware that profiles requests and injects a debug panel.

    Parameters
    ----------
    app:
        The wrapped ASGI application.
    config:
        FlowSurgeon configuration. Defaults to :class:`Config` with all
        defaults applied.
    storage:
        Async storage backend. Defaults to :class:`AsyncSQLiteBackend`
        pointed at ``config.db_path``.
    """

    def __init__(
        self,
        app: ASGIApp,
        config: Config | None = None,
        storage: AsyncSQLiteBackend | None = None,
    ) -> None:
        self._app = app
        self._config = config or Config()
        self._storage: AsyncSQLiteBackend = storage or AsyncSQLiteBackend(self._config.db_path)

    # ------------------------------------------------------------------
    # ASGI entry point
    # ------------------------------------------------------------------

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
            return

        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        if not self._config.enabled:
            await self._app(scope, receive, send)
            return

        client_host = _client_host(scope)
        if not self._is_allowed(client_host):
            await self._app(scope, receive, send)
            return

        path = scope.get("path", "/")
        debug_route = self._config.debug_route

        if path == debug_route or path == debug_route + "/":
            await self._serve_history(send)
            return
        if path.startswith(debug_route + "/"):
            request_id = path[len(debug_route) + 1 :]
            await self._serve_detail(request_id, send)
            return

        await self._profile_request(scope, receive, send, client_host, path)

    # ------------------------------------------------------------------
    # Lifespan
    # ------------------------------------------------------------------

    async def _handle_lifespan(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def receive_wrapper() -> dict:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await self._storage.start()
            return message

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "lifespan.shutdown.complete":
                await self._storage.close()
            await send(message)

        await self._app(scope, receive_wrapper, send_wrapper)

    # ------------------------------------------------------------------
    # Debug UI routes
    # ------------------------------------------------------------------

    async def _serve_history(self, send: Send) -> None:
        records = await self._storage.list_recent(limit=100)
        body = render_history_page(records, self._config.debug_route).encode()
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

    async def _serve_detail(self, request_id: str, send: Send) -> None:
        record = await self._storage.get(request_id)
        if record is None:
            body = b"<h1>Not found</h1>"
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        (b"content-type", b"text/html; charset=utf-8"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        body = render_detail_page(record, self._config.debug_route).encode()
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

    # ------------------------------------------------------------------
    # Request profiling
    # ------------------------------------------------------------------

    async def _profile_request(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        client_host: str,
        path: str,
    ) -> None:
        raw_headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        qs = scope.get("query_string", b"").decode("latin-1")

        record = RequestRecord(
            method=scope.get("method", "GET"),
            path=path,
            query_string=qs,
            client_host=client_host,
            request_headers=_asgi_headers_to_dict(
                raw_headers, self._config.strip_sensitive_headers
            ),
        )

        # Capture response start + body chunks, detect if HTML to decide strategy
        start_message: dict | None = None
        is_html = False
        forwarding = False  # True when we're in pass-through mode (non-HTML)
        body_chunks: list[bytes] = []

        async def capturing_send(message: dict) -> None:
            nonlocal start_message, is_html, forwarding

            if message["type"] == "http.response.start":
                start_message = message
                ct = _get_asgi_header(message.get("headers", []), b"content-type") or b""
                is_html = any(h.encode() in ct for h in _HTML_CONTENT_TYPES)
                if not is_html:
                    # Non-HTML: forward start immediately and switch to pass-through
                    await send(message)
                    forwarding = True
                return

            if message["type"] == "http.response.body":
                if forwarding:
                    await send(message)
                else:
                    body_chunks.append(message.get("body", b""))

        t0 = time.perf_counter()
        await self._app(scope, receive, capturing_send)
        duration_ms = (time.perf_counter() - t0) * 1000

        if start_message is None:
            return  # degenerate app

        status_code: int = start_message["status"]
        resp_raw_headers: list[tuple[bytes, bytes]] = start_message.get("headers", [])

        record.status_code = status_code
        record.duration_ms = duration_ms
        record.response_headers = _asgi_headers_to_dict(
            resp_raw_headers, self._config.strip_sensitive_headers
        )

        # Persist asynchronously (non-blocking)
        await self._storage.enqueue(record, self._config.max_stored_requests)

        if forwarding:
            # Already forwarded — nothing more to do
            return

        # HTML path: inject panel, then forward full response
        body = b"".join(body_chunks)
        panel_html = render_panel(record, self._config.debug_route).encode()
        if b"</body>" in body:
            body = body.replace(b"</body>", panel_html + b"</body>", 1)
        else:
            body += panel_html

        # Rebuild headers with updated Content-Length
        updated_headers = [(k, v) for k, v in resp_raw_headers if k.lower() != b"content-length"]
        updated_headers.append((b"content-length", str(len(body)).encode()))

        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": updated_headers,
            }
        )
        await send({"type": "http.response.body", "body": body})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_allowed(self, host: str) -> bool:
        return host in self._config.allowed_hosts


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _client_host(scope: Scope) -> str:
    headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
    for name, value in headers:
        if name.lower() == b"x-forwarded-for":
            return value.decode("latin-1").split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else ""


def _asgi_headers_to_dict(headers: list[tuple[bytes, bytes]], strip: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name_bytes, value_bytes in headers:
        name = name_bytes.decode("latin-1").lower()
        value = value_bytes.decode("latin-1")
        result[name] = "[redacted]" if name in strip else value
    return result


def _get_asgi_header(headers: list[tuple[bytes, bytes]], name: bytes) -> bytes | None:
    name_lower = name.lower()
    for k, v in headers:
        if k.lower() == name_lower:
            return v
    return None
