# External Integrations

**Analysis Date:** 2026-03-14

## APIs & External Services

**Web Frameworks (Passive Integration):**
- FastAPI - ASGI web framework
  - Integration via middleware wrapping `src/flowsurgeon/middleware/asgi.py`
  - Auto-route discovery from `app.routes`
  - Example: `examples/fastapi/demo_fastapi.py`
- Flask - WSGI web framework
  - Integration via middleware wrapping `src/flowsurgeon/middleware/wsgi.py`
  - Auto-route discovery from `app.url_map`
  - Example: `examples/flask/demo_flask.py`
- Starlette - ASGI framework
  - Integration via ASGI middleware (same as FastAPI)
  - Auto-route discovery supported
- Django - WSGI framework
  - Integration via WSGI middleware (not explicitly tested but framework-agnostic)

**Debugging/Observability (No External Service):**
- cProfile - Stdlib call-stack profiling (optional, local only)

## Data Storage

**Databases:**
- SQLite 3 - Local filesystem database for request history
  - Connection: Local file at path specified by `config.db_path` (default: `flowsurgeon.db`)
  - Client: Python stdlib `sqlite3` module
  - Schema: Tables for `requests`, automatic schema creation in `src/flowsurgeon/storage/sqlite.py`
  - Async support: `src/flowsurgeon/storage/async_sqlite.py` for ASGI applications

**Optional Database Tracking (Client-side, no external dependency):**
- SQLAlchemy ORM - SQL query tracking
  - Client: `src/flowsurgeon/trackers/sqlalchemy.py`
  - Uses SQLAlchemy engine events (`before_cursor_execute`, `after_cursor_execute`)
  - Not a required dependency; installed separately by users
  - Example: `examples/fastapi/demo_fastapi.py` uses SQLAlchemy with sqlite:///books_fastapi.db
- DB-API 2.0 connections - SQL query tracking for raw database connections
  - Client: `src/flowsurgeon/trackers/dbapi.py`
  - Supports: sqlite3, psycopg2 (PostgreSQL), and any DB-API 2.0 compliant driver
  - Transparent proxy pattern; users wrap their connection with `DBAPITracker(connection)`
  - Example: `examples/flask/demo_flask.py` uses sqlite3.connect() with DBAPITracker

**File Storage:**
- Local filesystem only - Stores SQLite database files locally
- No cloud storage integration
- Response bodies captured to SQLite (up to 128 KB for text/JSON/XML)

**Caching:**
- None - No explicit caching layer. All data persisted directly to SQLite.

## Authentication & Identity

**Auth Provider:**
- Custom implementation - No external auth provider integration
- Sensitive header redaction instead: Authorization, Cookie, Set-Cookie headers redacted before storage
- Configured via `Config(strip_sensitive_headers=[...])` in `src/flowsurgeon/core/config.py`
- Allowed hosts restriction via `Config(allowed_hosts=[...])` for debug UI access control (default: localhost only)

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service integration

**Logs:**
- Stdlib logging module - `logging.getLogger(__name__)` used throughout
  - Example: `_log = logging.getLogger(__name__)` in `src/flowsurgeon/profiling.py`
- Local request/query storage in SQLite (not external logging service)
- No structured logging provider integration

## CI/CD & Deployment

**Hosting:**
- Framework-agnostic - Works with any WSGI or ASGI server:
  - uvicorn (ASGI, used in examples)
  - gunicorn (WSGI/ASGI)
  - Any WSGI-compatible server (Flask development server, etc.)

**CI Pipeline:**
- GitHub Actions - `.github/` directory present
- Workflow files expected (not examined per scope)

**Package Distribution:**
- PyPI - Published as `flowsurgeon` package
- Version 0.5.0 at release

## Environment Configuration

**Required env vars:**
- FLOWSURGEON_ENABLED - Master enable switch (default: False via environment or code)
- FLOWSURGEON_PROFILING - Enable profiling (default: False, optional)

**Optional configuration via code:**
- `Config(db_path="...")` - Custom SQLite database location
- `Config(allowed_hosts=[...])` - Restrict debug UI access to specific hosts
- `Config(debug_route="/...")` - Custom debug UI URL path
- `Config(slow_query_threshold_ms=100.0)` - Slow query detection threshold
- `Config(max_stored_requests=1000)` - Request history retention limit

**Secrets location:**
- No explicit secrets management required - Sensitive headers redacted automatically
- Database credentials not needed (SQLite uses local files)
- No API keys or external service credentials used

## Webhooks & Callbacks

**Incoming:**
- None - FlowSurgeon is a middleware, not a webhook receiver

**Outgoing:**
- None - No outbound webhook calls or external notifications

## Route Discovery

**Auto-discovery Patterns:**
- Flask: Routes extracted from `app.url_map`
- FastAPI/Starlette: Routes extracted from `app.routes`
- Function: `discover_routes(app)` in `src/flowsurgeon/ui/panel.py`
- Manual registration: `Config(known_routes=[("GET", "/path"), ...])` for framework-agnostic cases

## Query Tracking Integrations

**SQLAlchemy Tracker (`src/flowsurgeon/trackers/sqlalchemy.py`):**
- Hooks: `before_cursor_execute`, `after_cursor_execute` events
- Captures: SQL statement, parameters, execution duration, optional stack trace
- Installation: `SQLAlchemyTracker(engine).install()`
- Optional stacktrace: `capture_stacktrace=True` for per-query call stacks

**DB-API Tracker (`src/flowsurgeon/trackers/dbapi.py`):**
- Pattern: Transparent proxy wrapping native DB connection
- Captures: All `cursor().execute()` calls automatically
- No monkey-patching required
- Usage: Replace raw connection with `tracker.connection` everywhere

**Base Tracker Interface (`src/flowsurgeon/trackers/base.py`):**
- Abstract class for custom tracker implementations
- Methods: `install()`, `uninstall()`
- Query context: Uses contextvars for async-safe request-scoped collection

---

*Integration audit: 2026-03-14*
