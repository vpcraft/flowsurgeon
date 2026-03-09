"""Shared HTTP utilities used by both WSGI and ASGI middlewares."""

from __future__ import annotations

import urllib.parse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HTML_CONTENT_TYPES = ("text/html",)
_TEXT_CONTENT_TYPES = ("text/", "application/json", "application/xml", "application/javascript")
_MAX_BODY_STORE = 128 * 1024  # 128 KB — limit for in-memory response body storage
_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".css": "text/css",
    ".js": "application/javascript",
}

# ---------------------------------------------------------------------------
# Query-string helpers
# ---------------------------------------------------------------------------


def _parse_qs_param(query_string: str, key: str, default: str) -> str:
    """Return the first URL-decoded value for *key*, or *default*."""
    parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)
    values = parsed.get(key)
    return values[0] if values else default


def _parse_qs_int(query_string: str, key: str, default: int) -> int:
    val = _parse_qs_param(query_string, key, "")
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Body decoding
# ---------------------------------------------------------------------------


def _decode_body(body: bytes, content_type: str) -> str | None:
    """Decode *body* for storage; returns None for binary content types."""
    if not any(t in content_type for t in _TEXT_CONTENT_TYPES):
        return None
    data = body[:_MAX_BODY_STORE]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


# ---------------------------------------------------------------------------
# IP helpers
# ---------------------------------------------------------------------------


def _strip_ipv6_zone(host: str) -> str:
    """Remove an IPv6 zone ID suffix (e.g. ``::1%eth0`` → ``::1``)."""
    return host.split("%")[0]
