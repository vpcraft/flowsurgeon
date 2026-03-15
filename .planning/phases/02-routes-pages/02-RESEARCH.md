# Phase 2: Routes Pages - Research

**Researched:** 2026-03-15
**Domain:** Python server-rendered UI (Jinja2 + Alpine.js), WSGI/ASGI middleware routing
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Home page layout:** Swagger-style grouped layout with routes grouped by path prefix (first path segment)
- All groups start expanded by default
- No-traffic routes shown with muted text + no stats — method badge stays colored but at reduced opacity, stats columns show a dash or "No requests"
- Method filter pills at top: ALL | GET | POST | PUT | DELETE | PATCH — clicking filters the route list
- The existing all-requests list view is completely removed — routes list is the sole home view
- **Route row metadata:** Each route row shows method badge + path (left), right-aligned stats bar: `[GET] /api/users    12 reqs  15ms  2q  200  2m ago`
- **Route-to-detail navigation:** Clicking a route navigates to a separate filtered page showing only requests for that endpoint
- Route detail page shows the same request list layout with filtering/sorting controls (status, duration, date per RDET-02)
- Clicking a request row on the route detail page navigates to the existing detail.html with 4 tabs
- **Breadcrumb navigation:** Fully clickable 3-level breadcrumb: `FlowSurgeon > [GET] /api/users > Request #abc123`
- **Detail page polish:** All 4 request detail tabs inherit Phase 1 CSS design system

### Claude's Discretion
- URL scheme for route detail page (query params vs nested path)
- Path prefix grouping algorithm (how to determine group boundaries)
- Exact relative time formatting implementation
- Route detail page filter/sort control design
- Empty state when no routes are discovered

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RHOM-01 | Home page (`/flowsurgeon`) displays API routes list as primary view | `_build_endpoint_summaries()` already returns the needed data; `render_history_page()` must be replaced with a routes-first renderer |
| RHOM-02 | Each route shows HTTP method badge + path + description (if available) | Method badge CSS classes (`m-GET`, etc.) are already in `base.html`; description field not in current data model — show path only |
| RHOM-03 | Routes grouped or sortable by method | Alpine.js method filter pills drive client-side or server-side filtering; path-prefix grouping done in Python |
| RHOM-04 | Routes with no traffic shown in muted style | `has_data: False` already produced by `_build_endpoint_summaries()`; need CSS for muted-opacity rows |
| RHOM-05 | Existing requests grid available as secondary tab/view | CONTEXT.md overrides this: the requests grid is **removed entirely** — routes list is sole view |
| RDET-01 | Clicking a route navigates to filtered view showing only requests for that endpoint | New route detail page served at `debug_route/?method=GET&path=/api/users` or `debug_route/route?...` |
| RDET-02 | Route detail shows filtering and sorting controls (status, duration, date) | Reuse existing `_filter_records()` and `_paginate()` helpers; add status/date query params |
| RDET-03 | Route breadcrumb shows method + path context | `detail.html` already has breadcrumb structure; route detail page needs its own breadcrumb level |
| DPOL-01 | Request detail page inherits new CSS design system | `detail.html` extends `base.html` which already has Phase 1 tokens — propagation is automatic |
| DPOL-02 | All 4 tabs (Details, SQL, Traceback, Profile) visually consistent with new design | Profile tab partial exists but is missing from `detail.html` subnav — must be added |
</phase_requirements>

---

## Summary

Phase 2 is a UI restructuring phase within an existing Python server-rendered stack. No new dependencies are needed. All the data is already available: `_build_endpoint_summaries()` returns per-route stats (method, path, count, duration, query count, status, timestamp, `has_data`), and `_filter_records()` + `_paginate()` handle the route-filtered request list. The work is largely template replacement and refactoring the two render entry points.

The central architectural decision for the planner is the URL scheme for the route detail page. Query params (`/flowsurgeon?method=GET&path=/api/users`) are strongly preferred over a nested path approach because the existing routing in `asgi.py` and `wsgi.py` uses path-prefix matching: anything starting with `debug_route + "/"` is treated as a request ID, which would conflict with a nested route path like `/flowsurgeon/route/api/users`. Query params avoid this conflict with zero routing changes.

