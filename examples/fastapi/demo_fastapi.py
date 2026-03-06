"""FlowSurgeon v0.2.0 — demo with FastAPI (ASGI).

Run:
    uv run --group examples uvicorn examples.fastapi.demo_fastapi:app

Then open http://127.0.0.1:8000 in your browser.

Routes to try:
    /                  HTML page — panel injects here
    /about             another HTML page
    /api/items         JSON response — panel must NOT appear
    /slow              waits 300ms — panel shows timing
    /boom              raises 500 — panel shows red badge
    /__flowsurgeon__/              request history
    /__flowsurgeon__/<id>          single request detail
"""

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from flowsurgeon import Config, FlowSurgeon

_inner = FastAPI()

# Wrap the FastAPI ASGI app with FlowSurgeon.
# FlowSurgeon() auto-detects ASGI and returns FlowSurgeonASGI.
app = FlowSurgeon(
    _inner,
    config=Config(
        enabled=True,
        db_path="demo_fastapi.db",
        allowed_hosts=["127.0.0.1", "::1", "localhost"],
    ),
)

# ---------------------------------------------------------------------------
# Shared HTML template
# ---------------------------------------------------------------------------

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; max-width: 680px; margin: 60px auto; color: #333; }}
    nav a {{ margin-right: 16px; color: #0066cc; text-decoration: none; }}
    nav a:hover {{ text-decoration: underline; }}
    h1 {{ color: #1a1a2e; }}
  </style>
</head>
<body>
  <nav>
    <a href="/">Home</a>
    <a href="/about">About</a>
    <a href="/api/items">JSON API</a>
    <a href="/slow">Slow (300ms)</a>
    <a href="/boom">Boom (500)</a>
  </nav>
  <h1>{title}</h1>
  <p>{body}</p>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@_inner.get("/", response_class=HTMLResponse)
async def index():
    return _PAGE.format(
        title="FlowSurgeon Demo (FastAPI)",
        body="This is the home page. The debug panel should appear in the bottom-right corner.",
    )


@_inner.get("/about", response_class=HTMLResponse)
async def about():
    return _PAGE.format(
        title="About",
        body="FlowSurgeon is a framework-agnostic profiling middleware for Python.",
    )


@_inner.get("/api/items", response_class=JSONResponse)
async def api_items():
    # JSON response — FlowSurgeon must NOT inject the panel here.
    return {"items": ["apple", "banana", "cherry"], "count": 3}


@_inner.get("/slow", response_class=HTMLResponse)
async def slow():
    await asyncio.sleep(0.3)
    return _PAGE.format(
        title="Slow endpoint",
        body="This route sleeps 300ms. The panel should show ~300ms duration.",
    )


@_inner.get("/boom")
async def boom():
    raise HTTPException(status_code=500, detail="Intentional server error")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print("FlowSurgeon FastAPI demo running at http://127.0.0.1:8000")
    print("Debug history:  http://127.0.0.1:8000/__flowsurgeon__/")
    uvicorn.run(app, host="127.0.0.1", port=8000)
