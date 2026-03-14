from __future__ import annotations

import cProfile
import os
import time
from typing import Callable, Iterable

import logging

from flowsurgeon._http import (
    _HTML_CONTENT_TYPES,
    _MIME_TYPES,
    _TEXT_CONTENT_TYPES,
    _decode_body,
    _parse_qs_int,
    _parse_qs_param,
    _strip_ipv6_zone,
)

_log = logging.getLogger(__name__)
from flowsurgeon.core.config import Config
from flowsurgeon.core.records import RequestRecord
from flowsurgeon.profiling import _parse_profile
from flowsurgeon.storage.base import StorageBackend
from flowsurgeon.storage.sqlite import SQLiteBackend
from flowsurgeon.trackers.base import QueryTracker
from flowsurgeon.trackers.context import begin_query_collection, end_query_collection
from flowsurgeon.ui.panel import (
    _load_asset_bytes,
    discover_routes,
    render_detail_page,
    render_history_page,
    render_panel,
)

# WSGI type aliases
Environ = dict
StartResponse = Callable[[str, list[tuple[str, str]]], None]
WSGIApp = Callable[[Environ, StartResponse], Iterable[bytes]]


class FlowSurgeonWSGI:
    """WSGI middleware that profiles requests and injects a debug panel.

    Parameters
    ----------
    app:
        The wrapped WSGI application.
    config:
        FlowSurgeon configuration. Defaults to :class:`Config` with all
        defaults applied (middleware disabled unless FLOWSURGEON_ENABLED=1).
    storage:
        Storage backend to use. Defaults to :class:`SQLiteBackend` pointed
        at ``config.db_path``.
    """

    def __init__(
        self,
        app: WSGIApp,
        config: Config | None = None,
        storage: StorageBackend | None = None,
        trackers: list[QueryTracker] | None = None,
    ) -> None:
        self._app = app
        self._config = config or Config()
        self._storage: StorageBackend = storage or SQLiteBackend(self._config.db_path)
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

    def close(self) -> None:
        """Uninstall all trackers and release storage resources."""
        for tracker in self._trackers:
            tracker.uninstall()
        self._storage.close()

    # ------------------------------------------------------------------
    # WSGI entry point
    # ------------------------------------------------------------------

    def __call__(self, environ: Environ, start_response: StartResponse) -> Iterable[bytes]:
        if not self._config.enabled:
            return self._app(environ, start_response)

        client_host = _client_host(environ)
        if not self._is_allowed(client_host):
            return self._app(environ, start_response)

        path = environ.get("PATH_INFO", "/")
        debug_route = self._config.debug_route
        qs = environ.get("QUERY_STRING", "")

        # Static assets: /{debug_route}/_static/<filename>
        static_prefix = debug_route + "/_static/"
        if path.startswith(static_prefix):
            filename = path[len(static_prefix) :]
            return self._serve_static(filename, start_response)

        if path == debug_route or path == debug_route + "/":
            return self._serve_history(environ, start_response, qs)
        if path.startswith(debug_route + "/"):
            request_id = path[len(debug_route) + 1 :]
            return self._serve_detail(request_id, environ, start_response, qs)

        return self._profile_request(environ, start_response, client_host, path)

    # ------------------------------------------------------------------
    # Debug UI routes
    # ------------------------------------------------------------------

    def _serve_static(self, filename: str, start_response: StartResponse) -> Iterable[bytes]:
        # Guard against path traversal (e.g. /_static/../panel.py)
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            body = b"Not found"
            start_response(
                "404 Not Found",
                [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))],
            )
            return [body]
        ext = os.path.splitext(filename)[1].lower()
        mime = _MIME_TYPES.get(ext, "application/octet-stream")
        try:
            data = _load_asset_bytes(filename)
        except Exception:
            body = b"Not found"
            start_response(
                "404 Not Found",
                [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))],
            )
            return [body]
        start_response("200 OK", [("Content-Type", mime), ("Content-Length", str(len(data)))])
        return [data]

    def _serve_history(
        self, environ: Environ, start_response: StartResponse, query_string: str = ""
    ) -> Iterable[bytes]:
        view = _parse_qs_param(query_string, "view", "latency")
        q = _parse_qs_param(query_string, "q", "")
        order = _parse_qs_param(query_string, "order", "queries")
        show = _parse_qs_int(query_string, "show", 25)
        page = _parse_qs_int(query_string, "page", 1)

        records = self._storage.list_recent(limit=500)
        body = render_history_page(
            records,
            self._config.debug_route,
            view=view,
            q=q,
            order=order,
            show=show,
            page=page,
            profiling_enabled=self._config.enable_profiling,
        ).encode()
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [body]

    def _serve_detail(
        self,
        request_id: str,
        environ: Environ,
        start_response: StartResponse,
        query_string: str = "",
    ) -> Iterable[bytes]:
        tab = _parse_qs_param(query_string, "tab", "details")
        record = self._storage.get(request_id)
        if record is None:
            body = b"<h1>Not found</h1>"
            start_response(
                "404 Not Found",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]
        body = render_detail_page(
            record,
            self._config.debug_route,
            tab=tab,
            slow_threshold=self._config.slow_query_threshold_ms,
        ).encode()
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [body]

    # ------------------------------------------------------------------
    # Request profiling
    # ------------------------------------------------------------------

    def _profile_request(
        self,
        environ: Environ,
        start_response: StartResponse,
        client_host: str,
        path: str,
    ) -> Iterable[bytes]:
        record = RequestRecord(
            method=environ.get("REQUEST_METHOD", "GET"),
            path=path,
            query_string=environ.get("QUERY_STRING", ""),
            client_host=client_host,
            request_headers=_extract_request_headers(environ, self._config.strip_sensitive_headers),
        )

        response_started: list[tuple[str, list[tuple[str, str]]]] = []

        def capturing_start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response_started.append((status, headers))

        queries, token = (
            begin_query_collection()
            if self._trackers and self._config.track_queries
            else ([], None)
        )
        prof: cProfile.Profile | None = None
        if self._config.enable_profiling:
            prof = cProfile.Profile()
            prof.enable()

        t0 = time.perf_counter()
        app_iter = iter(self._app(environ, capturing_start_response))

        # Pull the first chunk to trigger start_response.
        try:
            first_chunk = next(app_iter)
        except StopIteration:
            first_chunk = b""

        if not response_started:
            # Degenerate app that never called start_response
            if prof is not None:
                prof.disable()
            if token is not None:
                end_query_collection(token)
            return [first_chunk] if first_chunk else []

        status_str, resp_headers = response_started[0]
        status_code = int(status_str.split(" ", 1)[0])
        content_type = _get_header(resp_headers, "content-type") or ""
        is_text = any(t in content_type for t in _TEXT_CONTENT_TYPES)

        if not is_text:
            # --- Binary response: stream through without buffering ---
            start_response(status_str, resp_headers)
            storage = self._storage
            config = self._config

            def _stream() -> Iterable[bytes]:
                try:
                    if first_chunk:
                        yield first_chunk
                    for chunk in app_iter:
                        yield chunk
                finally:
                    duration_ms = (time.perf_counter() - t0) * 1000
                    if prof is not None:
                        prof.disable()
                        record.profile_stats = _parse_profile(prof, config)
                    if token is not None:
                        end_query_collection(token)
                    record.status_code = status_code
                    record.duration_ms = duration_ms
                    record.response_headers = _headers_to_dict(
                        resp_headers, config.strip_sensitive_headers
                    )
                    record.queries = queries
                    record.response_body = None
                    storage.save(record)
                    storage.prune(config.max_stored_requests)

            return _stream()

        # --- Text response: buffer for storage / panel injection ---
        remaining = list(app_iter)
        duration_ms = (time.perf_counter() - t0) * 1000
        if prof is not None:
            prof.disable()
            record.profile_stats = _parse_profile(prof, self._config)
        if token is not None:
            end_query_collection(token)

        body = b"".join([first_chunk] + remaining)
        resp_headers_dict = _headers_to_dict(resp_headers, self._config.strip_sensitive_headers)

        record.status_code = status_code
        record.duration_ms = duration_ms
        record.response_headers = resp_headers_dict
        record.queries = queries
        if self._config.capture_response_body:
            record.response_body = _decode_body(body, content_type)
        else:
            record.response_body = None

        self._storage.save(record)
        self._storage.prune(self._config.max_stored_requests)

        # Inject panel into HTML responses
        if any(ct in content_type for ct in _HTML_CONTENT_TYPES):
            panel_html = render_panel(
                record,
                self._config.debug_route,
                slow_threshold=self._config.slow_query_threshold_ms,
            ).encode()
            if b"</body>" in body:
                body = body.replace(b"</body>", panel_html + b"</body>", 1)
            else:
                body = body + panel_html
            resp_headers = [(k, v) for k, v in resp_headers if k.lower() != "content-length"]
            resp_headers.append(("Content-Length", str(len(body))))

        start_response(status_str, resp_headers)
        return [body]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_allowed(self, host: str) -> bool:
        return host in self._config.allowed_hosts


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _client_host(environ: Environ) -> str:
    # Use only REMOTE_ADDR (the actual TCP connection source) — never
    # HTTP_X_FORWARDED_FOR, which is user-controlled and could be forged
    # to bypass the allowed_hosts check.
    return _strip_ipv6_zone(environ.get("REMOTE_ADDR", ""))


def _extract_request_headers(environ: Environ, strip: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in environ.items():
        if key == "CONTENT_TYPE":
            headers["content-type"] = value
        elif key == "CONTENT_LENGTH":
            headers["content-length"] = value
        elif key.startswith("HTTP_"):
            name = key[5:].replace("_", "-").lower()
            headers[name] = "[redacted]" if name in strip else value
    return headers


def _headers_to_dict(headers: list[tuple[str, str]], strip: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in headers:
        lower = name.lower()
        result[lower] = "[redacted]" if lower in strip else value
    return result


def _get_header(headers: list[tuple[str, str]], name: str) -> str | None:
    lower = name.lower()
    for k, v in headers:
        if k.lower() == lower:
            return v
    return None
