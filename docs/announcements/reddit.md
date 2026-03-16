# Reddit Announcement Draft

**Suggested subreddits:** r/Python, r/flask, r/FastAPI

---

**Title:** Show r/Python: FlowSurgeon — django-debug-toolbar for Flask & FastAPI

---

**Post body:**

Hey r/Python,

If you have ever used `django-debug-toolbar` you know how useful it is to see every SQL query your app fired, along with timing, stack traces, and duplicate detection — right there in the browser. But if you are on FastAPI or Flask, there is no equivalent that just works without framework-specific plugins and configuration overhead.

I built **FlowSurgeon** to fill that gap. It wraps any WSGI or ASGI app with a single line, no application code changes required.

**What it does:**

- Captures every HTTP request: timing, headers, response body, SQL queries
- Shows a dark-themed debug UI at `/flowsurgeon` — routes overview, per-request detail, SQL tab with `slow` and `dup` badges
- Auto-discovers routes from Flask's `url_map` or FastAPI's `app.routes`
- Tracks SQL via SQLAlchemy events or a DB-API 2.0 proxy (sqlite3, psycopg2, and others)
- Integrates `cProfile` for call-stack profiling per request (opt-in)
- Disabled by default, enabled via `FLOWSURGEON_ENABLED=1` — safe to ship in your codebase
- No build step, no React, no npm — just Python and Jinja2

**Quick start (FastAPI):**

```python
from fastapi import FastAPI
from flowsurgeon import FlowSurgeon, Config

_app = FastAPI()
app = FlowSurgeon(_app, config=Config(enabled=True))
```

```bash
pip install flowsurgeon
uvicorn myapp:app --reload
# Debug UI → http://127.0.0.1:8000/flowsurgeon
```

**Flask is just as simple:**

```python
app.wsgi_app = FlowSurgeon(app.wsgi_app, config=Config(enabled=True))
```

Here is what the routes home page looks like:

![FlowSurgeon routes home](https://raw.githubusercontent.com/vpcraft/flowsurgeon/master/src/flowsurgeon/ui/assets/routes-home.png)

And the SQL tab with slow/duplicate detection:

![SQL tab with slow and dup badges](https://raw.githubusercontent.com/vpcraft/flowsurgeon/master/src/flowsurgeon/ui/assets/request-detail-sql.png)

**Links:**

- GitHub: https://github.com/vpcraft/flowsurgeon
- PyPI: https://pypi.org/project/flowsurgeon/

It is MIT licensed and open source. The examples directory has fully working FastAPI and Flask demo apps if you want to see the SQL tracking in action before integrating with your own project.

Happy to answer questions or take feedback — especially on ASGI edge cases.
