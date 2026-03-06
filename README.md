# FlowSurgeon

Framework-agnostic profiling middleware for Python — works with **Flask** (WSGI) and **FastAPI / Starlette** (ASGI) out of the box.

FlowSurgeon injects a lightweight debug panel into every HTML response and stores request history in a local SQLite database, giving you timing, headers, and status codes without touching your application code.

## Features

- Zero required dependencies — pure stdlib
- WSGI middleware (`FlowSurgeonWSGI`) for Flask, Django, and any WSGI app
- ASGI middleware (`FlowSurgeonASGI`) for FastAPI, Starlette, and any ASGI app
- `FlowSurgeon()` factory — auto-detects WSGI vs ASGI
- Inline debug panel injected into HTML responses
- Built-in history UI at `/__flowsurgeon__/`
- SQLite persistence with auto-pruning
- Sensitive header redaction (`Authorization`, `Cookie`)
- `FLOWSURGEON_ENABLED` environment variable kill switch

## Installation

```bash
pip install flowsurgeon
```

## Quick start

### FastAPI (ASGI)

```python
from fastapi import FastAPI
from flowsurgeon import FlowSurgeon, Config

_app = FastAPI()
app = FlowSurgeon(_app, config=Config(enabled=True))

@_app.get("/")
async def index():
    return {"hello": "world"}
```

Run with uvicorn:

```bash
uvicorn myapp:app
```

### Flask (WSGI)

```python
from flask import Flask
from flowsurgeon import FlowSurgeon, Config

flask_app = Flask(__name__)
flask_app.wsgi_app = FlowSurgeon(
    flask_app.wsgi_app,
    config=Config(enabled=True),
)
```

## Configuration

```python
from flowsurgeon import Config

Config(
    enabled=True,                          # default: False (or FLOWSURGEON_ENABLED=1)
    allowed_hosts=["127.0.0.1", "::1"],    # hosts that see the panel
    db_path="flowsurgeon.db",              # SQLite file path
    max_stored_requests=1000,              # auto-prune threshold
    debug_route="/__flowsurgeon__",        # history UI prefix
    strip_sensitive_headers=["authorization", "cookie", "set-cookie"],
)
```

## Debug UI

| Route | Description |
|---|---|
| `/__flowsurgeon__/` | Paginated request history |
| `/__flowsurgeon__/{id}` | Full detail for one request |

## Roadmap

- v0.3.0 — SQL query tracking (SQLAlchemy, DB-API 2.0)
- v0.4.0 — CPU and memory profiling panel
- v0.5.0 — Log capture and headers panel
- v0.6.0 — Improved history/search UI

## License

MIT
