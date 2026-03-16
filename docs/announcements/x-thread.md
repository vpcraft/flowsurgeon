# X / Twitter Thread Draft

---

**Tweet 1 (hook):**

django-debug-toolbar for Flask and FastAPI.

FlowSurgeon wraps any Python WSGI/ASGI app with one line — instant debug UI with SQL query tracking, route overview, and cProfile integration.

No framework plugins. No build step. Zero app changes.

![routes home](https://raw.githubusercontent.com/vpcraft/flowsurgeon/master/src/flowsurgeon/ui/assets/routes-home.png)

---

**Tweet 2 (install + code):**

```
pip install flowsurgeon
```

FastAPI:
```python
app = FlowSurgeon(_app, config=Config(enabled=True))
```

Flask:
```python
app.wsgi_app = FlowSurgeon(app.wsgi_app, config=Config(enabled=True))
```

Debug UI at /flowsurgeon. That is the whole setup.

---

**Tweet 3 (key features):**

What you get in the SQL tab:

- Every query with timing
- `slow` badge when query exceeds your threshold
- `dup` badge when the same SQL runs more than once
- Bound params shown inline
- Optional stack trace per query

Exactly what you need to find N+1 queries before they hit prod.

---

**Tweet 4 (GIF + link):**

Here is the full walkthrough — routes home, click into a request, SQL tab with slow and dup detection:

![demo](https://raw.githubusercontent.com/vpcraft/flowsurgeon/master/src/flowsurgeon/ui/assets/demo.gif)

MIT licensed, open source.
GitHub: https://github.com/vpcraft/flowsurgeon
PyPI: https://pypi.org/project/flowsurgeon/
