# FlowSurgeon — Development Plan

## Versioning Strategy

Follows [Semantic Versioning](https://semver.org/). Pre-1.0 minor versions introduce new features; patch versions fix bugs. No breaking changes within a minor version series.

---

## v0.1.0 — Foundation

**Goal**: A working WSGI middleware that captures request timing and injects a minimal HTML panel.

### Deliverables

- `FlowSurgeonWSGI` middleware class (pure WSGI callable)
- `RequestRecord` data class with fields: `request_id`, `timestamp`, `method`, `path`, `status_code`, `duration_ms`
- SQLite storage layer (`StorageBackend` base class + `SQLiteBackend` implementation)
  - WAL mode enabled
  - Auto-pruning: keep last 1000 records
- HTML panel injection (only when `Content-Type: text/html`)
- Dedicated debug route: `GET /__flowsurgeon__/` — lists recent requests
- Config: `enabled`, `allowed_hosts`, `db_path`, `max_stored_requests`
- `FLOWSURGEON_ENABLED` env var kill switch

### Non-goals for this version

- ASGI, database query tracking, profiling, memory tracking

### Directory structure

```
src/flowsurgeon/
  core/
    records.py        # RequestRecord dataclass
    config.py         # Config dataclass
  middleware/
    wsgi.py           # FlowSurgeonWSGI
  storage/
    base.py           # StorageBackend ABC
    sqlite.py         # SQLiteBackend
  ui/
    panel.py          # HTML rendering
    assets/
      panel.css
      panel.js
  __init__.py         # Public API: FlowSurgeonWSGI, Config
```

---

## v0.2.0 — ASGI Support

**Goal**: Full ASGI (FastAPI/Starlette) support with feature parity to v0.1.

### Deliverables

- `FlowSurgeonASGI` middleware class (ASGI `scope/receive/send` protocol)
- Async-safe SQLite writer: asyncio queue + background writer task
- `FlowSurgeon` factory function: `FlowSurgeon(app, mode="auto")` — detects WSGI vs ASGI
- Same panel and storage as v0.1, shared via common core

### Notes

- Timing is wall-clock only for ASGI (`time.perf_counter()` per request scope)
- Handle streaming ASGI responses: buffer only HTML responses; pass through all others

---

## v0.3.0 — SQL Query Tracking

**Goal**: Track database queries per request with count, timing, and query text.

### Deliverables

- `QueryTracker` interface (ABC): `install()`, `uninstall()`, `get_queries() -> list[QueryRecord]`
- `QueryRecord` dataclass: `sql`, `params`, `duration_ms`, `stack_trace` (optional, configurable)
- Built-in adapters:
  - `SQLAlchemyTracker`: hooks via SQLAlchemy engine events
  - `DBAPITracker`: monkey-patches `cursor.execute` on a DB-API 2.0 connection/pool
- Request-scoped query collection (context variable for ASGI, thread-local for WSGI)
- Panel: "SQL Queries" tab showing query list, total count, total time, duplicate detection
- Config additions: `track_queries`, `capture_query_stacktrace`, `slow_query_threshold_ms`

### Usage example

```python
from flowsurgeon import FlowSurgeon, SQLAlchemyTracker

app = FlowSurgeon(app, trackers=[SQLAlchemyTracker(engine)])
```

---

## v0.4.0 — Profiling Panel

**Goal**: CPU and memory profiling per request.

### Deliverables

- **CPU profiling** (WSGI only): wrap request handler with `cProfile.Profile()`, store top-N functions by cumulative time
- **Wall-clock breakdown**: always available for both WSGI and ASGI — time spent in middleware vs handler vs response serialization
- **Memory profiling**: use `tracemalloc` to capture memory delta across the request lifecycle
- `ProfilingRecord` dataclass: `cpu_time_ms`, `memory_delta_kb`, `top_functions: list[FunctionStat]`
- Panel: "Performance" tab with flame-style table (top functions sorted by time)
- Config additions: `enable_cpu_profiling` (default: False, WSGI only), `enable_memory_profiling`, `profile_top_n`

### Notes

- CPU profiling is disabled by default due to overhead (~10-30% slowdown)
- Memory profiling uses `tracemalloc.start()` lazily; checks if already started to avoid conflicts

---

## v0.5.0 — History and Search UI

**Goal**: Improve the debug endpoint into a usable request history browser.

### Deliverables

- `GET /__flowsurgeon__/` — paginated request list with method, path, status, duration, query count
- `GET /__flowsurgeon__/{request_id}` — full detail view for a single request (all panels)
- Basic filtering: by status code, path prefix, slow threshold
- Self-contained HTML (no external CDN dependencies); minimal vanilla JS for tab switching
- Response time histogram (last 100 requests) rendered as inline SVG

---

## v0.6.0 — Optional Integrations and Extensibility

**Goal**: Plugin API for third-party panels; additional ORM adapters.

### Deliverables

- `Panel` base class: `title`, `collect(record) -> PanelData`, `render(data) -> str`
- Plugin registration: `FlowSurgeon(app, panels=[MyPanel()])`
- Additional built-in adapters:
  - `TortoiseORMTracker`
  - `DjangoORMTracker` (optional `django` extra)
- Cache panel stub (tracks cache hits/misses via a wrapped cache client)
- Published `Panel` ABC in public API so third-party packages can ship panels

---

## v1.0.0 — Stable Release

**Goal**: Production-ready, documented, secure, performant.

### Deliverables

- Full documentation (installation, configuration reference, panel descriptions, adapter guide, plugin authoring)
- Security audit: confirm `allowed_hosts` enforcement, sensitive data redaction, no path traversal in debug routes
- Performance benchmark suite: measure overhead per middleware feature, publish results in docs
- `StorageBackend` alternatives documented: custom backends (e.g., in-memory for testing)
- Deprecation policy documented
- `py.typed` marker already present; verify all public APIs have complete type annotations
- Changelog complete for all versions

### Compatibility matrix at 1.0

| Framework | Protocol | Status |
|---|---|---|
| Flask | WSGI | Supported |
| Django (optional) | WSGI | Supported |
| FastAPI | ASGI | Supported |
| Starlette | ASGI | Supported |
| Pure WSGI app | WSGI | Supported |
| Pure ASGI app | ASGI | Supported |

---

## Cross-cutting Concerns (all versions)

- **Python**: `>=3.12` (as set in pyproject.toml)
- **Zero required dependencies**: all features use stdlib; adapters (SQLAlchemy, etc.) are optional extras declared in `pyproject.toml`
- **Testing**: each version ships with unit tests (pytest) and at minimum one integration test against a minimal Flask app (WSGI) and a minimal FastAPI app (ASGI)
- **Linting**: ruff (already configured per `.ruff_cache`)
- **CI**: add GitHub Actions workflow in v0.2.0 at the latest
