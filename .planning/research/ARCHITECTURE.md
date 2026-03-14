# Architecture Patterns

**Domain:** Python debug middleware UI — Swagger-like routes home page + shadcn-inspired dark styling
**Researched:** 2026-03-15
**Confidence:** HIGH (based on deep codebase analysis + well-established Swagger/shadcn patterns)

---

## Existing Architecture (v0.5.0 Baseline)

```
Request (HTTP)
    |
    v
FlowSurgeonWSGI / FlowSurgeonASGI          <- middleware/__init__.py factory
    |   dispatches on path prefix
    |-- /{debug_route}/_static/*           -> _serve_static()  -> _load_asset_bytes()
    |-- /{debug_route}  (exact)            -> _serve_history() -> render_history_page()
    |-- /{debug_route}/{id}               -> _serve_detail()  -> render_detail_page()
    +-- anything else                     -> _profile_request() -> save to SQLite
                                                               -> inject render_panel() into HTML
```

### Current UI Layer Components

| File | Role |
|------|------|
| `ui/panel.py` | All rendering logic: Jinja2 env, filters, asset loader, route discovery, data aggregation |
| `ui/templates/base.html` | Full CSS (all styles inlined in `<style>`), Alpine.js `<script>` tag, topbar/subnav blocks |
| `ui/templates/home.html` | Requests card grid — tabs (Latency & Queries, Profiling), filter form, pagination |
| `ui/templates/detail.html` | Single request — 4 Alpine tabs (Details, SQL, Traceback, Profile) |
| `ui/templates/partials/` | detail_sql.html, detail_traceback.html, detail_profile.html |
| `ui/assets/panel.css` | Panel injection CSS (injected inline into app HTML responses) |
| `ui/assets/panel.js` | Currently empty |
| `ui/assets/alpine.min.js` | Alpine.js 3.x, served as static asset |

### Current Data Flow

```
SQLiteBackend.list_recent(500)
    |
    v
panel.py: _filter_records() -> sort -> paginate
    |
    v
render_history_page() -> Jinja2 template -> HTML string -> bytes -> WSGI/ASGI response
```

Routes are discovered once at middleware init via `discover_routes(app)` and stored in `self._app_routes`. They are NOT currently passed to `render_history_page()` — this is the gap the new home page must fill.

---

## Recommended Architecture for v0.6.0

### New Page: Routes Home (`/flowsurgeon`)

```
SQLiteBackend.list_recent(500)   +   self._app_routes (discovered at init)
        |                                      |
        +--------------------------------------+
                          |
                          v
          panel.py: _build_endpoint_summaries()    <- ALREADY EXISTS
                          |
                          v
          render_routes_page() or extended render_history_page()
                          |
                          v
          templates/home.html   (redesigned — routes table as primary view)
```

The `_build_endpoint_summaries()` function already merges routes + records into the right data shape. The data pipeline is complete; only the template and render function signature need to change.

### Component Boundaries

| Component | Change in v0.6.0 |
|-----------|------------------|
| `middleware/wsgi.py` `middleware/asgi.py` | Pass `app_routes` to history render call; add route detail dispatch |
| `ui/panel.py` | Add/extend render function; add route-specific Jinja filters |
| `ui/templates/base.html` | Full CSS refactor to CSS custom properties + shadcn-inspired tokens |
| `ui/templates/home.html` | Full redesign: routes-as-primary layout |
| `ui/templates/detail.html` | Inherits visual refresh via base.html; minor layout tuning |
| `ui/templates/partials/` | Minor cleanup for new CSS token names |

### New Route: Route Detail Page

```
GET /flowsurgeon/routes/{METHOD}/{encoded_path}
    |
    v
_serve_route_detail() in middleware (new handler)
    |
    v
panel.py: render_route_detail_page() OR render_history_page() with route_context pre-filter
    |
    v
templates/home.html with route_context variable
```