The `RHOM-05` requirement in REQUIREMENTS.md says "Existing requests grid available as secondary tab/view." The CONTEXT.md locked decision overrides this — the all-requests list is being removed entirely. The planner must note this divergence: RHOM-05 as written is satisfied by the CONTEXT decision only if we reinterpret it, but the user's locked choice removes that secondary view completely.

**Primary recommendation:** Replace `render_history_page()` with a new `render_routes_page()` function, add a `render_route_detail_page()` function, route `/flowsurgeon?method=X&path=Y` as the route detail URL, and update both `asgi.py` and `wsgi.py` `_serve_history()` to branch on whether `method` + `path` query params are present.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | >=3.1.0 (already dep) | Server-side HTML rendering | Already in use; all templates extend base.html |
| Alpine.js | already vendored as static asset | Client-side interactivity (expand/collapse groups, method filter pills) | Already in use; no build step required |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `datetime` | stdlib | Relative time calculation ("2m ago") | Use `datetime.now(timezone.utc) - record.timestamp` to produce timedelta, format in Jinja2 filter |
| Python stdlib `urllib.parse` | stdlib | Query string parsing | Already used in `_http.py`; `_parse_qs_param` already exists |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Query params for route detail URL | Nested path `/flowsurgeon/route/GET/api/users` | Nested path requires routing surgery in both ASGI and WSGI; query params work today without routing changes |
| Python-side grouping in `render_routes_page()` | Alpine.js `x-data` grouping | Alpine grouping would require passing group metadata to JS; Python grouping at render time is simpler and testable |
| Jinja2 filter for relative time | JavaScript `Date` relative format | Server-side filter produces correct time at page render; no JS required, consistent with SSR pattern |

**Installation:** No new packages required.

---

## Architecture Patterns

### Recommended Project Structure Changes

```
src/flowsurgeon/ui/
├── panel.py                 # Add render_routes_page(), render_route_detail_page(), _group_by_prefix(), _relative_time() filter
├── templates/
│   ├── base.html            # Unchanged — CSS tokens already Phase 1
│   ├── home.html            # REPLACE entirely — becomes routes list view
│   ├── detail.html          # ADD Profile tab to subnav; fix breadcrumb links
│   └── partials/
│       ├── detail_sql.html      # Unchanged
│       ├── detail_traceback.html # Unchanged
│       └── detail_profile.html  # Unchanged (already exists)
src/flowsurgeon/middleware/
├── asgi.py                  # Update _serve_history() to branch on route detail params
└── wsgi.py                  # Same update as asgi.py
```

### Pattern 1: Query-param-based Route Detail Dispatch

**What:** Use `?method=GET&path=/api/users` on the home route to serve the route-filtered request list instead of the home view.

**When to use:** Whenever the user clicks a route row.

**Example — dispatcher in `_serve_history()`:**
```python
# In both asgi.py and wsgi.py _serve_history()
method_param = _parse_qs_param(query_string, "method", "")
path_param   = _parse_qs_param(query_string, "path", "")

if method_param and path_param:
    # Route detail view
    records = await self._storage.list_recent(limit=500)
    body = render_route_detail_page(
        records,
        self._config.debug_route,
        route_method=method_param.upper(),
        route_path=path_param,
        ...filter params...
    ).encode()
else:
    # Routes home view
    body = render_routes_page(
        records,
        self._config.debug_route,
        app_routes=self._app_routes,
        method_filter=method_filter,
    ).encode()
```

### Pattern 2: Path-prefix Grouping in Python

**What:** Group route summaries by the first segment of their path (e.g., `/api/users` and `/api/posts` both go into group `api`).

**When to use:** In `render_routes_page()` to produce grouped sections.

**Example:**
```python
def _group_by_prefix(summaries: list[dict]) -> dict[str, list[dict]]:
    """Group routes by first path segment. '/' prefix → 'root'."""
    from collections import defaultdict
    groups: dict[str, list[dict]] = defaultdict(list)
    for s in summaries:
        parts = s["path"].strip("/").split("/", 1)
        prefix = parts[0] if parts[0] else "root"
        groups[prefix].append(s)
    return dict(groups)
```

### Pattern 3: Relative Time as a Jinja2 Filter

**What:** Add a `_relative_time(ts_str)` filter to `_env` that converts `"2026-03-15 10:30:00"` to `"2m ago"`.

**When to use:** On each route row's "last seen" stat.

