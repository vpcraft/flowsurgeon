# FlowSurgeon v0.5.0 — Debug Report

## Architecture

**Module map:**

```
__init__.py          Auto-detect WSGI/ASGI, facade function
_http.py             Shared: QS parsing, body decode, MIME, IPv6
core/config.py       Dataclass config with env-var defaults + __post_init__ validation
core/records.py      RequestRecord, QueryRecord, ProfileStat
middleware/wsgi.py    WSGI middleware (sync, thread-safe)
middleware/asgi.py    ASGI middleware (async, queue-based writer)
storage/base.py      Abstract StorageBackend
storage/sqlite.py    Sync SQLite with per-thread connections, WAL, migrations
storage/async_sqlite.py  Async wrapper: queue + background writer coroutine
trackers/context.py  ContextVar for per-request query collection
trackers/dbapi.py    Transparent DB-API 2.0 proxy (connection + cursor)
trackers/sqlalchemy.py  SQLAlchemy event-listener tracker
profiling.py         cProfile → pstats.Stats → ProfileStat list
ui/panel.py          Jinja2 rendering, route discovery, filtering, pagination
```

**Data flow:** Request → access-control gate → cProfile wrap → app call → capture response → store to SQLite → inject panel button into HTML → return response.

---

## Issues Found

### Security

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| S1 | High | **Response body stored unredacted.** API responses containing tokens, passwords, or PII are persisted in plaintext SQLite. `strip_sensitive_headers` exists for headers but there is no equivalent for body content. | `wsgi.py:265`, `asgi.py:334` |
| S2 | Medium | **No `X-Content-Type-Options: nosniff` on static assets.** Browser could MIME-sniff served assets if a future file type is added. | `wsgi.py:135`, `asgi.py:186-187` |
| S3 | Medium | **SQLite database is unencrypted plaintext.** Contains full request/response data. If committed to VCS or included in backups, all captured data leaks. | `sqlite.py` |
| S4 | Low | **Default `allowed_hosts` bypassed behind misconfigured reverse proxy.** If the proxy doesn't set `REMOTE_ADDR` correctly, the check is meaningless. No warning emitted. | `config.py:31` |

### Implementation

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| I1 | High | **Full response buffering for all content types.** `chunks = list(self._app(...))` loads entire response into memory before returning anything. A 50 MB file download response holds 50 MB in RAM and breaks TTFB. Panel injection only applies to HTML; non-HTML responses should be streamed through. | `wsgi.py:240`, `asgi.py:310` |
| I2 | Medium | **`_client_host()` still duplicated between middlewares.** Both wsgi.py and asgi.py define their own `_client_host()`. Only the IPv6 stripping was extracted to `_http.py`. The functions themselves should move there too. | `wsgi.py:308`, `asgi.py:379` |
| I3 | Medium | **`_serve_static()` logic duplicated.** Identical path-traversal guard + asset load + MIME lookup in both middlewares. Only differs in response API (WSGI tuples vs ASGI dicts). | `wsgi.py:115-136`, `asgi.py:143-187` |
| I4 | Medium | **`discover_routes()` swallows all exceptions silently.** Flask `url_map.iter_rules()` errors are caught with bare `except Exception: pass` — no logging. | `panel.py:151` |
| I5 | Medium | **`_parse_profile()` returns `[]` on error without logging.** If `pstats.Stats()` fails, profiling silently produces no data — user sees empty Profile tab with no explanation. | `profiling.py:91-92` |
| I6 | Low | **Pruning query is O(n).** `DELETE WHERE request_id NOT IN (SELECT ... ORDER BY timestamp DESC LIMIT ?)` scans the full table on every request. For 10k+ rows this adds measurable latency. A `DELETE WHERE timestamp < (SELECT timestamp FROM requests ORDER BY timestamp DESC LIMIT 1 OFFSET ?)` would be faster. | `sqlite.py:155-163` |
| I7 | Low | **No connection eviction in `SQLiteBackend`.** `threading.local()` connections accumulate for the lifetime of each thread. On thread-pool servers (Gunicorn with many workers), this means many open SQLite connections with no cleanup until process exit. | `sqlite.py:45-50` |

### Design / UX

