# Roadmap: FlowSurgeon v0.6.0

## Overview

v0.6.0 is a polish-and-launch milestone on top of a working v0.5.0 codebase. The core middleware, SQL tracking, cProfile integration, and request history are all shipping. What remains is making the tool look and feel like a professional product: a cohesive CSS design system, two new UI pages (routes home and route detail), security documentation, and the announcement assets needed for a credible public launch on Reddit/X. Phases are ordered by visual dependency — the design system lands first so every subsequent page looks correct on first implementation.

## Phases

- [x] **Phase 1: CSS Design System** - Refactor UI to shadcn-inspired CSS custom properties with Swagger-convention method badges (completed 2026-03-14)
- [ ] **Phase 2: Routes Pages** - Build routes home page and route detail page, polish detail tabs
- [ ] **Phase 3: Security Documentation** - Write security and production-warning docs
- [ ] **Phase 4: Announcement Assets** - Produce screenshots, demo GIF, and README for public launch

## Phase Details

### Phase 1: CSS Design System
**Goal**: The UI has a coherent, professional visual foundation that all pages inherit from
**Depends on**: Nothing (first phase)
**Requirements**: UIDS-01, UIDS-02, UIDS-03, UIDS-04, UIDS-05
**Success Criteria** (what must be TRUE):
  1. All color and spacing values are defined as CSS custom properties in `:root {}` — no hardcoded hex or px literals remain in templates
  2. HTTP method badges display Swagger-convention colors: GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple
  3. Containers are defined by clean borders, not box shadows
  4. Labels and values use distinct typographic weights/colors — labels are muted, values are bright
  5. No inline `style=` attributes remain in any template — all overrides are utility classes
**Plans:** 2/2 plans complete
Plans:
- [ ] 01-01-PLAN.md — Build CSS token layer, refactor base.html (tokens, badges, borders, typography, utilities)
- [ ] 01-02-PLAN.md — Replace inline style= attributes across all template files with utility classes

### Phase 2: Routes Pages
**Goal**: Users can navigate a Swagger-like routes list as the home page and drill into per-route request history
**Depends on**: Phase 1
**Requirements**: RHOM-01, RHOM-02, RHOM-03, RHOM-04, RHOM-05, RDET-01, RDET-02, RDET-03, DPOL-01, DPOL-02
**Success Criteria** (what must be TRUE):
  1. Visiting `/flowsurgeon` shows an API routes list as the primary view, with method badge + path + description per route
  2. Routes with no traffic are visually distinct (muted style) from routes that have received requests
  3. Routes can be sorted or grouped by HTTP method
  4. Clicking a route navigates to a filtered view showing only requests for that endpoint, with method + path in the breadcrumb
  5. The filtered route view includes status, duration, and date controls; all 4 request detail tabs (Details, SQL, Traceback, Profile) are visually consistent with the design system
**Plans**: TBD

### Phase 3: Security Documentation
**Goal**: Users understand that FlowSurgeon is a development tool and how to keep it safe
**Depends on**: Nothing (independent of UI work)
**Requirements**: SDOC-01, SDOC-02, SDOC-03
**Success Criteria** (what must be TRUE):
  1. Documentation covers `allowed_hosts`, header redaction behavior, and the `FLOWSURGEON_ENABLED` env var kill switch
  2. A production warning is visible in the Quick Start — "FlowSurgeon is a development tool. Do not enable in production."
  3. Docs include guidance on adding `flowsurgeon.db` to `.gitignore`
**Plans**: TBD

### Phase 4: Announcement Assets
**Goal**: The project has compelling, accurate screenshots and a demo GIF ready for a public announcement
**Depends on**: Phase 2, Phase 3
**Requirements**: ANMT-01, ANMT-02
**Success Criteria** (what must be TRUE):
  1. README contains fresh screenshots showing the redesigned routes home page and request detail view with realistic data
  2. A 30-60 second demo GIF or video exists showing the install-to-debug-UI flow
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. CSS Design System | 2/2 | Complete   | 2026-03-14 |
| 2. Routes Pages | 0/TBD | Not started | - |
| 3. Security Documentation | 0/TBD | Not started | - |
| 4. Announcement Assets | 0/TBD | Not started | - |
