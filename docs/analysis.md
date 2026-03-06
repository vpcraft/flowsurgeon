# FlowSurgeon — Idea Analysis

## Concept

FlowSurgeon is a framework-agnostic Python profiling middleware — inspired by django-debug-toolbar but not tied to Django or any specific framework. It collects request profiling data, database query statistics, and other runtime metrics, then surfaces them via an HTML panel injected into responses (or a dedicated debug endpoint). SQLite is used for persistent storage of historical data.

---

## Feasibility

**Highly feasible.** Python has well-established primitives for every part of this:

- `cProfile` / `time.perf_counter()` for timing and CPU profiling
- `tracemalloc` for memory profiling
- `sqlite3` (stdlib) for persistence — no extra dependency needed
- WSGI and ASGI middleware protocols are both well-defined and stable
- Response HTML injection is standard practice (django-debug-toolbar, werkzeug debugger)

The hardest part is **database query interception**, which is inherently driver/ORM-specific. This is solvable but requires explicit integrations rather than a single magic hook.

---

## Core Invariants (confirmed)

| Invariant | Status |
|---|---|
| Framework-agnostic | Valid. Support both WSGI and ASGI middleware protocols. |
| Profiling (timing, CPU) | Valid. Use `cProfile` + `time.perf_counter`. |
| Database query tracking | Valid with caveats — see below. |
| HTML panel in browser | Valid. Inject only into `text/html` responses. |
| SQLite persistence | Valid. Use stdlib `sqlite3`. Async writes need care. |
| No Django dependency | Valid. Keep Django as an optional integration, not a requirement. |

---

## Issues and Recommendations

### 1. WSGI vs ASGI — must support both

Django-debug-toolbar only targets WSGI (Django). FlowSurgeon targets FastAPI (ASGI) and Flask (WSGI). These are fundamentally different calling conventions:

- **WSGI**: synchronous callable `(environ, start_response) -> iterable`
- **ASGI**: async callable `(scope, receive, send) -> None`

**Recommendation**: Implement two distinct middleware classes — `FlowSurgeonWSGI` and `FlowSurgeonASGI` — sharing the same core data collection and storage logic. Provide a unified `FlowSurgeon` factory that auto-detects or accepts a `mode` argument.

### 2. Database query tracking is ORM/driver-specific

There is no universal Python hook for "a SQL query was executed." Each integration layer requires its own approach:

- **SQLAlchemy**: Use `event.listen(engine, "before_cursor_execute", ...)` and `"after_cursor_execute"`. Clean, non-invasive.
- **Raw DB-API 2.0** (psycopg2, sqlite3, etc.): Monkey-patch `cursor.execute`. More fragile, requires care.
- **Django ORM**: Hook into `django.db.backends` signals (`connection_created`). Optional integration.
- **Tortoise ORM / Beanie / others**: Each needs its own thin adapter.

**Recommendation**: Define a `QueryTracker` interface. Ship built-in adapters for SQLAlchemy and raw DB-API 2.0. Make adapters for other ORMs optional/pluggable. Do not promise "automatic" DB tracking — users must register the adapter for their stack.

### 3. HTML injection must be conditional

Injecting a debug panel HTML fragment into every response is wrong for:

- `application/json` responses (API endpoints)
- Binary/streaming responses
- Responses where `Content-Length` was already set

**Recommendation**: Only inject when `Content-Type: text/html` is present in the response. For JSON/API-only apps, provide a standalone debug route (`/__flowsurgeon__/`) that serves the panel separately. Injection should be the default only for HTML responses; the dedicated route is always available.

### 4. SQLite concurrency under async workloads

SQLite with default settings is not safe under high-concurrency async usage (multiple coroutines writing simultaneously).

**Recommendation**:
- Use `WAL` journal mode (`PRAGMA journal_mode=WAL`) — significantly improves concurrent reads.
- Use a single write-serialized queue (asyncio queue + background writer task) for ASGI contexts.
- For WSGI, standard thread-local connections are sufficient.
- Add a max-rows cap and auto-pruning (e.g., keep last 1000 requests) to prevent unbounded growth.

### 5. Overhead and production safety

Profiling adds real overhead. Leaving it on in production is a security risk (exposes internals) and a performance liability.

**Recommendation**:
- Default `enabled=False`. Require explicit opt-in.
- Provide an `allowed_hosts` config (default: `["127.0.0.1", "::1"]`) — only serve the panel to localhost.
- Add a master `FLOWSURGEON_ENABLED` environment variable as a kill switch.
- Strip sensitive headers (Authorization, Cookie) from stored data by default, with a `strip_sensitive=True` default.

### 6. Async-safe profiling

`cProfile` is not async-aware — it profiles wall time across all coroutines, not per-request CPU time.

**Recommendation**: For ASGI, use `time.perf_counter()` for wall-clock timing per request. Reserve `cProfile` for WSGI where synchronous execution makes it meaningful. Document this distinction clearly.

### 7. Panel data model

Define a clear, versioned schema from day one. Each request produces a `RequestRecord` with:

```
request_id (uuid)
timestamp
method, path, status_code
duration_ms
queries: [{sql, duration_ms, stack_trace?}]
query_count, query_time_ms
cpu_time_ms (WSGI only)
memory_delta_kb
log_messages: [{level, message}]
```

Storing structured data (JSON columns in SQLite) alongside indexed scalar fields enables both fast lookup and flexible panel rendering.

---

## What to Avoid

- **Do not** auto-instrument everything magically. Explicit registration is safer and more debuggable.
- **Do not** use a heavy dependency (Redis, Postgres) for default storage. SQLite is the right default.
- **Do not** build a JavaScript-heavy frontend initially. A server-rendered HTML panel with minimal vanilla JS is simpler, faster, and avoids build tooling.
- **Do not** tie the panel UI to any CSS framework. Inline styles or a single bundled CSS file keeps the panel self-contained and conflict-free.
