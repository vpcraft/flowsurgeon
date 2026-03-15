# Phase 2: Routes Pages - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a Swagger-like routes list as the home page at `/flowsurgeon` and a per-route request history page. The existing all-requests grid is removed — route drill-down is the only way to view individual requests. All 4 request detail tabs (Details, SQL, Traceback, Profile) must be visually consistent with the Phase 1 design system.

</domain>

<decisions>
## Implementation Decisions

### Home page layout
- Swagger-style grouped layout with routes grouped by path prefix (first path segment)
- All groups start expanded by default
- No-traffic routes shown with muted text + no stats — method badge stays colored but at reduced opacity, stats columns show a dash or "No requests"
- Method filter pills at top: ALL | GET | POST | PUT | DELETE | PATCH — clicking filters the route list
- The existing all-requests list view is completely removed — routes list is the sole home view

### Route row metadata
- Each route row shows: method badge + path (left), right-aligned stats bar
- Stats shown: request count, latest duration, latest query count, latest status (with status coloring), last seen time (relative, e.g., "2m ago")
- Right-aligned compact stats layout: `[GET] /api/users    12 reqs  15ms  2q  200  2m ago`

### Route-to-detail navigation
- Clicking a route row navigates to a separate filtered page showing only requests for that endpoint
- URL structure: Claude's discretion (query params or nested path — whichever is cleanest with existing middleware routing)
- Route detail page shows the same request list layout with filtering/sorting controls (status, duration, date per RDET-02)
- Clicking a request row on the route detail page navigates to the existing detail.html with 4 tabs

### Breadcrumb navigation
- Fully clickable breadcrumb trail throughout:
  - Home: `FlowSurgeon`
  - Route view: `FlowSurgeon > [GET] /api/users`
  - Request detail: `FlowSurgeon > [GET] /api/users > Request #abc123`
- Each breadcrumb segment links back to its page (RDET-03)

### Detail page polish
- All 4 request detail tabs (Details, SQL, Traceback, Profile) inherit the Phase 1 CSS design system
- Visually consistent with new token-based styling (DPOL-01, DPOL-02)

### Claude's Discretion
- URL scheme for route detail page (query params vs nested path)
- Path prefix grouping algorithm (how to determine group boundaries)
- Exact relative time formatting implementation
- Route detail page filter/sort control design
- Empty state when no routes are discovered

</decisions>

<specifics>
## Specific Ideas

- Swagger UI is the primary visual reference for the grouped routes layout
- Stats bar on route rows should be compact and scannable — think admin dashboard density
- The current `_build_endpoint_summaries()` function already provides all needed data (method, path, count, duration, query count, status, timestamp)
- Phase 1 decision: list view is default (Swagger UI pattern), no card view on home

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_build_endpoint_summaries()` in `ui/panel.py`: Already merges discovered routes with request history, supports method_filter and sort params
- `discover_routes()` in `ui/panel.py`: Auto-discovers routes from Flask/FastAPI apps as (METHOD, path) tuples
- `render_history_page()` in `ui/panel.py`: Current home page renderer — needs to be refactored for routes-first view
- `render_detail_page()` in `ui/panel.py`: Request detail renderer with 4 tabs — reuse as-is
- `home.html`: Current template with requests list — needs replacement with routes layout
- `detail.html`: Request detail template — add breadcrumb, ensure design system consistency

### Established Patterns
- Server-rendered HTML via Jinja2, Alpine.js for client-side interactivity (tab switching, expand/collapse)
- CSS custom properties from Phase 1 design system (`:root {}` tokens)
- Method badge tokens: `--color-method-*-bg` with Swagger solid colors
- Bordered-row admin pattern (no box shadows)
- Muted label / bright value typographic hierarchy

### Integration Points
- `_serve_history()` in both `asgi.py` and `wsgi.py` — needs route view logic added
- `_app_routes` stored in middleware `__init__` — already available for route list
- `home.html` extends `base.html` — CSS changes propagate automatically
- New route detail page may need a new template or reuse of `home.html` with different context

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-routes-pages*
*Context gathered: 2026-03-15*
