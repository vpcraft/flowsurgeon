"""FlowSurgeon v0.1.0 — manual demo with Flask.

Run:
    uv run examples/demo_flask.py

Then open http://127.0.0.1:5000 in your browser.

Routes to try:
    /                  HTML page — panel injects here
    /about             another HTML page
    /api/items         JSON response — panel must NOT appear
    /slow              waits 300ms — panel shows timing
    /boom              raises 500 — panel shows red badge
    /__flowsurgeon__/              request history
    /__flowsurgeon__/<id>          single request detail
"""

import time

from flask import Flask, abort, jsonify

from flowsurgeon import Config, FlowSurgeonWSGI

app = Flask(__name__)

# ------------------------------------------------------------------
# Wrap Flask's internal WSGI callable with FlowSurgeon.
# Note: wrap app.wsgi_app, not app itself, so Flask's own error
# handling and request context still work correctly.
# ------------------------------------------------------------------
app.wsgi_app = FlowSurgeonWSGI(
    app.wsgi_app,
    config=Config(
        enabled=True,
        db_path="demo.db",
        allowed_hosts=["127.0.0.1", "::1", "localhost"],
    ),
)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

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


@app.get("/")
def index():
    return _PAGE.format(
        title="FlowSurgeon Demo",
        body="This is the home page. The debug panel should appear in the bottom-right corner.",
    )


@app.get("/about")
def about():
    return _PAGE.format(
        title="About",
        body="FlowSurgeon is a framework-agnostic profiling middleware for Python.",
    )


@app.get("/api/items")
def api_items():
    # JSON response — FlowSurgeon must NOT inject the panel here.
    return jsonify({"items": ["apple", "banana", "cherry"], "count": 3})


@app.get("/slow")
def slow():
    time.sleep(0.3)
    return _PAGE.format(
        title="Slow endpoint",
        body="This route sleeps 300ms. The panel should show ~300ms duration.",
    )


@app.get("/boom")
def boom():
    abort(500)


# ------------------------------------------------------------------

if __name__ == "__main__":
    print("FlowSurgeon demo running at http://127.0.0.1:5000")
    print("Debug history:  http://127.0.0.1:5000/__flowsurgeon__/")
    app.run(host="127.0.0.1", port=5000, debug=False)