**Example:**
```python
def _relative_time(ts_str: str | None) -> str:
    """Convert a UTC datetime string to a human-readable relative label."""
    if not ts_str:
        return "—"
    from datetime import datetime, timezone
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return ts_str
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"

_env.filters["relative_time"] = _relative_time
```

### Pattern 4: Alpine.js Method Filter Pills (client-side)

**What:** Method filter pills (ALL | GET | POST | PUT | DELETE | PATCH) that show/hide route groups without a page reload.

**When to use:** On the routes home page `home.html`.

**Example:**
```html
<div x-data="{ methodFilter: 'ALL' }">
  <div class="filter-pills">
    {% for m in ['ALL', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'] %}
    <button class="pill" :class="methodFilter === '{{ m }}' ? 'pill-active' : ''"
      @click="methodFilter = '{{ m }}'">{{ m }}</button>
    {% endfor %}
  </div>

  {% for prefix, routes in groups.items() %}
  <div class="route-group"
       x-show="methodFilter === 'ALL' || {{ routes | map(attribute='method') | list | tojson }}.includes(methodFilter)">
    ...
  </div>
  {% endfor %}
</div>
```

Note: `tojson` is a built-in Jinja2 filter available in Jinja2 >= 2.9.

### Pattern 5: No-traffic Row Muted Style

**What:** When `has_data` is `False`, apply reduced opacity to the method badge and show dashes for stats.

**When to use:** In route row Jinja2 template.

**Example:**
```html
<a class="tr {% if not route.has_data %}tr-no-traffic{% endif %}"
   href="{{ debug_route }}?method={{ route.method }}&path={{ route.path | urlencode }}">
  <div class="td w-80">
    <span class="method {{ route.method | method_class }} {% if not route.has_data %}method-muted{% endif %}">
      {{ route.method }}
    </span>
  </div>
  <div class="td w-fill u-mono td-path {% if not route.has_data %}u-faint{% endif %}">
    {{ route.path }}
  </div>
  {% if route.has_data %}
  <div class="td w-80">{{ route.count }} reqs</div>
  <div class="td w-110 {{ route.latest_duration_ms | duration_class }}">
    {{ "%.0f"|format(route.latest_duration_ms) }}ms
  </div>
  <div class="td w-80 td-dim">{{ route.latest_query_count }}q</div>
  <div class="td w-80">
    <span class="status {{ route.latest_status | status_class }}">{{ route.latest_status }}</span>
  </div>
  <div class="td w-120 td-dim">{{ route.last_request_time | relative_time }}</div>
  {% else %}
  <div class="td w-fill td-dim u-text-right">No requests</div>
  {% endif %}
</a>
```

CSS additions needed in `base.html`:
```css
.method-muted { opacity: 0.45; }
.pill { ... }       /* method filter pill */
.pill-active { ... } /* active pill styling */
.route-group-hd { ... } /* group header row */
```

### Anti-Patterns to Avoid

- **Using a nested URL path for route detail:** `/flowsurgeon/GET/api/users` would be intercepted by the existing `path.startswith(debug_route + "/")` check and treated as a request ID. Do not go this route.
- **Rendering both tabs from the same render function:** Keep `render_routes_page()` and `render_route_detail_page()` as separate functions. The template context shapes are different enough that merging them adds complexity without benefit.
- **Client-side grouping with Alpine.js:** Grouping in Python gives deterministic output and is testable with `pytest`. Keep grouping on the server side.
- **Rebuilding relative time in Jinja2 macro with string math:** Use a Python filter — Jinja2 macros don't have access to `datetime` or arithmetic reliable enough for this task.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Query string parsing | Custom `split("&")` logic | `_parse_qs_param()` already in `_http.py` | URL encoding edge cases, already handles `keep_blank_values` |
| Route filtering | Custom filter loop | `_filter_records()` already in `panel.py` | Already handles path, method, status, query filters |
| Pagination | Custom slice logic | `_paginate()` already in `panel.py` | Already clamps page, handles edge cases |
| Method badge styling | New CSS classes | Existing `m-GET`, `m-POST`, etc. in `base.html` | Already defined; adding `method-muted` opacity modifier is sufficient |
| Status badge styling | New CSS classes | Existing `s-2xx`, `s-3xx`, etc. in `base.html` | Already defined |
| Duration coloring | New CSS classes | Existing `dur-fast`, `dur-medium`, `dur-slow` in `base.html` | Already defined |

