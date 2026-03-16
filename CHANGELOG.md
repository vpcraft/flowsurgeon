# Changelog

All notable changes to FlowSurgeon are documented in this file.

---

## [v0.6.0] — 2026-03-16

### Added

- **Light mode** support with system-preference detection.
- **Toggle group** component replacing CSS pill filters on the home page.
- **Breadcrumb navigation** — logo link, slash separators, no duplicates across home and detail pages.
- Playwright-based screenshot capture script and announcement assets.
- README rewritten with repo-relative image paths and platform-specific announcement drafts.

### Changed

- Removed CSS animations and tightened spacing density across all pages.
- Route detail table stretches full width; request IDs shown in full; timestamps use relative time.
- Screenshots and GIF assets moved to `src/flowsurgeon/ui/assets/`.

### Fixed

- Breadcrumb separators inconsistent between home and route detail pages.
- Query text display in route detail view.

---

## [v0.5.1] — 2026-03-16

### Added

- **CSS design system** — token layer in `base.html` with CSS custom properties for colors, spacing, and typography.
- **Utility classes** replacing all static inline styles across templates.
- **Routes home page** — Swagger-style grouped routes list with `_group_by_prefix()` and `_relative_time` filter.
- **Route detail page** — `render_route_detail_page()` with `route_detail.html` template, dispatched from both WSGI and ASGI middlewares.
- **Security documentation** — dedicated Security section and production warning added to README.
- List view as default with method-colored row backgrounds.
- Integration tests for route detail, breadcrumb, and profile tab.

### Changed

- Home page rewritten from grid view to Swagger-style routes list with new CSS.
- Migrated to shadcn-inspired UI component patterns.

### Fixed

- Security issues in middleware request handling.
- Home page layout and rendering bugs.
- Post-checkpoint UI feedback applied (design adjustments from review).

---

## [v0.5.0] — 2026-03-09

### Added

- **Call-stack profiling** — opt-in per-request profiling using Python's stdlib `cProfile`.
  - New `Config` fields: `enable_profiling`, `profile_top_n`, `profile_user_code_only` (also `FLOWSURGEON_PROFILING=1` env var).
  - Works with both WSGI and ASGI middlewares — wraps the full request lifecycle.
  - Results stored per-request in SQLite as a JSON column (`profile_stats`) with automatic schema migration.
- **Profile tab** on the request detail page: stats table sorted by cumulative time, per-function time bars, and `<details>` callers drilldown.
- `ProfileStat` dataclass exported from the package top-level.
- Shared HTTP utilities extracted into internal `flowsurgeon._http` module (`_parse_qs_param`, `_parse_qs_int`, `_decode_body`, content-type constants, MIME map).

### Changed

- `sql_counts` in the panel renderer uses `collections.Counter` instead of a manual `dict.get` loop.
- Detail page tabs (Details, SQL, Traceback, Profile) are independently scrollable.
- Home page template restructured.

### Fixed

- `SQLAlchemyTracker` used `threading.local` for query timing, returning `0 ms` inside `asyncio.to_thread`. Replaced with `contextvars.ContextVar`.
- `AsyncSQLiteBackend.close()` race condition — sentinel-based stop could drop concurrent items. Now drains with `queue.join()`.
- Silent data loss: async writer errors swallowed with bare `pass`, now logged via `logging.exception`.
- Query-string parameters not URL-decoded. Replaced manual parser with `urllib.parse.parse_qs`.
- IPv6 zone IDs (e.g. `::1%eth0`) not stripped before `allowed_hosts` comparison — potential bypass in both middlewares.
- `_row_to_record` `KeyError` on rows from older schema versions. All accesses now use `.get(key, default)`.
- `Config(profile_top_n=-1)` silently behaved like `0`. Negative values clamped in `__post_init__`.
- `Config(db_path="some/new/dir/x.db")` crashed if parent directory missing. Now auto-created.

---

## [v0.4.1] — 2026-03-09

### Changed

- SPA layout rewrite using Alpine.js — tab switching without full-page reloads.

### Fixed

- Design polish — Nitro UI-based styling and linting cleanup.
- README corrections.

---

## [v0.4.0] — 2026-03-08

### Fixed

- **Security hardening**: `allowed_hosts` enforcement in both WSGI and ASGI middlewares, `X-Forwarded-For` ignored for access control, sensitive header redaction.

---

## [v0.3.2] — 2026-03-08

_Version bump only._

---

## [v0.3.1] — 2026-03-08

### Changed

- **UI overhaul** — redesigned debug panel with partial templates for SQL detail and traceback views.
- New template partials: `detail_sql.html`, `detail_traceback.html`.
- Updated test expectations to match new UI structure.

---

## [v0.3.0] — 2026-03-08

### Added

- **SQLAlchemy query tracker** — automatic SQL query capture via SQLAlchemy event listeners.
- **DB-API query tracker** — generic tracker for any PEP 249-compliant database driver.
- SQL query display in the debug panel UI.
- Comprehensive test suite for query tracking (`test_query_tracking.py`).

---

## [v0.2.0] — 2026-03-06

### Added

- **ASGI middleware** — `FlowSurgeonASGIMiddleware` for async frameworks (Starlette, FastAPI, etc.).
- Async SQLite storage backend.

---

## v0.1.0 — 2026-03-06

### Added

- Initial release.
- **WSGI middleware** — `FlowSurgeonWSGIMiddleware` for Flask and other WSGI apps.
- SQLite-backed request storage with automatic pruning.
- Debug panel UI served at configurable path.
- `Config` dataclass for all settings.
- Flask demo app in `examples/`.

[Unreleased]: https://github.com/vpcraft/flowsurgeon/compare/v0.5.1...HEAD
[v0.5.1]: https://github.com/vpcraft/flowsurgeon/compare/v0.5.0...v0.5.1
[v0.5.0]: https://github.com/vpcraft/flowsurgeon/compare/v0.4.1...v0.5.0
[v0.4.1]: https://github.com/vpcraft/flowsurgeon/compare/v0.4.0...v0.4.1
[v0.4.0]: https://github.com/vpcraft/flowsurgeon/compare/v0.3.2...v0.4.0
[v0.3.2]: https://github.com/vpcraft/flowsurgeon/compare/v0.3.1...v0.3.2
[v0.3.1]: https://github.com/vpcraft/flowsurgeon/compare/v0.3.0...v0.3.1
[v0.3.0]: https://github.com/vpcraft/flowsurgeon/compare/v0.2.0...v0.3.0
[v0.2.0]: https://github.com/vpcraft/flowsurgeon/compare/v0.1.0...v0.2.0
