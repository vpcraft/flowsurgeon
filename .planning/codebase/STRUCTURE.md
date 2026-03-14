# Codebase Structure

**Analysis Date:** 2026-03-14

## Directory Layout

```
flowsurgeon/
├── src/flowsurgeon/              # Main package
│   ├── __init__.py               # Public API + factory
│   ├── core/                     # Data models & configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Config dataclass
│   │   └── records.py            # RequestRecord, QueryRecord, ProfileStat
│   ├── middleware/               # HTTP middleware (protocol-specific)
│   │   ├── __init__.py
│   │   ├── asgi.py               # FlowSurgeonASGI class
│   │   └── wsgi.py               # FlowSurgeonWSGI class
│   ├── storage/                  # Persistence layer (abstract + backends)
│   │   ├── __init__.py
│   │   ├── base.py               # StorageBackend ABC
│   │   ├── sqlite.py             # SQLiteBackend (sync, thread-safe)
│   │   └── async_sqlite.py       # AsyncSQLiteBackend (ASGI-compatible)
│   ├── trackers/                 # Database instrumentation
│   │   ├── __init__.py
│   │   ├── base.py               # QueryTracker ABC
│   │   ├── context.py            # ContextVar for per-request queries
│   │   ├── dbapi.py              # DBAPITracker (sqlite3, psycopg2, etc.)
│   │   └── sqlalchemy.py         # SQLAlchemyTracker
│   ├── ui/                       # Debug panel & history UI
│   │   ├── __init__.py
│   │   ├── panel.py              # Rendering logic + route discovery
│   │   ├── assets/               # CSS, JS, images
│   │   │   ├── panel.css
│   │   │   ├── panel.js
│   │   │   └── (favicon, etc.)
│   │   └── templates/            # Jinja2 templates
│   │       ├── panel.html        # Inline panel (injected into responses)
│   │       ├── history.html      # History/grid view
│   │       ├── detail.html       # Single request detail page
│   │       └── partials/         # Reusable template components
│   ├── profiling.py              # cProfile parsing & filtering
│   └── _http.py                  # Shared HTTP utilities
├── tests/                        # Test suite
│   └── (test files)
├── examples/                     # Usage examples
│   ├── flask/                    # Flask demo
│   └── fastapi/                  # FastAPI demo
├── docs/                         # Documentation
├── pyproject.toml                # Project metadata, dependencies
├── README.md                     # User documentation
└── LICENSE                       # MIT license
```

## Directory Purposes

**`src/flowsurgeon/`:**
- Purpose: Main package source code
- Contains: Middleware, storage backends, trackers, UI, utilities
- Key files: `__init__.py` (public API), `core/`, `middleware/`, `storage/`, `trackers/`, `ui/`

**`src/flowsurgeon/core/`:**
- Purpose: Core data structures and configuration
- Contains: `Config` dataclass, request/query/profile record definitions
- Key files: `config.py`, `records.py`

**`src/flowsurgeon/middleware/`:**
- Purpose: HTTP protocol-specific middleware implementations
- Contains: WSGI and ASGI middleware classes with request interception
- Key files: `asgi.py` (FlowSurgeonASGI), `wsgi.py` (FlowSurgeonWSGI)

**`src/flowsurgeon/storage/`:**
- Purpose: Request persistence layer (abstract + implementations)
- Contains: Base class, SQLite sync/async backends
- Key files: `base.py` (ABC), `sqlite.py`, `async_sqlite.py`

**`src/flowsurgeon/trackers/`:**
- Purpose: Database query instrumentation
- Contains: Query trackers for DB-API, SQLAlchemy; context management
- Key files: `base.py` (ABC), `dbapi.py`, `sqlalchemy.py`, `context.py`

**`src/flowsurgeon/ui/`:**
- Purpose: Debug panel rendering and history UI
- Contains: Jinja2 template rendering, route discovery, asset serving
- Key files: `panel.py` (all rendering + asset loading), `templates/`, `assets/`

**`src/flowsurgeon/ui/assets/`:**
- Purpose: Static files served from debug UI
- Contains: CSS, JavaScript, images
- Key files: `panel.css`, `panel.js` (Alpine.js SPA)

**`src/flowsurgeon/ui/templates/`:**
- Purpose: Jinja2 HTML templates for panel and history
- Contains: Panel (injected), history grid, detail pages
- Key files: `panel.html`, `history.html`, `detail.html`, `partials/`

**`tests/`:**
- Purpose: Unit and integration tests
- Contains: Test cases for middleware, storage, trackers, UI

**`examples/`:**
- Purpose: Reference implementations
- Contains: Flask and FastAPI demo apps
- Key files: `flask/`, `fastapi/`

## Key File Locations

**Entry Points:**
- `src/flowsurgeon/__init__.py`: `FlowSurgeon()` factory, public API exports
- `src/flowsurgeon/middleware/asgi.py`: `FlowSurgeonASGI.__call__()` (ASGI entry)
- `src/flowsurgeon/middleware/wsgi.py`: `FlowSurgeonWSGI.__call__()` (WSGI entry)

**Configuration:**
- `src/flowsurgeon/core/config.py`: `Config` dataclass with all settings
- `pyproject.toml`: Package metadata, dependencies, build config