**Key insight:** This codebase has already built the data layer and CSS system. Phase 2 is primarily template and render function work, not new infrastructure.

---

## Common Pitfalls

### Pitfall 1: RHOM-05 vs CONTEXT.md Conflict

**What goes wrong:** REQUIREMENTS.md says "Existing requests grid available as secondary tab/view." CONTEXT.md locked decision says the requests grid is completely removed.

**Why it happens:** Requirements were written before the context discussion resolved the design question.

**How to avoid:** Honor CONTEXT.md. The planner must explicitly note that RHOM-05 is satisfied by interpretation: the routes list IS the primary view, and the all-requests grid is intentionally removed per user decision. Do not re-add a secondary requests tab.

**Warning signs:** Any plan task that adds a second tab showing a flat requests list.

### Pitfall 2: Route Detail URL Conflicts with Request ID Routing

**What goes wrong:** If the route detail URL uses a path like `/flowsurgeon/route/api/users`, the existing ASGI/WSGI routing treats everything starting with `debug_route + "/"` as a request ID, producing a 404.

**Why it happens:** The routing is a simple prefix check, not a router with pattern matching.

**How to avoid:** Use query params (`?method=GET&path=/api/users`) on the base `debug_route`. The `_serve_history()` dispatcher checks for these params and branches.

**Warning signs:** Any task that adds a new path segment under `debug_route/` that is not a UUID.

### Pitfall 3: Profile Tab Missing from detail.html

**What goes wrong:** `detail_profile.html` partial exists in `partials/` but is NOT included in `detail.html`. The current subnav only has Details, SQL, Traceback — no Profile tab.

**Why it happens:** The Profile tab was removed in Phase 1 ("Latency & Queries, Profiling, and Profile tabs removed from home/detail pages"). The STATE.md records this.

**How to avoid:** Per DPOL-02 requirement, all 4 tabs must be visually consistent. CONTEXT.md says "All 4 request detail tabs (Details, SQL, Traceback, Profile) inherit the Phase 1 CSS design system." This means the Profile tab must be RE-ADDED to `detail.html` with the Phase 1 design system. The partial already exists — just add it back to the subnav and content.

**Warning signs:** Any plan that only touches 3 tabs on the detail page.

### Pitfall 4: `last_request_time` is a Formatted String, Not a datetime

**What goes wrong:** `_build_endpoint_summaries()` stores `last_request_time` as `latest.timestamp.strftime("%Y-%m-%d %H:%M:%S")` — a string without timezone info. The `_relative_time` filter must parse it back as UTC.

**Why it happens:** The builder formats the timestamp for display convenience. For relative time we need to re-parse it.

**How to avoid:** The `_relative_time` Jinja2 filter must use `datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)` before computing the delta.

**Warning signs:** Relative time showing unreasonably large values ("87600h ago") due to no timezone on parse.

### Pitfall 5: URL-encoding Path Parameters

**What goes wrong:** Paths like `/api/users/{id}` contain `{` and `}` characters. When building the route detail URL `?path=/api/users/{id}`, the braces must be URL-encoded.

**Why it happens:** Curly braces are not reserved in query strings but can confuse some parsers.

**How to avoid:** Use `| urlencode` Jinja2 filter (built-in) when constructing route detail href. On the Python side, `_parse_qs_param` uses `urllib.parse.parse_qs` which handles decoding correctly.

### Pitfall 6: Alpine.js Method Filter with Groups

**What goes wrong:** If Alpine.js hides entire groups when the method filter doesn't match, a group with mixed methods (e.g., `api` group has GET and POST routes) would disappear when POST is selected, hiding the POST routes.

**Why it happens:** Naive group-level `x-show` checks the group, not individual rows.

**How to avoid:** Apply `x-show` on individual route rows, not on group containers. Keep group headers visible if any route in the group matches, or apply `x-show` on rows with the data-method attribute:

```html
<a class="tr" x-show="methodFilter === 'ALL' || methodFilter === '{{ route.method }}'" ...>
```

---

## Code Examples

### New `render_routes_page()` Function Signature

