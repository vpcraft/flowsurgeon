# Testing Patterns

**Analysis Date:** 2026-03-14

## Test Framework

**Runner:**
- pytest 9.0.2+ (from `pyproject.toml`: `dev = ["pytest>=9.0.2", "pytest-asyncio>=1.3.0", "pytest-cov>=7.0.0"]`)
- Config: `pyproject.toml` under `[tool.pytest.ini_options]` at lines 41-43:
  ```
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  ```

**Assertion Library:**
- Built-in Python assertions (no external library; stdlib sufficient)

**Run Commands:**
```bash
pytest tests/                          # Run all tests
pytest tests/ -v                       # Verbose output
pytest tests/ --cov=src/flowsurgeon   # Coverage report
pytest tests/test_query_tracking.py    # Run single file
pytest tests/ -k test_execute          # Run tests matching pattern
```

## Test File Organization

**Location:**
- All tests in `tests/` directory at project root
- Mirrors conceptual structure but flat organization

**Naming:**
- Test files: `test_*.py` pattern (e.g., `test_query_tracking.py`, `test_wsgi.py`, `test_asgi.py`, `test_profiling.py`)
- Test classes: `Test*` PascalCase (e.g., `TestQueryContext`, `TestDBAPITracker`, `TestWSGIWithTracker`)
- Test methods: `test_*` lowercase (e.g., `test_default_is_none`, `test_execute_records_query_in_context`)

**Structure:**
```
tests/
├── __init__.py
├── test_query_tracking.py      # Context, DBAPITracker, SQLAlchemyTracker tests
├── test_wsgi.py                # WSGI middleware integration tests
├── test_asgi.py                # ASGI middleware integration tests
└── test_profiling.py           # cProfile integration, parsing, and serialization tests
```

## Test Structure

**Suite Organization:**
Tests organize into test classes grouped by functionality, with setup helpers at module level. From `tests/test_query_tracking.py`:

```python
# Module docstring explaining test scope
"""Tests for v0.3.0 query tracking (DBAPITracker, SQLAlchemyTracker, context)."""

from __future__ import annotations

# Standard library imports
import asyncio
import io
import sqlite3

import pytest

# Local imports
from flowsurgeon import Config, FlowSurgeonASGI, FlowSurgeonWSGI
from flowsurgeon.core.records import QueryRecord
...

# ---------------------------------------------------------------------------
# Minimal WSGI/ASGI JSON app helpers
# ---------------------------------------------------------------------------

def _make_wsgi_environ(path: str = "/", remote_addr: str = "127.0.0.1") -> dict:
    """Helper to create WSGI environ dict."""
    return {...}

def _wsgi_json_app(environ, start_response):
    """Minimal WSGI app that returns JSON."""
    ...

# ---------------------------------------------------------------------------
# Context variable tests
# ---------------------------------------------------------------------------

class TestQueryContext:
    """Tests for context variable management."""

    def test_default_is_none(self):
        assert get_current_queries() is None

    def test_begin_returns_empty_list_and_token(self):
        queries, token = begin_query_collection()
        ...
```

**Patterns:**

1. **Module-level helpers:** Prefixed with underscore, appear before test classes
   - `_make_wsgi_environ()` - creates WSGI environ dicts for testing
   - `_make_scope()` - creates ASGI scope dicts for testing
   - `_call_wsgi()` - invokes WSGI apps and captures responses
   - `_call_asgi()` - invokes ASGI apps and captures responses
   - `_run_and_profile()` - profiles functions and returns stats
   - `_fib()` - test target for profiling (synthetic workload)

2. **Test classes:** Organize related tests together
   - `TestQueryContext` - context variable behavior
   - `TestDBAPITracker` - single tracker unit tests
   - `TestWSGIWithTracker` - middleware + tracker integration
   - `TestASGIWithTracker` - async middleware + tracker integration
   - `TestSQLAlchemyTracker` - SQLAlchemy-specific tracking

