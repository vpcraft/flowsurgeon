---
phase: 02-routes-pages
plan: "01"
subsystem: ui
tags: [routes, home-page, swagger-style, alpine-js, jinja2, tdd]
dependency_graph:
  requires: []
  provides: [render_routes_page, grouped-routes-ui, method-filter-pills]
  affects: [asgi-middleware, wsgi-middleware, home-template]
tech_stack:
  added: []
  patterns: [TDD-red-green, Jinja2-filters, Alpine.js-x-data, grouped-route-display]
key_files:
  created: []
  modified:
    - src/flowsurgeon/ui/panel.py
    - src/flowsurgeon/ui/templates/home.html
    - src/flowsurgeon/ui/templates/base.html
    - src/flowsurgeon/middleware/asgi.py
    - src/flowsurgeon/middleware/wsgi.py
    - tests/test_asgi.py
decisions:
  - "render_routes_page() replaces render_history_page() for the home page; render_history_page() kept with deprecation notice for backward compat"
  - "WSGI middleware updated in same plan (auto-fix) to avoid template regression"
  - "method filter implemented via Alpine.js x-show on individual route rows per plan pitfall note"
metrics:
  duration: 4min
  completed: "2026-03-15"
  tasks_completed: 2
  files_changed: 6
---

# Phase 2 Plan 1: Swagger-Style Routes Home Page Summary

Grouped Swagger-style routes home page with Alpine.js method filter pills, replacing the old flat all-requests list at `/flowsurgeon`.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Add render_routes_page(), _group_by_prefix(), _relative_time filter to panel.py (TDD RED + GREEN) | 2755903 |
| 2 | Rewrite home.html as Swagger-style grouped routes list; add CSS to base.html | ffc5c0f |

## What Was Built

**panel.py additions:**
- `_group_by_prefix(summaries)` — groups route dicts by first path segment; paths like `/` become `"root"`
- `_relative_time(ts_str)` — Jinja2 filter converting timestamps to `"Xs/Xm/Xh/Xd ago"` or `—`
- `render_routes_page()` — new home page renderer calling `_build_endpoint_summaries()` + `_group_by_prefix()`, renders `home.html` with `groups`, `debug_route`, `method_filter`, `sort`, `total_routes`
- `render_history_page()` marked deprecated via docstring

**home.html (complete rewrite):**
- Topbar with FlowSurgeon logo (no breadcrumb — this IS the root)
- Alpine.js `x-data="{ methodFilter: 'ALL' }"` wrapping entire page
- Method filter pills: ALL, GET, POST, PUT, DELETE, PATCH — client-side `x-show` on individual route rows
- Route groups with `.route-group-hd` section headers by path prefix
- Route rows: method badge (`.m-GET` etc.) + monospace path (left), stats (right)
- No-traffic rows: `.tr-no-traffic` + `.method-muted` + "No requests" text
- Route row `href` links to `?method=X&path=Y` for Plan 02 drill-down
- Empty state: "No routes discovered." when `total_routes == 0`

**base.html CSS additions:**
- `.filter-pills`, `.pill`, `.pill-active` — method filter pill bar
- `.route-group-hd` — uppercase section dividers
- `.tr-no-traffic`, `.method-muted` — muted styling for zero-traffic routes
- `.td-stats` — flex container for right-aligned stats

**ASGI + WSGI middleware:**
- Both `_serve_history()` methods updated to call `render_routes_page()` with `app_routes`, `method_filter`, `sort`
- `render_history_page` import removed from both; `render_routes_page` imported instead

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] WSGI middleware also called render_history_page()**
- **Found during:** Task 2 full test suite run
- **Issue:** `tests/test_wsgi.py::TestDebugRoutes::test_history_route_returns_html` failed because `wsgi.py` still imported and called the old `render_history_page()` which passed the old template context (no `groups` variable), causing a Jinja2 UndefinedError
- **Fix:** Updated `wsgi.py` `_serve_history()` to call `render_routes_page()` with same pattern as asgi.py; removed `render_history_page` and `_parse_qs_int` imports
- **Files modified:** `src/flowsurgeon/middleware/wsgi.py`
- **Commit:** ffc5c0f (included in Task 2 commit)

## Test Results

- 4 new tests added to `TestRoutesHomePage` class in `tests/test_asgi.py`
- All 76 tests pass (72 pre-existing + 4 new)
- No regressions

## Self-Check: PASSED

- panel.py: FOUND
- home.html: FOUND
- base.html: FOUND
- test_asgi.py: FOUND
- Commit 2755903: FOUND
- Commit ffc5c0f: FOUND
