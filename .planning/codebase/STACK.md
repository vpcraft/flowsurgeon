# Technology Stack

**Analysis Date:** 2026-03-14

## Languages

**Primary:**
- Python 3.12+ - Core middleware implementation, WSGI/ASGI support

**Secondary:**
- HTML/Jinja2 - Debug UI templates (`src/flowsurgeon/ui/templates/`)
- JavaScript - Alpine.js for interactive SPA (`src/flowsurgeon/ui/assets/alpine.min.js`)
- CSS - Debug panel styling (`src/flowsurgeon/ui/assets/panel.css`)

## Runtime

**Environment:**
- Python 3.12 (minimum required, specified in `pyproject.toml` with `requires-python = ">=3.12"`)
- Configured via `.python-version` file (contains: `3.12`)

**Package Manager:**
- uv (uses `uv.lock` lockfile for reproducible builds)
- Alternative: pip (supported)

## Frameworks

**Core:**
- Jinja2 3.1.0+ - Template engine for debug UI rendering (`src/flowsurgeon/ui/panel.py` imports from `jinja2`)

**Web Framework Support (not direct dependencies, but target frameworks):**
- FastAPI - ASGI framework support
- Flask - WSGI framework support
- Starlette - ASGI framework support (via FastAPI)

**Build/Dev:**
- uv_build 0.9.17-0.10.0 - Build backend for packaging

## Key Dependencies

**Critical:**
- jinja2 >=3.1.0 - Only required runtime dependency; used for rendering debug UI templates at `src/flowsurgeon/ui/templates/`

**Development:**
- pytest >=9.0.2 - Test runner (configured in `pyproject.toml` with `testpaths = ["tests"]`)
- pytest-asyncio >=1.3.0 - Async test support (configured with `asyncio_mode = "auto"`)
- pytest-cov >=7.0.0 - Coverage reporting

**Examples/Optional:**
- fastapi >=0.135.1 - FastAPI demo (`examples/fastapi/demo_fastapi.py`)
- flask >=3.1.3 - Flask demo (`examples/flask/demo_flask.py`)
- sqlalchemy >=2.0 - SQLAlchemy ORM demo integration (`src/flowsurgeon/trackers/sqlalchemy.py`)
- uvicorn >=0.41.0 - ASGI server for running examples

## Configuration

**Environment:**
- FLOWSURGEON_ENABLED - Master enable/disable switch (default: False)
  - Set via environment variable or `Config(enabled=True)` parameter
  - Parsed in `src/flowsurgeon/core/config.py` by `_env_bool()` function
- FLOWSURGEON_PROFILING - Enable call-stack profiling (default: False)
  - Optional performance feature controlled at runtime

**Build:**
- `pyproject.toml` - Main project config with dependencies, metadata, tool configs
- `[tool.ruff]` section - Linting config with line-length = 100
- `[tool.pytest.ini_options]` section - Test discovery and asyncio mode

## Platform Requirements

**Development:**
- Python 3.12+
- Linux/Mac/Windows (OS-independent per classifiers)
- SQLite3 (included in Python stdlib)

**Production:**
- Python 3.12+
- WSGI or ASGI web server (uvicorn, gunicorn, etc.)
- SQLite3 for request history storage (local filesystem database)

## Profiling Support

**cProfile Integration:**
- Stdlib `cProfile` module used for per-request call-stack profiling
- Implemented in `src/flowsurgeon/profiling.py`
- Optional feature controlled by `Config(enable_profiling=True)` or `FLOWSURGEON_PROFILING=1`
- Adds ~1-10% overhead when enabled

## Database

**Storage:**
- SQLite 3 (no external database required)
- Two backend implementations:
  - `src/flowsurgeon/storage/sqlite.py` - Thread-safe synchronous backend (WSGI)
  - `src/flowsurgeon/storage/async_sqlite.py` - Async backend (ASGI)
- Schema created automatically with tables for: requests, queries, profile stats, response bodies
- WAL (Write-Ahead Logging) mode for better concurrent read performance

---

*Stack analysis: 2026-03-14*
