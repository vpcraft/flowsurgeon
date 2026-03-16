# Requirements: FlowSurgeon v0.6.0

**Defined:** 2026-03-15
**Core Value:** Developers can instantly see what their Python web app is doing — every request, every SQL query, every hotspot — without modifying application code.

## v1 Requirements

Requirements for v0.6.0 release. Each maps to roadmap phases.

### UI Design System

- [x] **UIDS-01**: All hardcoded CSS values extracted to `:root {}` custom properties (colors, spacing, radii)
- [x] **UIDS-02**: HTTP method badges follow Swagger convention (GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple)
- [x] **UIDS-03**: Clean borders over shadows as primary container definition
- [x] **UIDS-04**: Muted label / bright value typographic hierarchy
- [x] **UIDS-05**: Inline style overrides in templates replaced with utility classes

### Routes Home Page

- [x] **RHOM-01**: Home page (`/flowsurgeon`) displays API routes list as primary view
- [x] **RHOM-02**: Each route shows HTTP method badge + path + description (if available)
- [x] **RHOM-03**: Routes grouped or sortable by method
- [x] **RHOM-04**: Routes with no traffic shown in muted style
- [x] **RHOM-05**: Existing requests grid available as secondary tab/view

### Route Detail Page

- [x] **RDET-01**: Clicking a route navigates to filtered view showing only requests for that endpoint
- [x] **RDET-02**: Route detail shows filtering and sorting controls (status, duration, date)
- [x] **RDET-03**: Route breadcrumb shows method + path context

### Detail Page Polish

- [x] **DPOL-01**: Request detail page inherits new CSS design system
- [x] **DPOL-02**: All 4 tabs (Details, SQL, Traceback, Profile) visually consistent with new design

### Security Documentation

- [x] **SDOC-01**: Security section documenting allowed_hosts, header redaction, env var kill switch
- [x] **SDOC-02**: Production warning: "FlowSurgeon is a development tool. Do not enable in production."
- [x] **SDOC-03**: Guidance on .gitignore for flowsurgeon.db

### Announcement Assets

- [x] **ANMT-01**: Fresh README screenshots showing redesigned UI with realistic data
- [x] **ANMT-02**: Demo GIF or video (30-60 seconds) showing install, wrap app, browse debug UI

## v2 Requirements

Deferred to future releases. Tracked but not in current roadmap.

### Plugin API

- **PLUG-01**: Panel base class with `title`, `collect()`, `render()` interface
- **PLUG-02**: Plugin registration via `FlowSurgeon(app, panels=[MyPanel()])`

### Additional ORM Adapters

- **OADP-01**: TortoiseORM query tracker
- **OADP-02**: Django ORM query tracker

### Documentation Site

- **DOCS-01**: Full MkDocs + Material docs site (installation, config reference, adapter guide)
- **DOCS-02**: Comparison table vs django-debug-toolbar / Flask-DebugToolbar

### CI/CD

- **CICD-01**: Ruff linting and format checking in GitHub Actions
- **CICD-02**: Coverage reporting in CI
- **CICD-03**: Docs deployment workflow (mkdocs gh-deploy)

### Additional Features

- **FEAT-01**: Request body capture (requires RequestRecord schema migration)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| "Try it out" API sender | FlowSurgeon is a debug tool, not an API client |
| OpenAPI spec parsing | Routes discovered from framework, not spec files |
| Production sampling/APM | Use Sentry/Datadog for that |
| React/Webpack build toolchain | Project constraint: no build step |
| Mobile-responsive debug UI | Developers use this on desktop |
| Auth on debug UI | `allowed_hosts` is sufficient for dev tool |
| Distributed tracing | Use OpenTelemetry for that |
| Log capture panel | Adds complexity without clear value |
| Tailwind CSS | Requires PostCSS build step |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| UIDS-01 | Phase 1 | Complete |
| UIDS-02 | Phase 1 | Complete |
| UIDS-03 | Phase 1 | Complete |
| UIDS-04 | Phase 1 | Complete |
| UIDS-05 | Phase 1 | Complete |
| RHOM-01 | Phase 2 | Complete |
| RHOM-02 | Phase 2 | Complete |
| RHOM-03 | Phase 2 | Complete |
| RHOM-04 | Phase 2 | Complete |
| RHOM-05 | Phase 2 | Complete |
| RDET-01 | Phase 2 | Complete |
| RDET-02 | Phase 2 | Complete |
| RDET-03 | Phase 2 | Complete |
| DPOL-01 | Phase 2 | Complete |
| DPOL-02 | Phase 2 | Complete |
| SDOC-01 | Phase 3 | Complete |
| SDOC-02 | Phase 3 | Complete |
| SDOC-03 | Phase 3 | Complete |
| ANMT-01 | Phase 4 | Complete |
| ANMT-02 | Phase 4 | Complete |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 after roadmap creation*
