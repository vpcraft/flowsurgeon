# FlowSurgeon

## What This Is

FlowSurgeon is a framework-agnostic profiling middleware for Python — a drop-in debug UI for Flask and FastAPI. It wraps any WSGI or ASGI app with a single line, injecting a collapsible debug panel into HTML responses and storing full request history (timing, headers, SQL queries, response bodies, cProfile data) in a local SQLite database, with a built-in dark-themed UI at `/flowsurgeon`.

The project is currently at v0.5.0 with working middleware, SQL tracking (SQLAlchemy + DB-API 2.0), cProfile profiling, and a request history browser. It's an open-source tool targeting Python developers who want django-debug-toolbar-like introspection without being tied to Django.

## Core Value

Developers can instantly see what their Python web app is doing — every request, every SQL query, every hotspot — without modifying application code or installing framework-specific tools.

## Requirements

### Validated

- WSGI middleware with request capture and panel injection — v0.1.0
- ASGI middleware with feature parity — v0.2.0
- Auto-detect WSGI vs ASGI via `FlowSurgeon()` factory — v0.2.0
- SQLAlchemy query tracking via engine events — v0.3.0
- DB-API 2.0 query tracking via transparent proxy — v0.3.0
- Duplicate and slow query detection with badges — v0.3.0
- cProfile-based per-request profiling with stats table — v0.4.0
- Callers drilldown per profiled function — v0.4.0
- Request history browser at `/flowsurgeon` — v0.5.0
- Request detail view with 4 tabs (Details, SQL, Traceback, Profile) — v0.5.0
- Card grid view with filtering and sorting — v0.5.0
- SQLite persistence with auto-pruning — v0.1.0
- Sensitive header redaction — v0.1.0
- `FLOWSURGEON_ENABLED` env var kill switch — v0.1.0
- Route auto-discovery for Flask and FastAPI — v0.5.0
- Response body capture (up to 128 KB) — v0.5.0

### Active

- [ ] New home page: API routes list (Swagger/OpenAPI-inspired) with method coloring and descriptions
- [ ] Route detail page: clicking a route shows filtered/sorted requests for that endpoint
- [ ] Full UI redesign: shadcn-inspired styling (clean typography, subtle borders, proper spacing) while keeping the current dark color palette
- [ ] Documentation site (mkdocs or similar) — installation, configuration reference, panel descriptions, adapter guide
- [ ] CI/CD pipeline — GitHub Actions for tests, linting, release workflow
- [ ] Proper release packaging — badges, changelog, consistent versioning

### Out of Scope

- Plugin API / Panel base class — deferred to future version after public announcement
- Additional ORM adapters (Tortoise, Django) — deferred to future version
- React/JS build toolchain — keeping server-rendered HTML + Alpine.js + CSS
- v1.0.0 stable release — staying in 0.x for flexibility
- Mobile-responsive debug UI — developers use this on desktop

## Context

- The project follows the plan in `docs/plan.md` but v0.6.0 scope is shifting from plugin API to UI redesign + docs + CI
- Current UI uses server-rendered HTML via Jinja2, Alpine.js for SPA-like behavior, custom CSS with a dark theme
- The goal is a public announcement on Reddit/X — the UI needs to look impressive in screenshots
- Swagger/OpenAPI is the visual reference for the new API routes list page
- Method coloring: GET=blue, POST=green, PUT=orange, DELETE=red (standard Swagger convention)
- The existing dark color palette should be preserved — users have confirmed it looks good
- Python 3.12+ only, single runtime dependency (jinja2)

## Constraints

- **No build step**: UI must remain server-rendered HTML + Alpine.js + CSS. No React, no Webpack, no npm.
- **Zero heavy dependencies**: Only jinja2 at runtime. SQLAlchemy/DB-API adapters are optional.
- **Self-contained**: All assets (CSS, JS) bundled inline or as static files within the package.
- **Design-first**: UI changes must be designed in `ui.pen` and approved before implementation.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Server-rendered HTML over React | No build step, self-contained middleware, simpler distribution | — Pending |
| shadcn-inspired CSS over actual shadcn | Can't use React components in server-rendered context; CSS polish achieves the visual goal | — Pending |
| API routes list as home page | Makes FlowSurgeon feel like a professional API tool (Swagger-like), not just a debug panel | — Pending |
| Stay in 0.x after public launch | Flexibility to change scope/API; follows FastAPI's versioning approach | — Pending |

---
*Last updated: 2026-03-15 after initialization*
