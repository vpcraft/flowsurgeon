from __future__ import annotations

import cProfile
import os
import time
from typing import Awaitable, Callable

import logging

from flowsurgeon._http import (
    _HTML_CONTENT_TYPES,
    _MIME_TYPES,
    _TEXT_CONTENT_TYPES,
    _decode_body,
    _parse_qs_param,
    _strip_ipv6_zone,
)

_log = logging.getLogger(__name__)
from flowsurgeon.core.config import Config
from flowsurgeon.core.records import RequestRecord
from flowsurgeon.profiling import _parse_profile
from flowsurgeon.storage.async_sqlite import AsyncSQLiteBackend
from flowsurgeon.trackers.base import QueryTracker
from flowsurgeon.trackers.context import begin_query_collection, end_query_collection
from flowsurgeon.ui.panel import (
    _load_asset_bytes,
    discover_routes,
    render_detail_page,
    render_panel,
    render_routes_page,
)

# ASGI type aliases
Scope = dict
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


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
        trackers: list[QueryTracker] | None = None,
    ) -> None:
        self._app = app
        self._config = config or Config()
        self._storage: AsyncSQLiteBackend = storage or AsyncSQLiteBackend(self._config.db_path)
        self._trackers: list[QueryTracker] = trackers or []
        for tracker in self._trackers:
            tracker.install()

        # Merge explicit known_routes with auto-discovered routes (dedup, preserve order)
        discovered = discover_routes(app)
        seen: set[tuple[str, str]] = set()
        self._app_routes: list[tuple[str, str]] = []
        for route in list(self._config.known_routes) + discovered:
            if route not in seen:
                seen.add(route)
                self._app_routes.append(route)

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
        qs = scope.get("query_string", b"").decode("latin-1")

        # Static assets: /{debug_route}/_static/<filename>
        static_prefix = debug_route + "/_static/"
        if path.startswith(static_prefix):
            filename = path[len(static_prefix) :]
            await self._serve_static(filename, send)
            return

        if path == debug_route or path == debug_route + "/":
            await self._serve_history(send, qs)
            return

        if path.startswith(debug_route + "/"):
            request_id = path[len(debug_route) + 1 :]
            await self._serve_detail(request_id, send, qs)
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
                for tracker in self._trackers:
                    tracker.uninstall()
                await self._storage.close()
            await send(message)

        await self._app(scope, receive_wrapper, send_wrapper)

    # ------------------------------------------------------------------
    # Debug UI routes
    # ------------------------------------------------------------------

    async def _serve_static(self, filename: str, send: Send) -> None:
        # Guard against path traversal (e.g. /_static/../panel.py)
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            body = b"Not found"
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        (b"content-type", b"text/plain"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        ext = os.path.splitext(filename)[1].lower()
        mime = _MIME_TYPES.get(ext, "application/octet-stream")
        try:
            data = _load_asset_bytes(filename)
        except Exception:
            body = b"Not found"
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        (b"content-type", b"text/plain"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", mime.encode()),
                    (b"content-length", str(len(data)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": data})

    async def _serve_history(self, send: Send, query_string: str = "") -> None:
        method_filter = _parse_qs_param(query_string, "method", "")
        sort = _parse_qs_param(query_string, "sort", "duration")

        records = await self._storage.list_recent(limit=500)
        body = render_routes_page(
            records,
            self._config.debug_route,
            app_routes=self._app_routes,
            method_filter=method_filter,
            sort=sort,
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/html; charset=utf-8"),
                    (b"content-length", str(len(body)).encode()),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def _serve_detail(self, request_id: str, send: Send, query_string: str = "") -> None:
        tab = _parse_qs_param(query_string, "tab", "details")
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
        body = render_detail_page(
            record,
            self._config.debug_route,
            tab=tab,
            slow_threshold=self._config.slow_query_threshold_ms,
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/html; charset=utf-8"),
                    (b"content-length", str(len(body)).encode()),
                    (b"cache-control", b"no-store"),
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

        start_message: dict | None = None
        is_html = False
        is_text = False
        streaming = False
        body_chunks: list[bytes] = []

        async def capturing_send(message: dict) -> None:
            nonlocal start_message, is_html, is_text, streaming

            if message["type"] == "http.response.start":
                start_message = message
                ct = _get_asgi_header(message.get("headers", []), b"content-type") or b""
                is_html = any(h.encode() in ct for h in _HTML_CONTENT_TYPES)
                is_text = any(t.encode() in ct for t in _TEXT_CONTENT_TYPES)
                if not is_text:
                    # Binary response: forward immediately, don't buffer
                    streaming = True
                    await send(message)
                return

            if message["type"] == "http.response.body":
                if streaming:
                    await send(message)
                else:
                    body_chunks.append(message.get("body", b""))

        queries, token = (
            begin_query_collection()
            if self._trackers and self._config.track_queries
            else ([], None)
        )
        prof: cProfile.Profile | None = None
        if self._config.enable_profiling:
            prof = cProfile.Profile()
            prof.enable()
        try:
            t0 = time.perf_counter()
            await self._app(scope, receive, capturing_send)
            duration_ms = (time.perf_counter() - t0) * 1000
        finally:
            if prof is not None:
                prof.disable()
                record.profile_stats = _parse_profile(prof, self._config)
            if token is not None:
                end_query_collection(token)

        if start_message is None:
            return  # degenerate app

        status_code: int = start_message["status"]
        resp_raw_headers: list[tuple[bytes, bytes]] = start_message.get("headers", [])
        ct_header = (_get_asgi_header(resp_raw_headers, b"content-type") or b"").decode("latin-1")

        record.status_code = status_code
        record.duration_ms = duration_ms
        record.response_headers = _asgi_headers_to_dict(
            resp_raw_headers, self._config.strip_sensitive_headers
        )
        record.queries = queries

        if streaming:
            # Binary response already forwarded — just save metadata
            record.response_body = None
            await self._storage.enqueue(record, self._config.max_stored_requests)
            return

        # --- Text response: buffered ---
        body = b"".join(body_chunks)

        if self._config.capture_response_body:
            record.response_body = _decode_body(body, ct_header)
        else:
            record.response_body = None

        await self._storage.enqueue(record, self._config.max_stored_requests)

        if is_html:
            panel_html = render_panel(
                record,
                self._config.debug_route,
                slow_threshold=self._config.slow_query_threshold_ms,
            ).encode()
            if b"</body>" in body:
                body = body.replace(b"</body>", panel_html + b"</body>", 1)
            else:
                body += panel_html

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
    # Use only the actual TCP connection source — never X-Forwarded-For,
    # which is user-controlled and could be forged to bypass allowed_hosts.
    client = scope.get("client")
    return _strip_ipv6_zone(client[0]) if client else ""


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
