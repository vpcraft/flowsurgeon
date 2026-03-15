# Architecture

**Analysis Date:** 2026-03-14

## Pattern Overview

**Overall:** Middleware + Service Layers

FlowSurgeon uses a classic middleware pattern with abstract service layers. The system wraps HTTP applications (WSGI/ASGI) at the framework boundary, intercepts requests, collects profiling data, stores results, and optionally injects a UI panel. Architecture is **protocol-agnostic** — WSGI and ASGI implementations are parallel with shared core logic.

**Key Characteristics:**
- **Protocol abstraction:** Separate middleware layers for WSGI (`FlowSurgeonWSGI`) and ASGI (`FlowSurgeonASGI`) with identical responsibilities
- **Pluggable backends:** Storage and query tracking use abstract base classes for extensibility
- **Context-scoped collection:** Request-specific data (queries, profiling) is collected via contextvars (works for both sync and async)
- **Factory pattern entry:** `FlowSurgeon()` factory auto-detects WSGI vs ASGI by inspecting coroutine status
- **Optional UI injection:** HTML responses receive an embedded debug panel; static routes serve history/detail pages

## Layers

**Middleware (Entry Point):**
- Purpose: Accept HTTP requests, route to debug UI or profile request, inject panel, manage lifecycle
- Location: `src/flowsurgeon/middleware/asgi.py`, `src/flowsurgeon/middleware/wsgi.py`
- Contains: `FlowSurgeonASGI`, `FlowSurgeonWSGI` classes with request routing and response interception
- Depends on: Config, Storage, QueryTrackers, UI renderers, Profiling
- Used by: Application code (Flask, FastAPI, etc.)

**Core (Models & Configuration):**
- Purpose: Define data structures and settings
- Location: `src/flowsurgeon/core/`
- Contains: `Config` dataclass, `RequestRecord`, `QueryRecord`, `ProfileStat` dataclasses
- Depends on: Nothing (pure data)
- Used by: All other layers

**Trackers (Query Instrumentation):**
- Purpose: Hook into database libraries and capture query execution timing
- Location: `src/flowsurgeon/trackers/`
- Contains: Abstract `QueryTracker`, concrete `DBAPITracker`, `SQLAlchemyTracker`, context management (`ContextVar`-based query list)
- Depends on: Core records
- Used by: Middleware (installed at startup, called via context during requests)

**Storage (Persistence):**
- Purpose: Persist and retrieve request records from local database
- Location: `src/flowsurgeon/storage/`
- Contains: Abstract `StorageBackend`, concrete `SQLiteBackend`, `AsyncSQLiteBackend`
- Depends on: Core records
- Used by: Middleware (on every request), UI layer (for history/detail views)

**UI (Debug Panel & History):**
- Purpose: Render HTML debug panel, history page, detail pages; serve static assets
- Location: `src/flowsurgeon/ui/`
- Contains: Jinja2 template environment, render functions, route discovery, asset loading
- Depends on: Core records, Storage
- Used by: Middleware for response injection and route serving

**Profiling (Call Stack Analysis):**
- Purpose: Parse cProfile output and extract per-request performance hotspots
- Location: `src/flowsurgeon/profiling.py`
- Contains: `_parse_profile()` function, stdlib/third-party filtering
- Depends on: Core records, Config
- Used by: Middleware (optional, if `enable_profiling=True`)

**HTTP Utilities:**
- Purpose: Shared parsing and header handling
- Location: `src/flowsurgeon/_http.py`
- Contains: Query string parsing, body decoding, MIME type map, IPv6 zone stripping
- Depends on: Nothing (pure utilities)
- Used by: Middleware, UI

## Data Flow

**Request Profiling (Happy Path):**

1. Client → HTTP request hits app
2. Middleware `__call__` receives request (scope/receive/send for ASGI, environ/start_response for WSGI)
3. Pre-checks: enabled flag, allowed host, static file, debug UI route
4. If not debug UI:
   - Create `RequestRecord` with method, path, headers
   - Start query collection (`begin_query_collection()`) — pushes empty list to ContextVar
   - Start cProfile if `enable_profiling=True`
   - Call wrapped app with capturing proxy (intercepts response headers/body)
   - Time entire duration
5. App executes:
   - Database queries trigger `DBAPITracker` instrumented cursors
   - Queries append to the ContextVar-scoped list (visible to tracker via `get_current_queries()`)
   - Response is buffered (text) or streamed (binary)
