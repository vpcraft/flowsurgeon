# Project Research Summary

**Project:** FlowSurgeon v0.6.0
**Domain:** Python debug middleware / profiling UI tools
**Researched:** 2026-03-15
**Confidence:** HIGH

## Executive Summary

FlowSurgeon v0.6.0 is a polish-and-launch milestone on top of a working v0.5.0 codebase. The core middleware, SQL tracking, cProfile integration, and SQLite storage are all done. What remains is entirely dev/docs tooling: a UI redesign to professional quality, two new UI pages (routes home and route detail), a documentation site, and CI/CD hardening. No new runtime dependencies are required — the architectural constraint of zero-dependency-except-Jinja2 is preserved throughout.

The recommended approach is a dependency-ordered build sequence. The CSS design system must come first because it makes every subsequent page look professional and enables screenshot-worthy output. The routes home page comes second because its data pipeline already exists (`_build_endpoint_summaries()` is written); only the template and render function signature need to change. Documentation and CI/CD are independent of the UI work and can proceed in parallel, but must complete before any public announcement.

The key risks are announcement-readiness, not technical. Missing compelling screenshots, a CDN dependency breaking air-gapped installs, and a security section absent from docs are the failure modes most likely to cause a poor first impression or credibility damage. All are preventable with explicit phase gates before the announcement phase.

---

## Key Findings

### Recommended Stack

The existing runtime stack (Python 3.12+, Jinja2 3.1.6, SQLite3, Alpine.js 3.x bundled) must not change. All additions for v0.6.0 are dev/docs tooling only. MkDocs with Material theme is the correct documentation choice — it is the industry standard for Python OSS projects (FastAPI, Pydantic, Ruff, uv all use it), requires only Markdown, and deploys to GitHub Pages with one command. Ruff for linting and formatting is already configured in pyproject.toml; it simply needs to be added to the CI pipeline.

**Core technologies:**
- Python 3.12+ / Jinja2 3.1.6 / SQLite3: Runtime stack — frozen, no changes
- Alpine.js 3.x (bundled): SPA-like interactivity — already bundled inline, no CDN
- mkdocs >= 1.6.0 + mkdocs-material >= 9.5.0: Documentation site — Markdown-based, GitHub Pages deployment
- ruff >= 0.5.0: Linting + formatting in CI — already in pyproject.toml, needs CI integration
- CSS custom properties (no framework): UI design system — shadcn-inspired tokens, no build step

**Critical version note:** mkdocs and ruff version numbers are MEDIUM confidence — verify against PyPI before pinning in pyproject.toml.

### Expected Features

Two table-stakes features are not yet done and block announcement: the API routes list home page (route discovery data is available but not surfaced as the primary view) and a professional documentation site. One table-stakes feature is partially done: HTTP method badges need colored pills following Swagger convention. All other 13 table-stakes features are complete.

Two differentiators are not yet done: the shadcn-inspired UI redesign (visual quality for screenshots) and the route detail page (filtered request history per endpoint). Request body capture is a differentiator that is explicitly deferred — it requires schema migration and is post-v0.6.0.

**Must have (table stakes):**
- API routes list home page — route data exists, template/render function must be wired up
- Professional documentation site — only README exists today
- HTTP method colored pills (GET=blue, POST=green, PUT=orange, DELETE=red) — partially done

**Should have (competitive differentiators):**
- shadcn-inspired CSS design system — unlocks visual consistency and screenshot quality
- Route detail page — filtered history per endpoint, unique combo of Swagger-like view + debug history

**Defer to post-v0.6.0:**
- Request body capture — requires `RequestRecord` schema migration, WSGI/ASGI middleware changes, size cap config
- Plugin API / Panel base class — per PROJECT.md
- Additional ORM adapters (Django ORM, etc.)

### Architecture Approach

The v0.6.0 architecture requires no structural changes — it is additive wiring of existing components. The `_build_endpoint_summaries()` function already merges routes + records into the correct shape for the routes home page; only `render_history_page()` needs to be extended to accept and pass `app_routes`. The route detail page reuses `home.html` with a `route_context` variable rather than a new template. The CSS refactor replaces hardcoded hex values in `base.html` with semantic CSS custom properties — this is the riskiest change surface-area-wise because it touches every page, but it is well-scoped to one file.