3. **Fixtures:** `@pytest.fixture` for shared setup
   - `tmp_path` - pytest built-in, creates temp directory for DB files
   - `sa_engine` - creates temporary SQLAlchemy engine with schema

   From `tests/test_query_tracking.py` lines 351-360:
   ```python
   @pytest.fixture
   def sa_engine(tmp_path):
       pytest.importorskip("sqlalchemy")
       from sqlalchemy import create_engine, text

       engine = create_engine(f"sqlite:///{tmp_path}/sa.db")
       with engine.connect() as conn:
           conn.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)"))
           conn.commit()
       return engine
   ```

4. **Section separators:** Dashes organize test classes
   ```python
   # ---------------------------------------------------------------------------
   # Context variable tests
   # ---------------------------------------------------------------------------
   ```

## Mocking

**Framework:** No explicit mocking library used (pytest-mock or unittest.mock not in dependencies)

**Patterns:**
- **Minimal test apps:** Custom WSGI/ASGI apps built inline for testing
  - `_wsgi_json_app()` - minimal WSGI that returns `{"ok": true}`
  - `_asgi_json_app()` - minimal ASGI equivalent

  From `tests/test_query_tracking.py` lines 44-49:
  ```python
  def _wsgi_json_app(environ, start_response):
      body = b'{"ok": true}'
      start_response(
          "200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))]
      )
      return [body]
  ```

- **State capture via closures:** Tests using mutable default lists to capture app state
  - From `tests/test_query_tracking.py` lines 226-246:
    ```python
    def test_multiple_requests_isolated(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))
        call_count = [0]  # Closure captures count

        def counting_app(environ, start_response):
            call_count[0] += 1
            for _ in range(call_count[0]):
                tracker.connection.cursor().execute("SELECT 1")
            return _wsgi_json_app(environ, start_response)
    ```

- **In-memory SQLite:** All DB tests use `:memory:` or temporary files
  - `sqlite3.connect(":memory:")` for single-connection tests
  - Temp files for multi-threaded storage tests

**What to Mock:**
- Nothing is mocked; tests use real implementations throughout
- Rationale: Small scope (middleware + trackers), no external services

**What NOT to Mock:**
- Storage backends (use real SQLite)
- Database connections (use real sqlite3 or in-memory)
- WSGI/ASGI environments (built with simple test apps)

## Fixtures and Factories

**Test Data:**

From `tests/test_profiling.py` lines 29-38:
```python
def _run_and_profile(target, config: Config | None = None) -> list[ProfileStat]:
    """Profile *target()* and return parsed stats."""
    cfg = config or Config(enable_profiling=True, profile_user_code_only=False, profile_top_n=0)
    prof = cProfile.Profile()
    prof.enable()
    try:
        target()
    finally:
        prof.disable()
    return _parse_profile(prof, cfg)
```

**Dataclass Factories:**

From `tests/test_profiling.py` lines 393-422:
```python
def test_sqlite_profile_stats_roundtrip(tmp_path):
    """ProfileStat serialises to SQLite and deserialises correctly."""
    from flowsurgeon.core.records import ProfileStat
    from flowsurgeon.storage.sqlite import SQLiteBackend

    db_path = str(tmp_path / "roundtrip.db")
    backend = SQLiteBackend(db_path)

    stats = [
        ProfileStat(
            file="app/views.py",
            line=42,
            func="get_books",
            prim_calls=1,
            calls=1,
            tt_ms=0.3,
            ct_ms=14.2,
            callers=[("app/router.py", "dispatch", 19, 14.2)],
        ),
        ProfileStat(...),
    ]

    record = RequestRecord(
        method="GET",
        path="/books",
        status_code=200,
        duration_ms=15.0,
        profile_stats=stats,
    )
```

**Location:**
- Fixtures with `@pytest.fixture` decorator in test files
- Helper factories as module-level functions prefixed with `_`

## Coverage

**Requirements:** No explicit coverage requirements enforced; coverage reporting available