**Recommendation:** Reuse `home.html` with a `route_context` context variable rather than a separate template. Avoids template duplication.

### Complete Data Flow (v0.6.0)

```
GET /flowsurgeon
    |-- middleware._serve_history()
    |      |-- storage.list_recent(500)
    |      |-- self._app_routes
    |      +-- render_routes_page(records, app_routes, ...)
    |              +-- _build_endpoint_summaries() -> summary dicts
    |              +-- Jinja2: home.html -> HTML

GET /flowsurgeon/routes/GET/%2Fapi%2Fusers  (new)
    +-- middleware._serve_route_detail()
           |-- storage.list_recent(500)
           |-- _filter_records(records, path="/api/users", method="GET")
           +-- render_history_page(filtered) with route_context

GET /flowsurgeon/{uuid}
    +-- middleware._serve_detail() -> render_detail_page() (unchanged)

GET /flowsurgeon/_static/*
    +-- middleware._serve_static() -> _load_asset_bytes() (unchanged)
```

---

## CSS Architecture: shadcn-Inspired Without React

### Pattern: CSS Custom Properties Design System

Replace hardcoded hex values in `base.html` with semantic tokens:

```css
:root {
  --bg-canvas:     #0D0F12;
  --bg-surface:    #131720;
  --bg-elevated:   #0D1117;
  --bg-hover:      #161A22;

  --border-subtle: #1E2328;
  --border-focus:  #00D4AA;

  --text-primary:  #E5E7EB;
  --text-secondary:#9CA3AF;
  --text-muted:    #6B7280;

  --brand:         #00D4AA;
  --brand-hover:   #00BFA0;

  --method-get-bg:    #0D3B2E;  --method-get-fg:    #10B981;
  --method-post-bg:   #1A2A0E;  --method-post-fg:   #4ADE80;
  --method-put-bg:    #2D1B0E;  --method-put-fg:    #F59E0B;
  --method-delete-bg: #3B0D0D;  --method-delete-fg: #EF4444;
  --method-patch-bg:  #1A1A2E;  --method-patch-fg:  #818CF8;

  --radius-sm:  4px;
  --radius-md:  8px;
  --radius-lg:  12px;
}
```

### shadcn Visual Signature (Four Rules)

1. **Clean borders over shadows** — `border: 1px solid var(--border-subtle)`
2. **Muted label / bright value hierarchy** — labels in `--text-muted`, values in `--text-primary`
3. **Subtle hover states** — `background: var(--bg-hover)` with `transition: background 0.12s ease`
4. **Tight typographic scale** — 11px labels (uppercase, letter-spacing), 13px body, 14px nav, 20-28px headings

---

## Patterns to Follow

1. **Single CSS file in base.html `<style>` block** — All non-panel CSS in one block. Panel CSS stays separate for injection.
2. **Alpine.js x-data scope isolation** — One top-level `x-data` per page, server-initialized from query params.
3. **Server-side filtering, Alpine only for UI state** — All filtering via query parameters. Alpine only for tab switching. Pages are functional without JS.
4. **Separate template per page type, shared base** — `base.html` -> page templates (one level deep).

## Anti-Patterns to Avoid

1. **Inline style overrides in templates** — Current templates use `style="width:240px;"` etc. Introduce utility classes instead.
2. **Not passing app_routes to render functions** — Current gap. Three-line change per middleware file.
3. **Route detail as copy-paste template** — Use `route_context` variable in `home.html` instead.

---

## Suggested Build Order

1. **CSS Design System** (base.html only) — Extract hardcoded values to `:root {}` CSS custom properties
2. **Routes Table** (home.html + panel.py + middleware) — Routes as primary view, requests as secondary
3. **Route Detail Page** — Dispatch + filter + route_context in home.html
4. **Detail Page Polish** — Inherits CSS improvements from Step 1
5. **Panel Injection Refresh** — Update panel.css if badge style needs to match

---

*Research date: 2026-03-15*