```python
def render_routes_page(
    records: list[RequestRecord],
    debug_route: str,
    app_routes: list[tuple[str, str]] | None = None,
    method_filter: str = "",
    sort: str = "duration",
) -> str:
    """Return the full HTML home page with Swagger-style routes list."""
    summaries = _build_endpoint_summaries(
        records,
        app_routes or [],
        method_filter=method_filter,
        sort=sort,
    )
    groups = _group_by_prefix(summaries)
    tmpl = _env.get_template("home.html")
    return tmpl.render(
        groups=groups,
        debug_route=debug_route,
        method_filter=method_filter,
        sort=sort,
        total_routes=len(summaries),
    )
```

### New `render_route_detail_page()` Function Signature

```python
def render_route_detail_page(
    records: list[RequestRecord],
    debug_route: str,
    route_method: str,
    route_path: str,
    # filters for the request list
    status: str = "",
    sort: str = "duration",
    page: int = 1,
    show: int = 25,
    # for breadcrumb
    profiling_enabled: bool = False,
) -> str:
    """Return the filtered request list for a specific route."""
    filtered = _filter_records(records, method=route_method, path=route_path)
    # apply sort, paginate
    page_items, total_pages, page = _paginate(filtered, page, show)
    tmpl = _env.get_template("route_detail.html")  # new template
    return tmpl.render(
        records=page_items,
        total_records=len(filtered),
        route_method=route_method,
        route_path=route_path,
        debug_route=debug_route,
        status=status,
        sort=sort,
        page=page,
        total_pages=total_pages,
        ...
    )
```

### Route Row URL Construction in Jinja2

```html
{# URL-encode path to handle curly-brace path params #}
<a class="tr" href="{{ debug_route }}?method={{ route.method }}&amp;path={{ route.path | urlencode }}">
```

Note: Jinja2's `urlencode` filter encodes the entire string (spaces → `%20`, braces → `%7B%7D`). This is correct for a query param value.

### Breadcrumb on Route Detail Page

```html
{# route_detail.html topbar block #}
<nav class="topbar">
  <span class="logo">FlowSurgeon</span>
  <div class="breadcrumb">
    <a class="b-dim" href="{{ debug_route }}">FlowSurgeon</a>
    <span class="sep">›</span>
    <span class="b-cur">
      <span class="method {{ route_method | method_class }}">{{ route_method }}</span>
      <span class="u-mono u-text-sm">{{ route_path }}</span>
    </span>
  </div>
</nav>
```

### Breadcrumb on Request Detail Page (3-level)

```html
{# detail.html — updated topbar block #}
<nav class="topbar">
  <span class="logo">FlowSurgeon</span>
  <div class="breadcrumb">
    <a class="b-dim" href="{{ debug_route }}">FlowSurgeon</a>
    <span class="sep">›</span>
    <a class="b-mid" href="{{ debug_route }}?method={{ record.method }}&path={{ record.path | urlencode }}">
      <span class="method {{ record.method | method_class }}">{{ record.method }}</span>
      <span class="u-mono u-text-sm">{{ record.path }}</span>
    </a>
    <span class="sep">›</span>
    <span class="b-cur">{{ record.request_id[:8] }}</span>
  </div>
</nav>
```

Note: `render_detail_page()` must receive the route path and method to construct the middle breadcrumb. These are already on the `record` object (`record.method`, `record.path`) — no new parameters needed.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All-requests flat list as home | Routes list (Swagger-style) as home | Phase 2 | Home page restructured; all-requests view removed |
| `render_history_page()` is the home renderer | `render_routes_page()` replaces it | Phase 2 | Old function becomes dead code or gets repurposed |
| Breadcrumb 2-level: `Requests > path > id` | Breadcrumb 3-level: `FlowSurgeon > METHOD /path > #id` | Phase 2 | `detail.html` topbar updated |
| Profile tab absent from detail.html | Profile tab re-added with Phase 1 design | Phase 2 | DPOL-02 satisfied |

**Deprecated/outdated in this phase:**
- `render_history_page()`: Will no longer be called from middleware. Can be kept for backward compatibility or removed — the planner should decide.
- The `view` parameter in `render_history_page()`: Was for switching between "latency" and "profiling" tab views that have already been removed.

---

## Open Questions

1. **RHOM-05 interpretation**
   - What we know: REQUIREMENTS.md says "Existing requests grid available as secondary tab/view." CONTEXT.md locks the all-requests list as completely removed.
   - What's unclear: Whether RHOM-05 should be marked as "satisfied by design decision" or modified.
   - Recommendation: Mark RHOM-05 as satisfied by the route-filtered request view (each route detail page IS a filtered requests view). No secondary all-requests tab needed.