**Major components:**
1. `middleware/wsgi.py` + `middleware/asgi.py` — Pass `app_routes` to render call; add route detail dispatch handler
2. `ui/panel.py` — Extend render function signature; add route-context Jinja filters
3. `ui/templates/base.html` — Full CSS refactor to CSS custom properties (`:root {}` token system)
4. `ui/templates/home.html` — Full redesign: routes table as primary view, requests as secondary
5. `docs/` (new) — MkDocs + Material; `mkdocs.yml` config; installation/config/security pages

### Critical Pitfalls

1. **Screenshot gap** — Announcing without compelling screenshots means the post gets scrolled past. UI redesign must be complete and fresh screenshots taken before any announcement. Include both routes list and detail view with realistic data.

2. **No security section in docs** — Users may deploy to staging/production without understanding the risk. Docs must include a dedicated Security page covering `allowed_hosts`, header redaction, env var kill switch, and response body implications. The Quick Start must include a production warning banner.

3. **False-green CI** — Tests pass but linting/formatting are unchecked. Add `ruff check` and `ruff format --check` to `ci.yaml`. Add `--cov=src/flowsurgeon` to pytest step.

4. **CDN dependency creep** — Any `<link>` to external fonts or CDN scripts breaks the tool in air-gapped environments. Use system font stack only. All JS is already bundled.

5. **Announcement framing as "another debug toolbar"** — The unique angle (framework-agnostic, WSGI + ASGI, cProfile integration) must lead the announcement. Prepare a comparison table vs django-debug-toolbar, Flask-DebugToolbar, and Sentry in docs before launch.

---

## Implications for Roadmap

Based on research, the build sequence is driven by visual dependencies: everything that appears in the UI inherits from the CSS design system, so that must land first. The data pipeline for routes is already built, making the routes home page low-risk to implement second. CI/CD and docs are independent tracks that can proceed in parallel with UI work.

### Phase 1: CSS Design System

**Rationale:** Every subsequent UI page inherits from `base.html`. Doing the design system first means the routes home page, route detail page, and all detail views look correct on first implementation rather than requiring a second visual pass.
**Delivers:** `base.html` refactored to CSS custom properties; shadcn-inspired dark token set; HTTP method colored pills; detail page visual refresh as a side effect.
**Addresses:** FEATURES table-stakes #6 (method badges), differentiator #10 (shadcn UI)
**Avoids:** PITFALL-3 (screenshot gap), PITFALL-4 (CDN dependency)

### Phase 2: Routes Home Page + Route Detail Page

**Rationale:** The data pipeline (`_build_endpoint_summaries()`) is complete. This is a template + render function wiring task, not a new data layer. Route detail page reuses `home.html` with `route_context` — minimal new code.
**Delivers:** `/flowsurgeon` as a Swagger-like routes table primary view; `/flowsurgeon/routes/{METHOD}/{path}` filtered request history per endpoint.
**Addresses:** FEATURES table-stakes #13 (routes list), differentiator #2 (route detail page)
**Implements:** Architecture components — middleware dispatch update, `render_routes_page()`, `route_context` variable

### Phase 3: Documentation Site

**Rationale:** MkDocs setup is straightforward and independent of UI work. Must be complete before announcement. Security section is non-negotiable for credibility.
**Delivers:** `docs/` directory with mkdocs.yml; Quick Start; Configuration Reference; Security page; GitHub Pages deployment via `docs.yml` workflow.
**Addresses:** FEATURES table-stakes #16 (professional docs site)
**Avoids:** PITFALL-1 (response body default), PITFALL-2 (SQLite permissions), PITFALL-7 (no security section), PITFALL-8 (no gitignore guidance), PITFALL-13 (getting started path)

### Phase 4: CI/CD Polish + Packaging

