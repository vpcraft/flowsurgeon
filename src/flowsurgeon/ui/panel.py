from __future__ import annotations

import importlib.resources
from collections import defaultdict
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from flowsurgeon.core.records import RequestRecord

# ---------------------------------------------------------------------------
# Jinja2 environment
# ---------------------------------------------------------------------------

_HTTP_STATUS_TEXT: dict[int, str] = {
    200: "OK", 201: "Created", 204: "No Content",
    301: "Moved Permanently", 302: "Found", 304: "Not Modified",
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
    404: "Not Found", 405: "Method Not Allowed", 409: "Conflict",
    422: "Unprocessable Entity", 429: "Too Many Requests",
    500: "Internal Server Error", 502: "Bad Gateway",
    503: "Service Unavailable", 504: "Gateway Timeout",
}

_KNOWN_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")


def _status_class(status: int) -> str:
    if status < 300:
        return "s-2xx"
    if status < 400:
        return "s-3xx"
    if status < 500:
        return "s-4xx"
    return "s-5xx"


def _duration_class(ms: float) -> str:
    if ms < 100:
        return "dur-fast"
    if ms < 300:
        return "dur-medium"
    return "dur-slow"


def _queries_color(count: int) -> str:
    if count == 0:
        return ""
    if count < 10:
        return "dur-fast"
    if count < 20:
        return "dur-medium"
    return "dur-slow"


def _status_text(status: int) -> str:
    return _HTTP_STATUS_TEXT.get(status, "")


def _method_class(method: str) -> str:
    m = method.upper()
    return f"m-{m}" if m in _KNOWN_METHODS else "m-OTHER"


_env = Environment(
    loader=PackageLoader("flowsurgeon.ui", "templates"),
    autoescape=select_autoescape(["html"]),
)
_env.filters["status_class"] = _status_class
_env.filters["duration_class"] = _duration_class
_env.filters["queries_color"] = _queries_color
_env.filters["status_text"] = _status_text
_env.filters["method_class"] = _method_class


# ---------------------------------------------------------------------------
# Asset loading
# ---------------------------------------------------------------------------


def _load_asset(name: str) -> str:
    pkg = importlib.resources.files("flowsurgeon.ui.assets")
    return (pkg / name).read_text(encoding="utf-8")


def _load_asset_bytes(name: str) -> bytes:
    pkg = importlib.resources.files("flowsurgeon.ui.assets")
    return (pkg / name).read_bytes()


# ---------------------------------------------------------------------------
# Route discovery
# ---------------------------------------------------------------------------


def discover_routes(app: Any) -> list[tuple[str, str]]:
    """Best-effort (METHOD, path) discovery from Flask/FastAPI/Starlette apps."""
    # FastAPI / Starlette: app.routes list
    if hasattr(app, "routes"):
        result: list[tuple[str, str]] = []
        for route in app.routes:
            methods = getattr(route, "methods", None) or set()
            path = getattr(route, "path", None)
            if path:
                for m in sorted(methods):
                    if m.upper() not in ("HEAD", "OPTIONS"):
                        result.append((m.upper(), path))
        return result

    # Flask app passed directly: app.url_map
    if hasattr(app, "url_map"):
        result = []
        try:
            for rule in app.url_map.iter_rules():
                if rule.endpoint != "static":
                    for m in sorted(rule.methods or []):
                        if m.upper() not in ("HEAD", "OPTIONS"):
                            result.append((m.upper(), rule.rule))
        except Exception:
            pass
        return result

    # Try common wrapper patterns: .app / .application / bound method __self__
    for attr in ("__self__", "app", "application"):
        inner = getattr(app, attr, None)
        if inner and inner is not app:
            found = discover_routes(inner)
            if found:
                return found

    return []


# ---------------------------------------------------------------------------
# Endpoint summary builder (APIs view)
# ---------------------------------------------------------------------------


_PAGE_SIZE = 20


def _build_endpoint_summaries(
    records: list[RequestRecord],
    app_routes: list[tuple[str, str]],
    method_filter: str = "",
    sort: str = "duration",
) -> list[dict]:
    """Merge discovered app routes with request history and return summary rows."""
    # Build a lookup from (method, path) → list[RequestRecord]
    groups: dict[tuple[str, str], list[RequestRecord]] = defaultdict(list)
    for r in records:
        groups[(r.method.upper(), r.path)].append(r)

    seen: set[tuple[str, str]] = set()
    summaries: list[dict] = []

    # Start from app_routes so all registered routes appear even with no traffic
    all_keys = list(dict.fromkeys(app_routes + list(groups.keys())))

    for key in all_keys:
        if key in seen:
            continue
        seen.add(key)
        method, path = key
        recs = groups.get(key, [])
        if recs:
            latest = recs[0]
            latest_query_ms = sum(q.duration_ms for q in latest.queries)
            summaries.append(
                {
                    "method": method,
                    "path": path,
                    "count": len(recs),
                    "latest_duration_ms": latest.duration_ms,
                    "latest_query_count": len(latest.queries),
                    "latest_query_ms": latest_query_ms,
                    "latest_status": latest.status_code,
                    "last_request_time": latest.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "has_data": True,
                }
            )
        else:
            summaries.append(
                {
                    "method": method,
                    "path": path,
                    "count": 0,
                    "latest_duration_ms": 0.0,
                    "latest_query_count": 0,
                    "latest_query_ms": 0.0,
                    "latest_status": 0,
                    "last_request_time": None,
                    "has_data": False,
                }
            )

    # Method filter
    if method_filter and method_filter.upper() != "ALL":
        summaries = [s for s in summaries if s["method"] == method_filter.upper()]

    # Sort
    if sort == "path":
        summaries.sort(key=lambda x: x["path"])
    elif sort == "method":
        summaries.sort(key=lambda x: x["method"])
    elif sort == "requests":
        summaries.sort(key=lambda x: x["count"], reverse=True)
    else:  # default: duration descending
        summaries.sort(key=lambda x: x["latest_duration_ms"], reverse=True)

    return summaries