| # | Severity | Issue | Location |
|---|----------|-------|----------|
| D1 | Medium | **Not responsive — desktop only.** 6-column card grid is hardcoded with no media queries. On anything under ~1200px wide, horizontal scroll is required. No mobile breakpoints, no collapsible nav. | `base.html:828` |
| D2 | Medium | **No keyboard accessibility.** Tab navigation uses `@click.prevent` with no `tabindex` or focus indicators. `<details>` callers drilldown in Profile tab is keyboard-accessible natively, but the tab bar is not. | `detail.html:22-49`, `home.html:38-48` |
| D3 | Medium | **No ARIA labels.** Filter inputs lack `<label>` elements. Status badges rely on color alone (no icon/text fallback for colorblind users). No `role` attributes on tab panels. | `home.html:54-61` |
| D4 | Low | **Tab state not reflected in URL.** Clicking the "Profiling" tab in home view uses `@click.prevent` which doesn't update `?view=profiling`. Refreshing the page resets to the default tab. Same for detail page tabs. | `home.html:45`, `detail.html:23-49` |
| D5 | Low | **No loading/empty state for slow storage reads.** If `list_recent(500)` is slow, the user sees a blank page until the full render completes. No skeleton/spinner. | `wsgi.py:147`, `asgi.py:196` |
| D6 | Low | **Breadcrumb shows truncated request ID.** `{{ record.request_id[:8] }}` gives 8 hex chars — collision-prone in large datasets and not copyable. | `detail.html:15` |

### Test Gaps

| # | What's missing | Risk |
|---|----------------|------|
| T1 | Concurrent WSGI requests writing to same SQLite | Thread-safety regression |
| T2 | Response with multiple `</body>` tags | Panel injected in wrong position |
| T3 | Non-HTML streaming response (large binary) | Memory spike not caught |
| T4 | `Config(db_path="/readonly/dir/x.db")` after `__post_init__` `makedirs` | Permission error not tested |
| T5 | Corrupted/truncated JSON in `profile_stats` column | `json.loads` crash on read |
| T6 | `profile_user_code_only=False` with deep stdlib call stack | Correctness of filtering |
| T7 | Profiling disabled mid-request (edge: `enable_profiling` toggled) | Not applicable (config is per-init) but worth documenting |

### Performance

| Area | Current | Concern |
|------|---------|---------|
| Response buffering | All content types buffered | 50 MB download = 50 MB in RAM |
| cProfile | ~1-10% CPU overhead | Acceptable when opt-in |
| Stack trace capture | `traceback.format_stack()` per query | ~5-10ms per query when enabled |
| Pruning | Full table scan per request | O(n) for n stored records |
| JSON deserialization | All records deserialized on `list_recent` | Slow for 500 records with large query lists |
| Async writer | Single background coroutine | Serializes all writes; fine for dev traffic |

---

## What's Working Well

- **Framework detection** — `FlowSurgeon()` auto-selects WSGI vs ASGI by inspecting the app. Route discovery works for Flask, FastAPI, and Starlette with no config.
- **Query tracking** — DB-API proxy and SQLAlchemy event listener both capture timing accurately. ContextVar-based per-request isolation is correct and tested.
- **Profiling pipeline** — `cProfile` → `pstats.Stats` → filtered `ProfileStat` list is solid. User-code filtering via `sys.prefix` / `site-packages` works. Callers drilldown provides real value.
- **Storage migrations** — `ALTER TABLE ADD COLUMN` with try/except for existing columns makes upgrades seamless.
- **Security defaults** — `enabled=False`, localhost-only `allowed_hosts`, sensitive header redaction, `REMOTE_ADDR`-only (no XFF).
- **Panel button** — Minimal footprint, opens detail page in new tab, no JS overhead.

---

## Recommended Priorities

1. **S1** — Add `capture_response_body: bool = True` config option. Default on for backward compat, but let users opt out.
2. **I1** — Stream non-HTML responses directly without buffering. Only buffer when `content-type` contains `text/html`.
3. **D1** — Add 2-3 responsive breakpoints (1-col mobile, 3-col tablet, 6-col desktop).
4. **I4/I5** — Add `logging.debug(...)` for silent failures in route discovery and profile parsing.
5. **I6** — Optimize pruning query.
