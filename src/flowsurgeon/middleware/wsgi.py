from __future__ import annotations

import time
from typing import Callable, Iterable

from flowsurgeon.core.config import Config
from flowsurgeon.core.records import RequestRecord
from flowsurgeon.storage.base import StorageBackend
from flowsurgeon.storage.sqlite import SQLiteBackend
from flowsurgeon.trackers.base import QueryTracker
from flowsurgeon.trackers.context import begin_query_collection, end_query_collection
from flowsurgeon.ui.panel import render_detail_page, render_history_page, render_panel

# WSGI type aliases
Environ = dict
StartResponse = Callable[[str, list[tuple[str, str]]], None]
WSGIApp = Callable[[Environ, StartResponse], Iterable[bytes]]

_REDACTED = b"[redacted]"
_HTML_CONTENT_TYPES = ("text/html",)


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

        # Serve built-in debug UI routes
        if path == debug_route or path == debug_route + "/":
            return self._serve_history(environ, start_response)
        if path.startswith(debug_route + "/"):
            request_id = path[len(debug_route) + 1 :]
            return self._serve_detail(request_id, environ, start_response)

        return self._profile_request(environ, start_response, client_host, path)

    # ------------------------------------------------------------------
    # Debug UI routes
    # ------------------------------------------------------------------

    def _serve_history(self, environ: Environ, start_response: StartResponse) -> Iterable[bytes]:
        records = self._storage.list_recent(limit=100)
        body = render_history_page(records, self._config.debug_route).encode()
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]

    def _serve_detail(
        self, request_id: str, environ: Environ, start_response: StartResponse
    ) -> Iterable[bytes]:
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
        body = render_detail_page(record, self._config.debug_route).encode()
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
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
            # Do NOT call the real start_response yet — we may need to
            # modify Content-Length after panel injection.

        queries, token = begin_query_collection() if self._trackers and self._config.track_queries else ([], None)
        try:
            t0 = time.perf_counter()
            chunks = list(self._app(environ, capturing_start_response))
            duration_ms = (time.perf_counter() - t0) * 1000
        finally:
            if token is not None:
                end_query_collection(token)

        if not response_started:
            # Degenerate app that never called start_response
            return chunks

        status_str, resp_headers = response_started[0]
        status_code = int(status_str.split(" ", 1)[0])

        resp_headers_dict = _headers_to_dict(resp_headers, self._config.strip_sensitive_headers)

        record.status_code = status_code
        record.duration_ms = duration_ms
        record.response_headers = resp_headers_dict
        record.queries = queries

        # Persist
        self._storage.save(record)
        self._storage.prune(self._config.max_stored_requests)

        # Inject panel into HTML responses
        content_type = _get_header(resp_headers, "content-type") or ""
        if any(ct in content_type for ct in _HTML_CONTENT_TYPES):
            panel_html = render_panel(record, self._config.debug_route).encode()
            # Insert panel before </body> if present, otherwise append
            body = b"".join(chunks)
            if b"</body>" in body:
                body = body.replace(b"</body>", panel_html + b"</body>", 1)
            else:
                body = body + panel_html
            chunks = [body]
            # Rebuild headers with updated Content-Length
            resp_headers = [(k, v) for k, v in resp_headers if k.lower() != "content-length"]
            resp_headers.append(("Content-Length", str(len(body))))

        start_response(status_str, resp_headers)
        return chunks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_allowed(self, host: str) -> bool:
        return host in self._config.allowed_hosts


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _client_host(environ: Environ) -> str:
    return environ.get("HTTP_X_FORWARDED_FOR", environ.get("REMOTE_ADDR", "")).split(",")[0].strip()


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
