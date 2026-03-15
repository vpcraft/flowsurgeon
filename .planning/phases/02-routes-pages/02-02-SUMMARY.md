---
phase: 02-routes-pages
plan: 02
subsystem: ui
tags: [jinja2, asgi, wsgi, middleware, html-templates]

# Dependency graph
requires:
  - phase: 02-routes-pages/02-01
    provides: render_routes_page(), home.html, _filter_records(), _paginate() helpers

provides:
  - render_route_detail_page() in panel.py — filtered request list for a specific route
  - route_detail.html — route detail template with 2-level breadcrumb, filter/sort controls, request table, pagination
  - ASGI/WSGI middleware dispatch branching on method+path query params
  - 3-level clickable breadcrumb in detail.html (FlowSurgeon > METHOD /path > request_id)
  - Profile tab re-added to detail.html subnav and content area

affects:
  - phase: 03-security-docs
  - phase: 04-release

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Route detail via query params (?method=GET&path=/api/users) instead of nested paths (avoids 404 collision with request_id routing)
    - Middleware double-dispatch: method+path present → route detail; otherwise → routes home
    - Jinja2 urlencode filter for URL-safe path encoding in templates

key-files:
  created:
    - src/flowsurgeon/ui/templates/route_detail.html
  modified:
    - src/flowsurgeon/ui/panel.py
    - src/flowsurgeon/middleware/asgi.py
    - src/flowsurgeon/middleware/wsgi.py
    - src/flowsurgeon/ui/templates/detail.html
    - tests/test_asgi.py
    - tests/test_wsgi.py

key-decisions:
  - "Route detail uses query params (?method=GET&path=/api/users) not nested paths to avoid collision with request_id routing in asgi.py/wsgi.py"
  - "method+path both required for route detail dispatch; method-only still routes to home with method filter"
  - "Profile tab re-added to detail.html subnav — detail_profile.html partial was already cleaned up in Phase 1"

patterns-established:
  - "Panel function pattern: render_route_detail_page() reuses _filter_records() and _paginate() from panel.py"
  - "Breadcrumb pattern: b-dim (muted link) > sep > b-mid (route link) > sep > b-cur (current, brand color)"

requirements-completed: [RDET-01, RDET-02, RDET-03, DPOL-01, DPOL-02]

# Metrics
duration: 3min
completed: 2026-03-15
---

# Phase 2 Plan 02: Route Detail Page, Middleware Dispatch, and Detail Page Polish Summary

**Route detail page with filtered request list, ASGI/WSGI dispatch branching on method+path params, 3-level breadcrumb on detail page, and Profile tab restored — all 86 tests green.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-15T18:15:04Z
- **Completed:** 2026-03-15T18:18:22Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- `render_route_detail_page()` added to panel.py: filters records by method+path, supports status/sort/pagination controls
- New `route_detail.html` template: 2-level breadcrumb, GET form with status/sort/show selects, request table, pagination
- ASGI and WSGI `_serve_history()` branches on method+path params to call route detail vs. routes home view
- `detail.html` updated with 3-level clickable breadcrumb (FlowSurgeon → METHOD /path → request_id[:8])
- Profile tab re-added to detail.html subnav and content area (was removed in Phase 1)
- 10 new integration tests (6 ASGI, 4 WSGI) covering RDET-01/02/03 and DPOL-01/02

## Task Commits

1. **Task 1: render_route_detail_page() + route_detail.html** - `0b724c0` (feat)
2. **Task 2: middleware dispatch + detail.html breadcrumb/profile** - `3a7af38` (feat)
3. **Task 3: integration tests** - `ef8bd70` (test)

## Files Created/Modified

- `src/flowsurgeon/ui/panel.py` - Added `render_route_detail_page()` function
- `src/flowsurgeon/ui/templates/route_detail.html` - New template: filtered request list per route
- `src/flowsurgeon/middleware/asgi.py` - Import _parse_qs_int + render_route_detail_page; branched _serve_history
- `src/flowsurgeon/middleware/wsgi.py` - Same changes as asgi.py (synchronous)
- `src/flowsurgeon/ui/templates/detail.html` - 3-level breadcrumb, Profile tab added
- `tests/test_asgi.py` - TestRouteDetail class (6 tests)
- `tests/test_wsgi.py` - TestRouteDetail class (4 tests)

## Decisions Made

- Route detail uses query params (`?method=GET&path=/api/users`) not nested URL paths, to avoid collision with request_id routing in `_serve_history` → `_serve_detail` dispatch logic.
- When `method` is present without `path`, middleware falls through to routes home view with method filter (backward compatible with existing pill filter UI).
- Profile tab re-added without changes — the `detail_profile.html` partial was already cleaned up in Phase 1 and just needed to be included.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Route detail navigation is fully wired: home page → route detail → request detail (3-level breadcrumb)
- All 4 tabs visible on detail page: Details, SQL, Traceback, Profile
- Phase 3 (Security Docs) can proceed independently
- Phase 4 (Release) depends on both Phase 2 and Phase 3 completing

## Self-Check: PASSED

- FOUND: src/flowsurgeon/ui/templates/route_detail.html
- FOUND: src/flowsurgeon/ui/panel.py (with render_route_detail_page)
- FOUND: .planning/phases/02-routes-pages/02-02-SUMMARY.md
- FOUND: 0b724c0 (feat: route_detail.html + panel function)
- FOUND: 3a7af38 (feat: middleware dispatch + detail.html polish)
- FOUND: ef8bd70 (test: integration tests)
- Full test suite: 86 passed

---
*Phase: 02-routes-pages*
*Completed: 2026-03-15*
