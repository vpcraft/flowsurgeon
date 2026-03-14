# Changelog

## v0.5.0 — 2026-03-09

### Added

**Call-stack profiling** — opt-in per-request profiling using Python's stdlib `cProfile`.

- New `Config` fields:
  - `enable_profiling: bool = False` — master switch (also `FLOWSURGEON_PROFILING=1` env var)
  - `profile_top_n: int = 50` — number of functions to keep, ranked by cumulative time
  - `profile_user_code_only: bool = True` — filter out stdlib and third-party frames
- Works with both WSGI and ASGI middlewares. Profiling wraps the full request, so CPU hotspots in your own code are captured accurately. I/O wait is accounted for as event-loop time in async apps — expected behaviour.
- Results are stored per-request in SQLite as a JSON column (`profile_stats`). Existing databases upgrade automatically via schema migration.
- New **Profile tab** on the request detail page: stats table sorted by cumulative time, per-function time bars, and a native `<details>` callers drilldown showing the top-3 call sites.
- New `ProfileStat` dataclass exported from the package top-level.

### Fixed

- `SQLAlchemyTracker` used `threading.local` for query timing, which returned `0 ms` for any query executed inside an `asyncio.to_thread` call. Replaced with a per-instance `contextvars.ContextVar` — timing is now correct in async apps.
- `AsyncSQLiteBackend.close()` used a sentinel (`None`) to stop the writer task, which had a narrow race where items enqueued concurrently could be dropped. Now drains the queue with `queue.join()` before cancelling the task.
- Silent data loss: storage write errors in the async writer were swallowed with a bare `pass`. They are now logged via `logging.exception`.
- Query-string parameters (`?q=`, `?page=`, etc.) were not URL-decoded. Replaced the manual parser with `urllib.parse.parse_qs`.
- IPv6 zone IDs (e.g. `::1%eth0`) were not stripped before comparing against `allowed_hosts`, allowing a potential bypass. Both WSGI and ASGI middlewares now strip zone IDs.
- `_row_to_record` used bare `dict["key"]` access for `ProfileStat` fields deserialized from SQLite, causing `KeyError` when reading rows written by older versions of the library. All accesses now use `.get(key, default)`.
- `Config(profile_top_n=-1)` silently behaved identically to `0`. Negative values are now clamped to `0` in `__post_init__`.
- `Config(db_path="some/new/dir/x.db")` crashed with an opaque `OperationalError` if the parent directory did not exist. The directory is now created automatically.

### Changed

- Shared HTTP utilities (`_parse_qs_param`, `_parse_qs_int`, `_decode_body`, content-type constants, MIME map) extracted from both middlewares into a single internal `flowsurgeon._http` module. No public API change.
- `sql_counts` in the panel renderer now uses `collections.Counter` instead of a manual `dict.get` loop.
- Detail page tabs (Details, SQL, Traceback, Profile) are all independently scrollable — long content no longer overflows the viewport.

---

## v0.4.1

- Design polish and README fixes.

## v0.4.0

- SPA layout rewrite using Alpine.js — tab switching without full-page reloads.
- Request grid view on the home page.
- Security hardening: `allowed_hosts` enforcement, `X-Forwarded-For` ignored, sensitive header redaction.
