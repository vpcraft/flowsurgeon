# Features Research

**Domain:** Python debug middleware / profiling UI tools
**Researched:** 2026-03-15
**Scope:** What features professional debug tools and API explorers offer. What's table stakes vs differentiating for a public announcement.

---

## Table Stakes (16 features)

Features users expect from a professional debug middleware. Missing any of these at announcement time would undermine credibility.

| # | Feature | Complexity | Status in FlowSurgeon | Notes |
|---|---------|------------|----------------------|-------|
| 1 | Request list with method/status/duration | Low | Done | Card grid view |
| 2 | SQL queries panel | Medium | Done | SQLAlchemy + DB-API trackers |
| 3 | Request/response headers view | Low | Done | With redaction |
| 4 | Response body capture | Low | Done | Up to 128 KB |
| 5 | Color-coded status badges | Low | Done | 2xx/3xx/4xx/5xx |
| 6 | HTTP method badges (Swagger convention) | Low | Partial | Need colored pills: GET=blue, POST=green, PUT=orange, DELETE=red |
| 7 | Duplicate query detection | Low | Done | `dup` badge |
| 8 | Slow query detection | Low | Done | `slow` badge |
| 9 | Kill switch (env var) | Low | Done | `FLOWSURGEON_ENABLED` |
| 10 | Localhost-only access | Low | Done | `allowed_hosts` config |
| 11 | Persistent history | Low | Done | SQLite with auto-pruning |
| 12 | Filtering and pagination | Medium | Done | Path filter, sort, pagination |
| 13 | API routes list home page | Medium | **Not done** | Routes discovered but not shown as primary view |
| 14 | Injected panel button | Low | Done | Panel injection into HTML |
| 15 | Dark theme | Low | Done | Custom dark CSS |
| 16 | Professional documentation site | Medium | **Not done** | Only README exists |

---

## Differentiators (11 features)

Features that set FlowSurgeon apart from alternatives. These are competitive advantages.

| # | Feature | Complexity | Status | Why it differentiates |
|---|---------|------------|--------|----------------------|
| 1 | Framework-agnostic (WSGI + ASGI) | High | Done | django-debug-toolbar is Django-only; Flask-DebugToolbar is Flask-only |
| 2 | Route detail page (API explorer + request history) | Medium | **Not done** | Bridges Swagger-like routes view with debug request history — unique combo |
| 3 | cProfile per-request call graph | Medium | Done | Most debug toolbars don't offer this |
| 4 | Callers drilldown per function | Medium | Done | Deep profiling visibility |
| 5 | Query stack traces | Low | Done | With `capture_query_stacktrace=True` |
| 6 | Zero heavy dependencies | Low | Done | Only jinja2 at runtime |
| 7 | Single-line integration | Low | Done | `FlowSurgeon(app)` |
| 8 | DB-API 2.0 transparent proxy | Medium | Done | Works with any DB-API driver |
| 9 | SQLAlchemy event listener | Medium | Done | Non-invasive engine events |
| 10 | shadcn-inspired UI redesign | Medium | **Not done** | Professional visual quality for screenshots |
| 11 | Request body capture | Medium | **Not done** | `RequestRecord` has no `request_body` field — non-trivial to add |

**Key finding:** `RequestRecord` has no `request_body` field. Implementing request body capture requires schema migration, middleware changes in both WSGI and ASGI, size cap config, and opt-out toggle. Should be post-v0.6.0.

---

## Anti-Features (12 items)

Things to deliberately NOT build. Including reasoning to prevent scope creep.

| # | Feature | Why NOT |
|---|---------|---------|
| 1 | "Try it out" API sender (like Swagger) | FlowSurgeon is a debug tool, not an API client. Adds massive complexity. |
| 2 | OpenAPI spec parsing | Would require openapi-spec-validator dep; routes are discovered from framework, not spec files |
| 3 | Production sampling/APM | Out of scope — tools like Sentry/Datadog do this. FlowSurgeon is for local dev. |
| 4 | Plugin API / Panel base class | Deferred to future version per PROJECT.md |
| 5 | React/Webpack build toolchain | Project constraint: no build step |
| 6 | Mobile-responsive debug UI | Developers use this on desktop |
| 7 | Auth on debug UI | `allowed_hosts` is sufficient for dev tool; auth adds complexity |
| 8 | Distributed tracing | Out of scope — use OpenTelemetry for that |
| 9 | Log capture panel | Would require logging handler integration; adds complexity without clear value |
| 10 | Template rendering timing | Django-specific feature; not framework-agnostic |
| 11 | Django ORM support | Deferred to future version |
| 12 | Cache hit/miss tracking | Deferred to future version |

---

## Feature Dependencies

```
Route discovery (done) ──► Routes home page (not done) ──► Route detail page (not done)
SQL tracking (done) ──► SQL tab + badges (done)
cProfile (done) ──► Profile tab + callers (done)
SQLite storage (done) ──► History + pagination (done)
CSS design system (not done) ──► All UI pages ──► Screenshots ──► Announcement
Docs site (not done) ──► Announcement
CI/CD polish (not done) ──► Announcement
```

---

## MVP Recommendation for v0.6.0

Ordered by dependency and impact:

1. **CSS design system** — shadcn-inspired tokens in `base.html` (unlocks visual consistency everywhere)
2. **API routes list home page** — Swagger-like primary view (data pipeline already exists)
3. **Route detail page** — filtered requests per endpoint (reuse existing grid)
4. **Documentation site** — MkDocs + Material (installation, config reference, quick start)
5. **CI/CD polish** — ruff in CI, docs deployment, coverage

**Deferred to post-v0.6.0:**
- Request body capture (schema migration needed)
- Plugin API
- Additional ORM adapters

---

*Research date: 2026-03-15*