**Rationale:** Independent of UI and docs. Adds linting, coverage, and docs deployment to CI. Also addresses packaging hygiene (py.typed, Python version floor decision, CHANGELOG commit, Documentation URL in pyproject.toml).
**Delivers:** `ci.yaml` with ruff check + coverage; `docs.yml` workflow; py.typed verification; CHANGELOG.md committed.
**Uses:** ruff >= 0.5.0 (already in pyproject.toml); mkdocs gh-deploy (from docs group)
**Avoids:** PITFALL-5 (Python version floor), PITFALL-6 (py.typed), PITFALL-9 (false-green CI), PITFALL-10 (no integration tests)

### Phase 5: Pre-Announcement Preparation

**Rationale:** Announcement readiness is its own phase — it requires artifacts (screenshots, GIF/video, comparison table) that depend on all prior phases being complete.
**Delivers:** Fresh screenshots after UI redesign; demo GIF showing install-to-UI flow; comparison table vs alternatives; framing for Reddit/HN announcement.
**Avoids:** PITFALL-11 (announcement framing), PITFALL-12 (no demo GIF)

### Phase Ordering Rationale

- CSS design system before routes home page: avoids a second visual-polish pass on newly built pages
- Routes home before docs: ensures screenshots taken for docs are of the final UI
- CI/CD in parallel with docs: independent track, no blockers either direction
- Pre-announcement last: all prior phases must gate into this one — no shortcuts

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (CI/CD):** Python version floor decision (3.10 vs 3.12) requires checking whether any 3.12-specific syntax or stdlib features are actually used in the codebase — codebase audit needed.
- **Phase 3 (Docs):** mkdocs-material plugin selection (search, social cards, etc.) may need version verification against PyPI before locking the docs dependency group.

Phases with standard patterns (skip research-phase):
- **Phase 1 (CSS Design System):** CSS custom properties pattern is well-documented; exact token values are specified in ARCHITECTURE.md.
- **Phase 2 (Routes Pages):** Architecture is fully specified; data pipeline already exists; no unknowns.
- **Phase 5 (Announcement):** Communication tasks, no technical research needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Runtime stack is HIGH confidence (locked). MkDocs/ruff versions are MEDIUM — verify on PyPI before pinning |
| Features | HIGH | Based on deep codebase analysis cross-referenced with competitive tools; feature status verified against actual code |
| Architecture | HIGH | Based on direct codebase analysis of v0.5.0; data pipeline existence confirmed; no speculative dependencies |
| Pitfalls | HIGH | Pitfalls are grounded in concrete code gaps and well-documented OSS launch failure modes |

**Overall confidence:** HIGH

### Gaps to Address

- **Python version floor (3.10 vs 3.12):** Research flagged this but did not audit the codebase for 3.12-specific usage. During Phase 4 planning, grep for 3.12-specific syntax (match statements with certain patterns, `tomllib`, `sys.monitoring`). If none found, consider lowering to 3.10.
- **mkdocs-material exact version:** Marked MEDIUM confidence. Verify `mkdocs-material >= 9.5.0` is current on PyPI before locking.
- **ruff exact version:** Marked MEDIUM confidence. Verify `ruff >= 0.5.0` reflects current stable releases.
- **Integration test coverage:** PITFALL-10 flagged that tests may use mock apps rather than real Flask/FastAPI instances. Audit test suite during Phase 4 planning before deciding whether to add integration tests.

---

## Sources

### Primary (HIGH confidence)
- Codebase analysis (v0.5.0) — feature status, architecture components, data flow, component boundaries
- ARCHITECTURE.md — CSS token values, routing patterns, build order rationale
- FEATURES.md — feature inventory with status, dependency graph, MVP recommendation

### Secondary (MEDIUM confidence)
- MkDocs and mkdocs-material documentation (training data, 2025) — version requirements, deployment commands
- Ruff documentation (training data, 2025) — CLI flags, CI integration pattern
- shadcn/ui design system patterns — CSS custom properties approach, visual signature rules

### Tertiary (LOW confidence)
- Python version adoption statistics — basis for PITFALL-5 (Python 3.10/3.11 still widely used); validate against current PyPI download stats if the version floor decision is contentious

---

*Research completed: 2026-03-15*
*Ready for roadmap: yes*
