# Hacker News Submission Draft

**Title:** Show HN: FlowSurgeon — Debug toolbar for Flask and FastAPI (Python)

**URL:** https://github.com/vpcraft/flowsurgeon

---

**Body (plain text — HN does not render markdown):**

FlowSurgeon is a WSGI/ASGI middleware that gives Flask and FastAPI apps a built-in debug toolbar at /flowsurgeon. It tracks every HTTP request with timing, headers, SQL queries (slow/duplicate detection), and optional cProfile call-stack profiling.

Unlike django-debug-toolbar, it works with any Python web framework via a single-line wrap — no framework-specific plugins required. The only runtime dependency is Jinja2.

GitHub: https://github.com/vpcraft/flowsurgeon
PyPI: https://pypi.org/project/flowsurgeon/
