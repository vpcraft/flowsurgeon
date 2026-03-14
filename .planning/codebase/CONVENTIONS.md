# Coding Conventions

**Analysis Date:** 2026-03-14

## Naming Patterns

**Files:**
- Lowercase with underscores for modules: `config.py`, `wsgi.py`, `async_sqlite.py`
- Test files use `test_` prefix: `test_query_tracking.py`, `test_profiling.py`
- Private/internal modules use leading underscore: `_http.py`

**Functions:**
- Lowercase with underscores: `begin_query_collection()`, `_strip_ipv6_zone()`, `_short_path()`
- Private functions use leading underscore: `_env_bool()`, `_run_and_profile()`, `_client_host()`
- Async functions follow same pattern: `async def _profile_request()`, `async def _call_app()`

**Variables:**
- Lowercase with underscores: `client_host`, `request_id`, `config`, `queries`
- Private instance variables use leading underscore: `self._app`, `self._config`, `self._storage`
- Magic/dunder methods preserved: `__call__`, `__init__`, `__getattr__`, `__setattr__`
- Type hints use modern Python 3.12+ syntax: `Config | None`, `list[str]`, `dict[str, str]`

**Classes:**
- PascalCase: `FlowSurgeonWSGI`, `FlowSurgeonASGI`, `DBAPITracker`, `SQLiteBackend`
- Private helper classes use leading underscore: `_TrackedConnection`, `_InstrumentedCursor`, `_StorageQueue`
- Abstract base classes inherit from `ABC`: `class StorageBackend(ABC)`

**Type Aliases:**
- Uppercase or PascalCase: `Environ = dict`, `StartResponse = Callable[[str, list[tuple[str, str]]], None]`, `WSGIApp = Callable[[Environ, StartResponse], Iterable[bytes]]`

## Code Style

**Formatting:**
- Line length: 100 characters (configured in `pyproject.toml`)
- Ruff is used for linting (see `[tool.ruff]` in `pyproject.toml`)
- Future annotations: All modules use `from __future__ import annotations` for forward-compatible type hints

**Linting:**
- Ruff linter active with 100-character line limit
- Configuration in `pyproject.toml` at `[tool.ruff]`

**Import Organization:**

Order of imports:
1. Docstring (module-level docstring)
2. `from __future__ import annotations` (always first after docstring)
3. Standard library imports (stdlib: `os`, `io`, `time`, `json`, `asyncio`, etc.)
4. Third-party imports (if any)
5. Local imports (from `flowsurgeon.*`)

Example from `src/flowsurgeon/middleware/wsgi.py`:
```python
"""WSGI middleware implementation."""

from __future__ import annotations

import cProfile
import os
import time
from typing import Callable, Iterable

import logging

from flowsurgeon._http import (...)
from flowsurgeon.core.config import Config
from flowsurgeon.core.records import RequestRecord
```

**Path Aliases:**
- No path aliases configured; all imports use absolute module paths from `flowsurgeon.*`

## Error Handling

**Patterns:**
- Try-finally blocks used extensively for cleanup: See `_InstrumentedCursor._run()` in `src/flowsurgeon/trackers/dbapi.py` lines 99-120
- Exception logging with `_log.exception()` for critical failures: `src/flowsurgeon/profiling.py` line 95
- Silent exception handling in edge cases with generic `except Exception:` for robustness: `src/flowsurgeon/middleware/wsgi.py` lines 131-139
- Graceful degradation: Returns empty lists or None rather than raising

Example from `src/flowsurgeon/profiling.py`:
```python
try:
    ps = pstats.Stats(prof, stream=stream)
except Exception:
    _log.exception("FlowSurgeon: failed to parse cProfile stats")
    return []
```