**View Coverage:**
```bash
pytest tests/ --cov=src/flowsurgeon --cov-report=html
pytest tests/ --cov=src/flowsurgeon --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and small classes in isolation
- Examples:
  - `TestQueryContext.test_default_is_none()` - context state verification
  - `TestDBAPITracker.test_execute_records_query_in_context()` - single tracker operation
  - `test_parse_profile_top_n()` - profiling utility behavior
- No external dependencies; use real in-memory SQLite

**Integration Tests:**
- Scope: Middleware + tracker interactions, end-to-end request flow
- Examples:
  - `TestWSGIWithTracker.test_queries_attached_to_record()` - middleware + DBAPITracker
  - `test_wsgi_profiling_populates_record()` - WSGI middleware with profiling
  - `test_asgi_profiling_populates_record()` - ASGI middleware with profiling
- Tests with real middleware instances handling synthetic requests

**Async Tests:**
- Framework: pytest-asyncio (configured in `pyproject.toml`)
- Marker: `@pytest.mark.asyncio` on async test methods
- Execution: `asyncio_mode = "auto"` allows direct `async def test_*()` methods

Example from `tests/test_query_tracking.py` lines 298-318:
```python
@pytest.mark.asyncio
class TestASGIWithTracker:
    async def test_queries_attached_to_record(self, tmp_path):
        tracker = DBAPITracker(sqlite3.connect(":memory:"))

        async def app_with_query(scope, receive, send):
            tracker.connection.cursor().execute("SELECT 42")
            await _asgi_json_app(scope, receive, send)

        cfg = _enabled_cfg(tmp_path)
        storage = AsyncSQLiteBackend(cfg.db_path)
        middleware = FlowSurgeonASGI(
            app_with_query, config=cfg, storage=storage, trackers=[tracker]
        )

        await _call_asgi(middleware)
        await storage._queue.join()
        records = await storage.list_recent()
        assert len(records[0].queries) == 1
```

## Common Patterns

**Async Testing:**

Pattern: Mark entire test class with `@pytest.mark.asyncio`, or individual methods.
- Use `async def` for test methods
- Await async operations naturally
- Fixtures work with async tests via pytest-asyncio
- Concurrent execution: `asyncio.gather(coro1, coro2, coro3)` for concurrent test scenarios

From `tests/test_query_tracking.py` lines 320-343:
```python
@pytest.mark.asyncio
class TestASGIWithTracker:
    async def test_concurrent_requests_isolated(self, tmp_path):
        ...
        await asyncio.gather(
            _call_asgi(middleware, path="/3"),
            _call_asgi(middleware, path="/1"),
            _call_asgi(middleware, path="/2"),
        )
        await storage._queue.join()
```

**Error Testing:**

Pattern: No explicit error tests; tests verify absence of errors in normal flows.
- Safe exception handling tested implicitly (e.g., trackers don't raise when called outside context)
- Query recording without context doesn't raise: `test_no_recording_outside_context()`

**Configuration Testing:**

Pattern: Pass `Config` objects with specific flags to test conditional behavior.
- `track_queries=False` disables query collection
- `enable_profiling=True/False` controls profiling
- `profile_user_code_only=True/False` controls frame filtering

From `tests/test_query_tracking.py` lines 270-290:
```python
def test_track_queries_false_skips_collection(self, tmp_path):
    tracker = DBAPITracker(sqlite3.connect(":memory:"))

    def app_with_query(environ, start_response):
        tracker.connection.cursor().execute("SELECT 99")
        return _wsgi_json_app(environ, start_response)

    cfg = Config(
        enabled=True,
        db_path=str(tmp_path / "t.db"),
        allowed_hosts=["127.0.0.1"],
        track_queries=False,
    )
    ...
    assert storage.list_recent()[0].queries == []
```

**Parametrization:**

Pattern: Not heavily used; tests are explicit and named descriptively instead.
- Each test method tests one specific behavior
- Test names describe the condition being tested

---

*Testing analysis: 2026-03-14*