**Core Logic:**
- `src/flowsurgeon/core/records.py`: Data structures (`RequestRecord`, `QueryRecord`, `ProfileStat`)
- `src/flowsurgeon/trackers/context.py`: `ContextVar`-based request query collection
- `src/flowsurgeon/profiling.py`: cProfile parsing and filtering
- `src/flowsurgeon/_http.py`: Shared HTTP utilities (query parsing, body decoding)

**Testing:**
- `tests/`: All test files (structure mirrors `src/`)

## Naming Conventions

**Files:**
- Module files use `snake_case`: `config.py`, `async_sqlite.py`, `panel.py`
- Private utilities: `_http.py` (underscore prefix)
- Template files use `.html`: `panel.html`, `history.html`
- Style files use `.css`: `panel.css`
- Script files use `.js`: `panel.js`

**Directories:**
- Package names use `snake_case`: `middleware`, `trackers`, `storage`, `ui`, `assets`, `templates`
- No nested packages beyond 3 levels (e.g., no `src/flowsurgeon/ui/templates/partials/components/`)

**Classes:**
- Concrete classes use `PascalCase`: `FlowSurgeonASGI`, `FlowSurgeonWSGI`, `SQLiteBackend`, `DBAPITracker`
- Abstract base classes use `PascalCase` with `ABC` suffix implied: `StorageBackend`, `QueryTracker`
- Private internal classes use leading underscore: `_TrackedConnection`, `_InstrumentedCursor`

**Functions:**
- Public functions use `snake_case`: `begin_query_collection()`, `discover_routes()`, `render_panel()`
- Private functions use leading underscore: `_parse_profile()`, `_status_class()`, `_load_asset_bytes()`
- Utility functions are prefixed by responsibility: `_parse_qs_param()`, `_decode_body()`, `_strip_ipv6_zone()`

**Constants:**
- All caps with underscores: `_MAX_BODY_STORE`, `_CREATE_TABLE`, `_HTML_CONTENT_TYPES`
- Module-scoped constants prefixed with `_` (private): `_MIME_TYPES`, `_HTTP_STATUS_TEXT`

## Where to Add New Code

**New Feature (e.g., new metric collection):**
- Primary code: `src/flowsurgeon/core/records.py` (add new field to `RequestRecord`), `src/flowsurgeon/middleware/` (capture logic)
- Tests: `tests/` (mirror structure)
- UI: `src/flowsurgeon/ui/templates/detail.html` (display), `src/flowsurgeon/ui/panel.py` (rendering logic)

**New Tracker Type (e.g., MongoDB):**
- Implementation: `src/flowsurgeon/trackers/mongodb.py` (extend `QueryTracker`)
- Tests: `tests/trackers/test_mongodb.py`
- Documentation: `examples/` (optional demo)

**New Storage Backend:**
- Implementation: `src/flowsurgeon/storage/redis.py` (extend `StorageBackend`)
- Tests: `tests/storage/test_redis.py`
- Public export: Add to `src/flowsurgeon/__init__.py` `__all__` list

**UI Enhancement (new filter, column, view):**
- Template: `src/flowsurgeon/ui/templates/history.html` or `detail.html`
- Rendering logic: `src/flowsurgeon/ui/panel.py` (add filter function or modify render function)
- Styling: `src/flowsurgeon/ui/assets/panel.css`
- Scripting: `src/flowsurgeon/ui/assets/panel.js` (Alpine.js)

**Utility Function:**
- Shared HTTP utils: `src/flowsurgeon/_http.py`
- Module-specific utils: Keep in the module (e.g., profiling helpers in `profiling.py`)

## Special Directories

**`.planning/codebase/`:**
- Purpose: GSD planning documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Generated: Via GSD tooling
- Committed: Yes

**`dist/`:**
- Purpose: Built distributions (wheels, sdists)
- Generated: By `pyproject.toml` build system
- Committed: No (in `.gitignore`)

**`tests/`:**
- Purpose: Test suite
- Generated: No
- Committed: Yes

**`examples/`:**
- Purpose: Reference implementations
- Generated: No (user-maintained)
- Committed: Yes

**`.venv/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`:**
- Purpose: Development environment artifacts
- Generated: Yes
- Committed: No (in `.gitignore`)

## Module Organization

**Import order (followed throughout codebase):**
1. `from __future__ import annotations` (enables PEP 563)
2. Standard library imports (`import os`, `from abc import ABC`)
3. Third-party imports (`from jinja2 import Environment`)
4. Local imports (`from flowsurgeon.core.config import Config`)

**Barrel files (when used):**
- `src/flowsurgeon/__init__.py`: Re-exports public API (Config, middleware classes, trackers)
- Other `__init__.py` files are minimal (mostly empty)

**Public API exposure:**
- All public classes and functions must be listed in `src/flowsurgeon/__init__.py` `__all__`
- Current exports: `Config`, `FlowSurgeon`, `FlowSurgeonASGI`, `FlowSurgeonWSGI`, `StorageBackend`, `SQLiteBackend`, `AsyncSQLiteBackend`, `QueryTracker`, `DBAPITracker`, `RequestRecord`, `QueryRecord`, `ProfileStat`

---

*Structure analysis: 2026-03-14*
