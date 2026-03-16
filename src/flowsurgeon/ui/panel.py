from __future__ import annotations

import importlib.resources
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any
from jinja2 import Environment, PackageLoader, select_autoescape

from flowsurgeon.core.records import RequestRecord

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Jinja2 environment
# ---------------------------------------------------------------------------

_HTTP_STATUS_TEXT: dict[int, str] = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

_KNOWN_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")


def _status_class(status: int) -> str:
    if status <= 0:
        return ""
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


def _card_status_class(status: int) -> str:
    """Text-only color class for status codes in request cards."""
    if status < 300:
        return "cs-2xx"
    if status < 400:
        return "cs-3xx"
    if status < 500:
        return "cs-4xx"
    return "cs-5xx"


def _card_method_class(method: str) -> str:
    """Text-only color class for HTTP methods in request cards."""
    m = method.upper()
    return f"cm-{m}" if m in _KNOWN_METHODS else "cm-OTHER"


_env = Environment(
    loader=PackageLoader("flowsurgeon.ui", "templates"),
    autoescape=select_autoescape(["html"]),
)
_env.filters["status_class"] = _status_class
_env.filters["duration_class"] = _duration_class
_env.filters["queries_color"] = _queries_color
_env.filters["status_text"] = _status_text
_env.filters["method_class"] = _method_class
_env.filters["card_status_class"] = _card_status_class
_env.filters["card_method_class"] = _card_method_class


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
        _log.debug("FlowSurgeon: discovered %d routes via app.routes", len(result))
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
            _log.exception("FlowSurgeon: error discovering routes from Flask url_map")
        _log.debug("FlowSurgeon: discovered %d routes via url_map", len(result))
        return result

    # Try common wrapper patterns: .app / .application / bound method __self__
    for attr in ("__self__", "app", "application"):
        inner = getattr(app, attr, None)
        if inner and inner is not app:
            found = discover_routes(inner)
            if found:
                return found

    _log.debug("FlowSurgeon: no routes discovered for %s", type(app).__name__)
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


def _group_by_prefix(summaries: list[dict]) -> dict[str, list[dict]]:
    """Group route summary dicts by first path segment.

    Paths like '/' or empty strings become group 'root'.
    Returns dict preserving insertion order.
    """
    groups: dict[str, list[dict]] = {}
    for summary in summaries:
        path = summary.get("path", "")
        # Split on '/' and take first non-empty part
        parts = [p for p in path.split("/") if p]
        prefix = parts[0] if parts else "root"
        if prefix not in groups:
            groups[prefix] = []
        groups[prefix].append(summary)
    return groups


def _relative_time(ts_str: str | None) -> str:
    """Convert a timestamp string to a relative time string like '5m ago'.

    Returns an em dash if ts_str is None or empty.
    """
    if not ts_str:
        return "\u2014"
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        delta = (datetime.now(timezone.utc) - dt).total_seconds()
        if delta < 60:
            return f"{int(delta)}s ago"
        if delta < 3600:
            return f"{int(delta // 60)}m ago"
        if delta < 86400:
            return f"{int(delta // 3600)}h ago"
        return f"{int(delta // 86400)}d ago"
    except (ValueError, OSError):
        return "\u2014"


_env.filters["relative_time"] = _relative_time


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
    if status and status[0] in ("2", "3", "4", "5"):
        prefix = status[0]
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
    """Return the HTML fragment for the injected debug button."""
    css = _load_asset("panel.css")
    tmpl = _env.get_template("panel.html")
    return tmpl.render(
        record=record,
        debug_route=debug_route,
        css=css,
        status_class=_status_class(record.status_code),
    )


def render_routes_page(
    records: list[RequestRecord],
    debug_route: str,
    app_routes: list[tuple[str, str]] | None = None,
    method_filter: str = "",
    sort: str = "duration",
) -> str:
    """Return the full HTML home page (Swagger-style grouped routes list)."""
    summaries = _build_endpoint_summaries(
        records, app_routes or [], method_filter=method_filter, sort=sort
    )
    groups = _group_by_prefix(summaries)
    tmpl = _env.get_template("home.html")
    return tmpl.render(
        groups=groups,
        debug_route=debug_route,
        method_filter=method_filter,
        sort=sort,
        total_routes=len(summaries),
    )


