<div align="center">
  <img src="https://dev-to-uploads.s3.amazonaws.com/uploads/articles/4ulii4nulch2u8qopdec.png" alt="FlowSurgeon" width="96">
  <h1>FlowSurgeon</h1>
  <p>Framework-agnostic profiling middleware for Python — drop-in debug UI for Flask and FastAPI.</p>

  [![PyPI version](https://img.shields.io/pypi/v/flowsurgeon.svg)](https://pypi.org/project/flowsurgeon/)
  [![Python 3.12+](https://img.shields.io/pypi/pyversions/flowsurgeon.svg)](https://pypi.org/project/flowsurgeon/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Tests](https://img.shields.io/github/actions/workflow/status/vpcraft/flowsurgeon/ci.yaml?label=tests)](https://github.com/vpcraft/flowsurgeon/actions)
  [![PyPI downloads](https://img.shields.io/pypi/dm/flowsurgeon.svg)](https://pypi.org/project/flowsurgeon/)
</div>

---

FlowSurgeon wraps your existing WSGI or ASGI app with a single line. It injects a collapsible debug panel into every HTML response and stores a full request history — timing, headers, SQL queries, response bodies — in a local SQLite database, with a built-in dark-themed UI at `/flowsurgeon`.

<div align="center">
    <img src="https://dev-to-uploads.s3.amazonaws.com/uploads/articles/ztt5hfvreqd7xff0jymz.png" alt="Home Screen">
</div>

## Features

- **Zero application changes** — wraps any WSGI or ASGI callable
- **Auto-detect** WSGI vs ASGI via the `FlowSurgeon()` factory
- **Inline debug panel** injected before `</body>` in every HTML response
- **Built-in history UI** at `/flowsurgeon` — no extra server needed
- **Request grid view** — browse captured requests sorted by query count, duration, or path
- **SQL query tracking** via SQLAlchemy and DB-API 2.0 (sqlite3, psycopg2, …)
- **Profiling tab** — call-stack profiling per endpoint *(coming soon)*
- **Route auto-discovery** from Flask (`url_map`) and FastAPI/Starlette (`app.routes`)
- **Response body capture** — stores up to 128 KB for text/JSON/XML responses
- **SQLite persistence** with auto-pruning (configurable max records)
- **Sensitive header redaction** — `Authorization`, `Cookie`, `Set-Cookie` stripped by default
- **`FLOWSURGEON_ENABLED` env var** — safe to ship in codebase; disabled by default

## Installation

```bash
# Recommended
uv add flowsurgeon

# pip
pip install flowsurgeon
```

Requires Python 3.12+. The only runtime dependency is `jinja2`.

## Quick start

### FastAPI / Starlette (ASGI)

```python
from fastapi import FastAPI
from flowsurgeon import FlowSurgeon, Config

_app = FastAPI()

app = FlowSurgeon(
    _app,
    config=Config(enabled=True),
)

@_app.get("/books")
async def books():
    return {"books": ["Clean Code", "Refactoring"]}
```

```bash
uvicorn myapp:app --reload
# Debug UI → http://127.0.0.1:8000/flowsurgeon
```

### Flask (WSGI)

```python
from flask import Flask
from flowsurgeon import FlowSurgeon, Config

app = Flask(__name__)

app.wsgi_app = FlowSurgeon(
    app.wsgi_app,
    config=Config(enabled=True),
)
```

```bash
flask run
# Debug UI → http://127.0.0.1:5000/flowsurgeon
```

## SQL query tracking

### SQLAlchemy

```python
from sqlalchemy import create_engine
from flowsurgeon import FlowSurgeon, Config
from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

engine = create_engine("sqlite:///mydb.db")
tracker = SQLAlchemyTracker(engine, capture_stacktrace=False)

app = FlowSurgeon(
    asgi_app,
    config=Config(enabled=True),
    trackers=[tracker],
)
```

### DB-API 2.0 (sqlite3, psycopg2, …)

```python
import sqlite3
from flowsurgeon import FlowSurgeon, Config
from flowsurgeon.trackers import DBAPITracker

raw_conn = sqlite3.connect("mydb.db")
tracker = DBAPITracker(raw_conn)
conn = tracker.connection  # use this instead of raw_conn everywhere

app = FlowSurgeon(
    wsgi_app,
    config=Config(enabled=True),
    trackers=[tracker],
)
```

`DBAPITracker` works via a transparent proxy — replace your connection object with `tracker.connection` and every `cursor().execute()` call is automatically timed and recorded.

## Configuration

```python
from flowsurgeon import Config

Config(
    # Master switch — default False. Also controlled by FLOWSURGEON_ENABLED env var.
    enabled=True,

    # Only serve the debug panel to requests from these hosts.
    allowed_hosts=["127.0.0.1", "::1", "localhost"],

    # SQLite file for request history storage.
    db_path="flowsurgeon.db",

    # Prune oldest records when this limit is exceeded.
    max_stored_requests=1000,

    # URL prefix for the built-in debug UI.
    debug_route="/flowsurgeon",

    # Headers replaced with "[redacted]" before storage.
    strip_sensitive_headers=["authorization", "cookie", "set-cookie"],

    # SQL query tracking options.
    track_queries=True,
    slow_query_threshold_ms=100.0,
    capture_query_stacktrace=False,

    # Manually register routes shown in the UI before any traffic.
    # Flask and FastAPI routes are auto-discovered; use this for other cases.
    known_routes=[("GET", "/health"), ("POST", "/webhooks/stripe")],
)
```

## Debug UI

| URL | Description |
|---|---|
| `/flowsurgeon` | Requests grid — all captured requests with latency and query info |
| `/flowsurgeon?view=profiling` | Profiling tab *(coming soon)* |
| `/flowsurgeon?q=/books` | Filter requests by path |
| `/flowsurgeon?order=duration` | Sort by duration (also: `queries`, `path`) |
| `/flowsurgeon/{request_id}` | Request detail: headers, response body, SQL, tracebacks |

### Requests view

Displays all captured requests as a card grid, sorted by number of queries by default. Each card shows: status code, HTTP method, path, total duration, query time and count. Supports filtering by path and ordering by query count, duration, or path.

### Request detail — three tabs

- **Details** — stat cards (status, duration, SQL count, SQL time); request headers; response headers and body (up to 128 KB for text/JSON content types)
- **SQL** — every captured query with timing, `slow` badge (exceeds threshold), `dup` badge (same SQL run more than once), and bound params
- **Traceback** — Python stack trace per query (requires `capture_query_stacktrace=True`)

## Running the examples

```bash
# FastAPI + SQLAlchemy
uv run --group examples uvicorn examples.fastapi.demo_fastapi:app --reload

# Flask + DB-API (sqlite3)
uv run --group examples python examples/flask/demo_flask.py
```

Debug UI:
- FastAPI → http://127.0.0.1:8000/flowsurgeon
- Flask → http://127.0.0.1:5000/flowsurgeon

Both demos expose these routes:

| Route | What it demonstrates |
|---|---|
| `GET /books` | Normal query — 1 SQL |
| `GET /books/{id}` | Parametrised query |
| `GET /books/duplicates` | Same query twice → **dup** badge |
| `GET /books/slow` | Query exceeds threshold → **slow** badge |
| `GET /slow` | Slow endpoint, no SQL |
| `GET /boom` | 500 error |

## Environment variable

```bash
# Enable without modifying code
FLOWSURGEON_ENABLED=1 uvicorn myapp:app
```

Keep `enabled=False` (the default) so the middleware is a no-op in production, and flip it on per-environment via the env var or your settings layer.

## License

[MIT](LICENSE)