Example from `src/flowsurgeon/trackers/dbapi.py` (try-finally):
```python
def _run(self, sql: str, parameters: Any, *, many: bool) -> Any:
    queries = get_current_queries()
    t0 = time.perf_counter()
    try:
        cursor = object.__getattribute__(self, "_cursor")
        if parameters is None:
            return cursor.executemany(sql) if many else cursor.execute(sql)
        ...
    finally:
        duration_ms = (time.perf_counter() - t0) * 1000
        if queries is not None:
            ...
```

## Logging

**Framework:** Python's built-in `logging` module

**Patterns:**
- Module-level logger created with `_log = logging.getLogger(__name__)` at module top
- Used sparingly, only for exceptions or critical events
- Example from `src/flowsurgeon/middleware/wsgi.py` line 20:
  ```python
  import logging
  _log = logging.getLogger(__name__)
  ```
- Log calls use `_log.exception()` for exception context: `src/flowsurgeon/profiling.py` line 95

## Comments

**When to Comment:**
- Code is heavily self-documenting; minimal inline comments
- Comments used for explaining non-obvious design decisions or workarounds
- Comments precede code sections: `# --- Binary response: stream through without buffering ---`
- Section headers use dashes for visual clarity: `# ------------------------------------------------------------------`

**Docstrings:**
- Classes have docstrings explaining purpose and parameters
- Public functions and methods have docstrings with Parameters/Returns sections
- Docstrings use Google-style format with Parameters/Returns/Example sections
- Example from `src/flowsurgeon/trackers/dbapi.py`:
  ```python
  """Query tracker for DB-API 2.0 connections.

  Because many DB-API connection types...

  Parameters
  ----------
  connection:
      A DB-API 2.0 connection object...
  capture_stacktrace:
      When True, attach a stack trace...

  Example
  -------
  ::

      import sqlite3
      from flowsurgeon import FlowSurgeon, Config
      ...
  """
  ```

## Function Design

**Size:** Functions are generally compact, 10-50 lines typical. Middleware functions can be longer (100-150 lines) due to state management requirements. See `src/flowsurgeon/middleware/wsgi.py` lines 212-334 (_profile_request method).

**Parameters:**
- Explicit parameters favored over *args/**kwargs
- Type hints required for all parameters
- Keyword-only arguments used where beneficial: `def __init__(self, connection: Any, *, capture_stacktrace: bool = False)`
- Context parameters often optional with None defaults: `config: Config | None = None`

**Return Values:**
- Type hints required for return values
- Union types with None for optional returns: `RequestRecord | None`
- Consistent return types within a module
- Empty collections returned rather than None when appropriate: `def list_recent() -> list[RequestRecord]`

## Module Design

**Exports:**
- Public APIs listed in `__all__` at module/package level
- Example from `src/flowsurgeon/__init__.py`:
  ```python
  __all__ = [
      "AsyncSQLiteBackend",
      "Config",
      "DBAPITracker",
      "FlowSurgeon",
      ...
  ]
  ```

**Barrel Files:**
- `src/flowsurgeon/__init__.py` re-exports key classes and functions from submodules
- `src/flowsurgeon/core/__init__.py` - empty or minimal
- Selective re-exports improve public API clarity

**Private Modules:**
- `_http.py` contains HTTP utilities not meant for public use
- Double-underscore names avoided; single underscore used for internal modules and classes

**Base Classes and Abstractions:**
- `StorageBackend` in `src/flowsurgeon/storage/base.py` defines interface via ABC
- Tracker base class in `src/flowsurgeon/trackers/base.py` defines query tracker contract
- All storage backends inherit from `StorageBackend`

## Dataclasses

- Extensively used for data structures: `Config`, `QueryRecord`, `ProfileStat`, `RequestRecord`
- Location: `src/flowsurgeon/core/records.py`, `src/flowsurgeon/core/config.py`
- Use default factories for mutable defaults: `field(default_factory=dict)`, `field(default_factory=lambda: [...])`
- Frozen dataclasses not used; objects are mutable when needed

---

*Convention analysis: 2026-03-14*