2. **`render_history_page()` fate**
   - What we know: It will no longer be called after this phase.
   - What's unclear: Whether to keep it (backward compat for any direct callers outside middleware) or remove it.
   - Recommendation: Keep the function, mark it as deprecated via docstring. This is a public API surface.

3. **`_filter_records()` does exact path match**
   - What we know: `_filter_records(path=...)` does `r.path == path` — an exact match.
   - What's unclear: FastAPI path-param routes like `/api/users/{id}` would discover the template path `/api/users/{id}` but recorded requests would have concrete paths like `/api/users/42`. These would not match.
   - Recommendation: For Phase 2, use exact match for now (consistent with existing behavior). Flag this as a known limitation — route template matching is a v2 concern.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x + pytest-asyncio |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/test_asgi.py tests/test_wsgi.py -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RHOM-01 | Home page renders routes list as primary view | integration | `uv run pytest tests/test_asgi.py -k "routes_home" -x` | ❌ Wave 0 |
| RHOM-02 | Route row shows method badge + path | integration | `uv run pytest tests/test_asgi.py -k "route_row" -x` | ❌ Wave 0 |
| RHOM-03 | Method filter pills filter routes | integration | `uv run pytest tests/test_asgi.py -k "method_filter" -x` | ❌ Wave 0 |
| RHOM-04 | No-traffic routes show muted style | integration | `uv run pytest tests/test_asgi.py -k "no_traffic" -x` | ❌ Wave 0 |
| RHOM-05 | (Satisfied by design — old requests grid removed) | manual | visual inspection | N/A |
| RDET-01 | Route detail URL returns filtered request list | integration | `uv run pytest tests/test_asgi.py -k "route_detail" -x` | ❌ Wave 0 |
| RDET-02 | Route detail has filter/sort controls | integration | `uv run pytest tests/test_asgi.py -k "route_detail_filters" -x` | ❌ Wave 0 |
| RDET-03 | Breadcrumb shows method + path | integration | `uv run pytest tests/test_asgi.py -k "breadcrumb" -x` | ❌ Wave 0 |
| DPOL-01 | Detail page renders with CSS tokens | integration | `uv run pytest tests/test_asgi.py -k "detail_css" -x` | ❌ Wave 0 |
| DPOL-02 | All 4 tabs present in detail page | integration | `uv run pytest tests/test_asgi.py -k "detail_profile_tab" -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_asgi.py` — extend with routes-home and route-detail test cases (file exists, needs new test functions)
- [ ] `tests/test_wsgi.py` — same as ASGI tests but for WSGI middleware (file exists, needs new test functions)
- [ ] Test helper: `_make_route_detail_scope(method, path)` — convenience for constructing route-detail request scopes

*(Core test infrastructure exists. Only new test functions needed, not new files.)*

---

## Sources

### Primary (HIGH confidence)
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/ui/panel.py` — `_build_endpoint_summaries()`, `_filter_records()`, `_paginate()`, `_env` filter registration patterns
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/middleware/asgi.py` — `_serve_history()`, `_serve_detail()`, URL routing logic
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/middleware/wsgi.py` — same routing patterns
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/ui/templates/base.html` — full CSS token set, utility classes, existing component classes
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/ui/templates/detail.html` — breadcrumb structure, subnav tabs, Alpine.js data pattern
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/ui/templates/home.html` — current template structure being replaced
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/ui/templates/partials/detail_profile.html` — Profile tab partial already exists
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/src/flowsurgeon/_http.py` — `_parse_qs_param()`, `_parse_qs_int()`
- Direct code reading: `/home/voidp/Projects/oss/flowsurgeon/pyproject.toml` — test config, dependency versions

### Secondary (MEDIUM confidence)
- Jinja2 `urlencode` filter: Built-in as of Jinja2 2.7; project uses `>=3.1.0` — confirmed available
- Alpine.js `x-show` on individual elements: Standard Alpine.js pattern; no breaking changes in version currently vendored

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all libraries confirmed in codebase
- Architecture: HIGH — based on direct code reading of all relevant source files
- Pitfalls: HIGH — all pitfalls identified from actual code examination (URL routing logic, timestamp format, missing Profile tab, Alpine.js group-level filtering)
- Validation: HIGH — existing test framework examined; test file structure confirmed

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable stack — no fast-moving dependencies)