6. After app returns:
   - Profiling disabled, profile stats parsed via `_parse_profile()`
   - Query collection ended, ContextVar reset
   - Record populated: duration, status, headers, queries, profile stats
   - Record persisted to Storage (enqueued for async write if ASGI)
   - If HTML response: panel HTML rendered and injected before `</body>`
   - Response returned to client

**Debug UI Navigation:**

1. Client → GET `/flowsurgeon` (or `/flowsurgeon/`)
2. Middleware matches debug route
3. Calls `_serve_history()` → fetches up to 500 records from Storage
4. Renders `render_history_page()` with sorting/filtering UI
5. Client clicks request ID
6. Middleware matches `/flowsurgeon/{request_id}`
7. Calls `_serve_detail()` → fetches single record, renders tabs (details/queries/profile)

**State Management:**

- **Per-Request Query List:** `ContextVar[list[QueryRecord]]` in `trackers.context`. Scoped to async task (ASGI) or thread-local (WSGI). Middleware sets on entry, resets on exit.
- **Request Record:** Local variable in middleware, populated during request, written to Storage after response.
- **Route Cache:** Built once in middleware `__init__`, stored as `_app_routes`.

## Key Abstractions

**StorageBackend:**
- Purpose: Decouple request persistence from middleware logic
- Examples: `src/flowsurgeon/storage/sqlite.py` (thread-safe sync), `src/flowsurgeon/storage/async_sqlite.py` (async)
- Pattern: Abstract base class with `save()`, `get()`, `list_recent()`, `prune()`, `close()`
- New backends can be swapped at middleware init: `FlowSurgeon(app, storage=CustomBackend())`

**QueryTracker:**
- Purpose: Hook into a specific DB library and append queries to active context
- Examples: `src/flowsurgeon/trackers/dbapi.py` (DB-API 2.0), `src/flowsurgeon/trackers/sqlalchemy.py`
- Pattern: Abstract `install()`/`uninstall()`, tracker appends to context via `get_current_queries()`
- New trackers extend this, called with: `FlowSurgeon(app, trackers=[MyTracker()])`

**Config:**
- Purpose: Centralize all knobs (enabled, routes, db path, header stripping, profiling settings)
- Pattern: Dataclass with sensible defaults and env var overrides
- Mutations: Minimal; most fields read-only after init (except `known_routes`, populated by middleware)

## Entry Points

**`FlowSurgeon()` Factory:**
- Location: `src/flowsurgeon/__init__.py`
- Triggers: Application startup (decorator or explicit wrap)
- Responsibilities: Detect ASGI vs WSGI, instantiate appropriate middleware class, return wrapped app

**`FlowSurgeonASGI.__call__(scope, receive, send)`:**
- Location: `src/flowsurgeon/middleware/asgi.py:84`
- Triggers: Every HTTP request (for ASGI apps)
- Responsibilities: Route to debug UI or profile, call app, handle response

**`FlowSurgeonWSGI.__call__(environ, start_response)`:**
- Location: `src/flowsurgeon/middleware/wsgi.py:90`
- Triggers: Every HTTP request (for WSGI apps)
- Responsibilities: Route to debug UI or profile, call app, handle response

## Error Handling

**Strategy:** Graceful degradation. Errors in profiling, storage, or tracking do not crash the app.

**Patterns:**

- **Profiling failures:** `_parse_profile()` catches exceptions and logs, returns empty stats list
- **Storage failures (async):** `enqueue()` writes to queue; exceptions logged; request still served
- **Tracker failures:** Installed once at init; if hook fails, app is already compromised — logged and re-raised
- **Missing records:** History/detail views return empty list or 404 if record missing
- **Body decoding:** Falls back to latin-1 if UTF-8 fails; truncates at 128 KB

## Cross-Cutting Concerns

**Logging:** Uses stdlib `logging` module with logger name per module (e.g., `logging.getLogger(__name__)`). Level defaults to INFO; DEBUG for route discovery.

**Validation:**
- Path traversal guards in static file serving (check for `..`, `/`, `\`)
- Client host validation against `allowed_hosts` list (rejects X-Forwarded-For)
- Query string parsing with safe defaults

**Authentication:** Header-based. `allowed_hosts` checks REMOTE_ADDR (WSGI) or scope[`client`] (ASGI) — not user-supplied headers. Sensitive headers (`Authorization`, `Cookie`) redacted before storage.

**Performance:**
- Query buffering for text responses, streaming for binary (no double-buffer)
- Async storage writes (ASGI) vs sync (WSGI)
- Optional cProfile with ~1-10% overhead (disabled by default)
- SQLite WAL mode for concurrent reads
- Max stored requests auto-pruned

---

*Architecture analysis: 2026-03-14*