def _filter_records(
    records: list[RequestRecord],
    q: str = "",
    status: str = "",
    method: str = "",
    path: str = "",
) -> list[RequestRecord]:
    """Apply filters to a list of records."""
    result = records
    if path:
        result = [r for r in result if r.path == path]
    if method:
        result = [r for r in result if r.method.upper() == method.upper()]
    if q:
        q_lower = q.lower()
        result = [r for r in result if q_lower in r.path.lower()]
    if status:
        prefix = status[0]  # "2", "3", "4", "5"
        result = [r for r in result if str(r.status_code).startswith(prefix)]
    return result


def _paginate(items: list, page: int, page_size: int = _PAGE_SIZE) -> tuple[list, int, int]:
    """Return (page_items, total_pages, clamped_page)."""
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    return items[start : start + page_size], total_pages, page


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------


def render_panel(record: RequestRecord, debug_route: str, slow_threshold: float = 100.0) -> str:
    """Return the HTML fragment for the inline debug panel."""
    css = _load_asset("panel.css")
    js = _load_asset("panel.js")
    sql_counts: dict[str, int] = {}
    for q in record.queries:
        sql_counts[q.sql] = sql_counts.get(q.sql, 0) + 1
    sql_total_ms = sum(q.duration_ms for q in record.queries)
    tmpl = _env.get_template("panel.html")
    return tmpl.render(
        record=record,
        debug_route=debug_route,
        css=css,
        js=js,
        status_class=_status_class(record.status_code),
        sql_total_ms=sql_total_ms,
        sql_counts=sql_counts,
        slow_threshold=slow_threshold,
    )


def render_history_page(
    records: list[RequestRecord],
    debug_route: str,
    view: str = "apis",
    # filters (requests view)
    q: str = "",
    status: str = "",
    method_filter: str = "",
    path_filter: str = "",
    # APIs view options
    sort: str = "duration",
    apis_method: str = "",
    # app routes for APIs view
    app_routes: list[tuple[str, str]] | None = None,
    # pagination
    page: int = 1,
) -> str:
    """Return the full HTML home page (APIs or Recent Requests view)."""
    app_routes = app_routes or []

    if view == "apis":
        summaries = _build_endpoint_summaries(
            records, app_routes, method_filter=apis_method, sort=sort
        )
        page_items, total_pages, page = _paginate(summaries, page)
        tmpl = _env.get_template("home.html")
        return tmpl.render(
            records=[],
            endpoint_summaries=page_items,
            total_summaries=len(summaries),
            debug_route=debug_route,
            active_view="apis",
            sort=sort,
            apis_method=apis_method,
            page=page,
            total_pages=total_pages,
            page_size=_PAGE_SIZE,
        )

    # Recent Requests view
    filtered = _filter_records(records, q=q, status=status, method=method_filter, path=path_filter)
    page_items, total_pages, page = _paginate(filtered, page)
    tmpl = _env.get_template("home.html")
    return tmpl.render(
        records=page_items,
        total_records=len(filtered),
        endpoint_summaries=[],
        debug_route=debug_route,
        active_view="requests",
        q=q,
        status_filter=status,
        method_filter=method_filter,
        path_filter=path_filter,
        page=page,
        total_pages=total_pages,
        page_size=_PAGE_SIZE,
    )


def render_detail_page(
    record: RequestRecord, debug_route: str, tab: str = "details", slow_threshold: float = 100.0
) -> str:
    """Return the full HTML detail page for a single request."""
    sql_total_ms = sum(q.duration_ms for q in record.queries)
    sql_counts: dict[str, int] = {}
    for q in record.queries:
        sql_counts[q.sql] = sql_counts.get(q.sql, 0) + 1
    tmpl = _env.get_template("detail.html")
    return tmpl.render(
        record=record,
        debug_route=debug_route,
        active_tab=tab,
        sql_total_ms=sql_total_ms,
        sql_counts=sql_counts,
        slow_threshold=slow_threshold,
    )