def render_route_detail_page(
    records: list[RequestRecord],
    debug_route: str,
    route_method: str,
    route_path: str,
    status: str = "",
    sort: str = "recent",
    page: int = 1,
    show: int = 25,
) -> str:
    """Return the filtered request list for a specific route."""
    filtered = _filter_records(records, method=route_method, path=route_path, status=status)

    # Sort
    if sort == "duration":
        filtered = sorted(filtered, key=lambda r: r.duration_ms, reverse=True)
    elif sort == "status":
        filtered = sorted(filtered, key=lambda r: r.status_code)
    else:  # "recent" (default) -- most recent first
        filtered = sorted(filtered, key=lambda r: r.timestamp, reverse=True)

    page_items, total_pages, page = _paginate(filtered, page, show)
    tmpl = _env.get_template("route_detail.html")
    return tmpl.render(
        records=page_items,
        total_records=len(filtered),
        route_method=route_method,
        route_path=route_path,
        debug_route=debug_route,
        status=status,
        sort=sort,
        page=page,
        total_pages=total_pages,
        show=show,
    )


def render_history_page(
    records: list[RequestRecord],
    debug_route: str,
    view: str = "latency",
    # search / filter
    q: str = "",
    # sorting for latency view: "queries" | "duration" | "path"
    order: str = "queries",
    # page size
    show: int = 25,
    # pagination
    page: int = 1,
    # kept for internal use (unused in new UI but kept for compat)
    app_routes: list[tuple[str, str]] | None = None,
    # whether profiling is enabled (shown in the Profiling tab empty state)
    profiling_enabled: bool = False,
) -> str:
    """Deprecated: Use render_routes_page() instead."""
    tmpl = _env.get_template("home.html")

    # Always compute latency data so both tab panels have records available
    # (the client-side Alpine tab switch must not show an empty grid when switching)
    filtered = _filter_records(records, q=q)

    if order == "duration":
        filtered = sorted(filtered, key=lambda r: r.duration_ms, reverse=True)
    elif order == "path":
        filtered = sorted(filtered, key=lambda r: r.path)
    else:  # "queries" (default)
        filtered = sorted(filtered, key=lambda r: len(r.queries), reverse=True)

    total = len(filtered)
    total_pages = max(1, (total + show - 1) // show)
    page = max(1, min(page, total_pages))
    start = (page - 1) * show
    page_items = filtered[start : start + show]

    return tmpl.render(
        records=page_items,
        all_records=records,  # needed by Profiling tab (not filtered/paginated)
        total_records=total,
        debug_route=debug_route,
        active_view=view,  # "latency" or "profiling" — Alpine initializes tab from this
        q=q,
        order=order,
        show=show,
        page=page,
        total_pages=total_pages,
        page_start=start + 1 if total > 0 else 0,
        page_end=min(start + show, total),
        profiling_enabled=profiling_enabled,
    )


def render_detail_page(
    record: RequestRecord, debug_route: str, tab: str = "details", slow_threshold: float = 100.0
) -> str:
    """Return the full HTML detail page for a single request."""
    sql_total_ms = sum(q.duration_ms for q in record.queries)
    sql_counts: Counter[str] = Counter(q.sql for q in record.queries)
    profile_stats = record.profile_stats or []
    max_ct_ms = max((s.ct_ms for s in profile_stats), default=1.0)
    tmpl = _env.get_template("detail.html")
    return tmpl.render(
        record=record,
        debug_route=debug_route,
        active_tab=tab,
        sql_total_ms=sql_total_ms,
        sql_counts=sql_counts,
        slow_threshold=slow_threshold,
        profile_stats=profile_stats,
        max_ct_ms=max_ct_ms,
    )
