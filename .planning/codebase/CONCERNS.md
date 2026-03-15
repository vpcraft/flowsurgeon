# Codebase Concerns

**Analysis Date:** 2026-03-14

## Tech Debt

**Bare Exception Handling:**
- Issue: Multiple catch-all `except Exception:` blocks swallow errors without context, potentially masking unexpected failure modes.
- Files: `src/flowsurgeon/middleware/asgi.py` (line 94), `src/flowsurgeon/middleware/wsgi.py` (line 133), `src/flowsurgeon/ui/panel.py` (line 155), `src/flowsurgeon/profiling.py` (line 94)
- Impact: Silent failures in route discovery, asset loading, and profile parsing make debugging difficult; errors are only logged, not raised.
- Fix approach: Log specific exception types, optionally re-raise or provide fallback behavior. Consider separate handlers for expected vs unexpected errors.

**Broad Type Annotations with `Any`:**
- Issue: Heavy use of `Any` type in tracker proxies (`_TrackedConnection`, `_InstrumentedCursor`) and route discovery reduces type safety.
- Files: `src/flowsurgeon/trackers/dbapi.py` (lines 48-78, 73-74, 126-130), `src/flowsurgeon/ui/panel.py` (lines 131-169)
- Impact: IDEs and type checkers cannot catch attribute access errors; potential runtime AttributeErrors when working with unexpected object shapes.
- Fix approach: Use `Protocol` types or `Generic` to constrain `Any` usage. Document expected interfaces clearly.

**JSON Deserialization Without Schema Validation:**
- Issue: `_row_to_record()` in `src/flowsurgeon/storage/sqlite.py` (lines 174-215) deserializes JSON with `.get()` fallbacks but no schema validation.
- Files: `src/flowsurgeon/storage/sqlite.py` (lines 188-200)
- Impact: Malformed or missing fields silently produce default values; data corruption or inconsistent state could go unnoticed if database is manually edited.
- Fix approach: Use Pydantic or similar schema validation on deserialization; add warnings for missing or unexpected fields.

**Thread-Local Storage Without Cleanup on Error:**
- Issue: `SQLiteBackend._local` (line 48 in `src/flowsurgeon/storage/sqlite.py`) stores per-thread connections but has no guaranteed cleanup if an exception occurs during query execution.
- Files: `src/flowsurgeon/storage/sqlite.py` (lines 46-76)
- Impact: Long-running threads could accumulate unclosed SQLite connections if errors occur mid-transaction; eventual resource leak.
- Fix approach: Implement context managers or try-finally blocks around database operations; add periodic cleanup of stale connections.

**Duplicate Exception Handling in WSGI/ASGI:**
- Issue: Nearly identical exception handling logic appears in both middleware implementations without shared extraction.
- Files: `src/flowsurgeon/middleware/wsgi.py` (lines 133, 155, 182), `src/flowsurgeon/middleware/asgi.py` (lines 94, 168, 180)
- Impact: Bug fixes or improvements must be applied in two places; inconsistent behavior between WSGI and ASGI.
- Fix approach: Extract common error handling to a shared utility module; reuse across both middleware classes.

## Known Bugs

**Race Condition in AsyncSQLiteBackend Start:**
- Symptoms: `_task` can transition from `None` to `done()` concurrently; `_ensure_started()` may create multiple writer tasks if called simultaneously.
- Files: `src/flowsurgeon/storage/async_sqlite.py` (lines 30-34, 72-74)
- Trigger: Enqueue requests during ASGI app startup when event loop is in flux; rapidly switching between startup and shutdown.
- Workaround: Serialize calls to `.enqueue()` after app startup, or ensure only one coroutine calls `_ensure_started()` at a time.

**`check_same_thread=False` SQLite Vulnerability:**
- Symptoms: Thread-safety is asserted but not actually enforced; SQLite writes can interleave if multiple threads execute outside middleware serialization.
- Files: `src/flowsurgeon/storage/sqlite.py` (line 67)
- Trigger: If user code directly accesses the backend's `_conn` or stores a reference to it across threads.
- Workaround: Document that `_conn` is internal and must not be accessed outside the owning thread. Consider using a connection pool or mutex.

**Panel Injection Overwrites All `</body>` Tags:**
- Symptoms: If response contains multiple `</body>` tags (uncommon but possible in malformed HTML or XML), only the first is replaced.
- Files: `src/flowsurgeon/middleware/asgi.py` (line 369), `src/flowsurgeon/middleware/wsgi.py` (line 327)
- Trigger: Responses with multiple closing body tags; edge case with legacy or non-conformant HTML.
- Workaround: Only affects debug UI injection; malformed HTML is already broken, so impact is minimal.

**Missing `content-length` Header Reset After Profile Parsing Failure:**
- Symptoms: If `_parse_profile()` raises an exception not caught in the `try` block, profile_stats is never set but request continues normally.
- Files: `src/flowsurgeon/middleware/asgi.py` (lines 317-328), `src/flowsurgeon/middleware/wsgi.py` (lines 237-302)
- Trigger: cProfile produces corrupted output or pstats.Stats parsing fails unexpectedly.
- Workaround: Profiling is opt-in (disabled by default); users can disable if issues occur.

## Security Considerations

**Response Body Captured by Default:**
- Risk: Sensitive data (API tokens, passwords, PII) in JSON/HTML responses is stored in plaintext SQLite database if `capture_response_body=True`.
- Files: `src/flowsurgeon/core/config.py` (line 52), `src/flowsurgeon/middleware/asgi.py` (lines 355-358), `src/flowsurgeon/middleware/wsgi.py` (lines 311-314)
- Current mitigation: Configuration flag `capture_response_body` defaults to `True` with explicit opt-out required; docs should warn users.
- Recommendations: Change default to `False`; add a redaction filter for common sensitive patterns (authorization headers, API keys); implement automatic trimming of response bodies to max size.

**Debug Panel Accessible to All Allowed Hosts:**
- Risk: If `allowed_hosts` includes a misconfigured IP/hostname, attackers can access request history including SQL queries and response bodies.
- Files: `src/flowsurgeon/core/config.py` (line 31), `src/flowsurgeon/middleware/asgi.py` (lines 98-100), `src/flowsurgeon/middleware/wsgi.py` (lines 94-96)
- Current mitigation: Defaults to localhost only; requires explicit configuration to broaden.
- Recommendations: Implement token-based authentication for debug panel; add rate limiting; log all accesses to the panel; consider environment-based toggle (e.g., only in development).

**No CSRF Protection on Debug Panel:**
- Risk: Debug panel has no CSRF tokens; if a user visits a malicious site while accessing their local debug panel, the site could trigger debug page requests.
- Files: `src/flowsurgeon/middleware/asgi.py` (lines 113-120), `src/flowsurgeon/middleware/wsgi.py` (lines 108-112)
- Current mitigation: Mitigated in practice since localhost access is hard to exploit; affects only development environments.
- Recommendations: Add simple CSRF token validation to detail/history endpoints if expanded for production use.

**SQLite Database File Permissions:**
- Risk: Database file created with default umask; other users on the system could read it if umask is permissive (contains full request/response history).
- Files: `src/flowsurgeon/core/config.py` (lines 60-61)
- Current mitigation: Typically stored in dev environments where this is acceptable; no explicit permission setting.
- Recommendations: Add `mode=0o600` when creating database file; warn users if file permissions are too open; provide option to store in-memory for testing.

**X-Forwarded-For Correctly Rejected:**
- Status: GOOD - Code correctly uses REMOTE_ADDR (ASGI `client`) instead of X-Forwarded-For, preventing IP spoofing.
- Files: `src/flowsurgeon/middleware/asgi.py` (lines 398-402), `src/flowsurgeon/middleware/wsgi.py` (lines 349-353)

## Performance Bottlenecks

**ASGI Panel Injection Rewrites Entire Response Body:**
- Problem: Response body is fully buffered and re-sent after HTML parsing (line 353 in `asgi.py`); large responses cause memory bloat.
- Files: `src/flowsurgeon/middleware/asgi.py` (lines 352-371)
- Cause: Panel HTML is injected before forwarding; requires reading entire body into memory.
- Improvement path: Stream response chunks and inject panel only on the final chunk; or delay injection to a separate phase. Currently marked as "text response: buffered" but no size check before buffering.

**Full Request Records Kept in Memory During Response Buffering:**
- Problem: Entire `RequestRecord` object stays in memory for text responses until response completes; if response is very large or slow, memory usage can spike.
- Files: `src/flowsurgeon/middleware/asgi.py` (lines 285-371), `src/flowsurgeon/middleware/wsgi.py` (lines 219-334)
- Cause: Record is populated incrementally but not flushed to storage until response completes.
- Improvement path: For large responses, stream to storage incrementally; use a ring buffer or temporary file instead of in-memory list.

**No Maximum Size Enforcement on Response Body Storage:**
- Problem: Responses up to 128 KB are stored (line 13 in `_http.py`), but this limit is only applied when decoding, not when checking if should buffer.
- Files: `src/flowsurgeon/_http.py` (line 13), `src/flowsurgeon/middleware/asgi.py` (lines 353, 360), `src/flowsurgeon/middleware/wsgi.py` (lines 304, 312)
- Cause: No check before buffering; a 128+ KB text response is still buffered fully before truncation.
- Improvement path: Check body size before deciding to buffer; implement streaming response capture.

**Profiling Overhead Not Documented:**
- Problem: Profiling adds 1-10% overhead (noted in code comment at line 44-45 in `config.py`), but no guidance on production impact or tuning.
- Files: `src/flowsurgeon/core/config.py` (line 44), `src/flowsurgeon/middleware/asgi.py` (lines 318-320), `src/flowsurgeon/middleware/wsgi.py` (lines 238-240)
- Cause: cProfile captures every function call, even when `profile_user_code_only=True` filters stdlib.
- Improvement path: Provide sampling-based profiling option; document memory overhead for `profile_top_n`; add metrics endpoint.

**Database Pruning Happens on Every Write:**
- Problem: `prune()` query executes after every request (line 165 in `sqlite.py`), even if database is far from the limit.
- Files: `src/flowsurgeon/storage/sqlite.py` (lines 153-165), `src/flowsurgeon/middleware/asgi.py` (line 349), `src/flowsurgeon/middleware/wsgi.py` (line 317)
- Cause: No batching; every single request triggers a DELETE subquery.
- Improvement path: Defer pruning; prune only when record count exceeds threshold; batch multiple pruning operations.

**Route Discovery Runs on Every Middleware Instantiation:**
- Problem: `discover_routes()` iterates through all app routes repeatedly during middleware init (line 72 in both middlewares); wasteful if middleware is recreated.
- Files: `src/flowsurgeon/middleware/asgi.py` (line 72), `src/flowsurgeon/middleware/wsgi.py` (line 72), `src/flowsurgeon/ui/panel.py` (lines 131-169)
- Cause: No caching; full traversal happens every time.
- Improvement path: Cache routes on the app object or in a global dict; only refresh on app reload.

## Fragile Areas

**Route Discovery via Reflection:**
- Files: `src/flowsurgeon/ui/panel.py` (lines 131-169)
- Why fragile: Assumes specific attributes (`routes`, `url_map`, `__self__`, `app`, `application`) exist and have expected structure. Different framework versions or custom ASGI apps may have different shapes. Fallback to checking `__self__`, `app`, `application` recursively could infinite-loop if an object has circular references.
- Safe modification: Add explicit list of supported framework versions; test against major versions (Flask 2.x, FastAPI 0.9x, Starlette 0.2x); document unsupported frameworks; add recursion depth limit in `discover_routes()`.
- Test coverage: No unit tests for route discovery across different frameworks visible in repo; test with Flask, FastAPI, Starlette, and custom ASGI apps.

**WSGI/ASGI Response Header Parsing:**
- Files: `src/flowsurgeon/middleware/wsgi.py` (lines 369-374), `src/flowsurgeon/middleware/asgi.py` (lines 414-419)
- Why fragile: Headers are lowercased for comparison; case-sensitivity variations in custom frameworks could cause mismatches. Header value parsing assumes Latin-1 encoding; non-standard encodings will decode incorrectly.
- Safe modification: Use HTTP header name constants; validate header encoding before decoding; test with non-ASCII header values.
- Test coverage: Only basic header tests; no tests for unusual but valid encodings (e.g., RFC 8187 encoded-word parameters).

**Profiling Depends on cProfile Output Format Stability:**
- Files: `src/flowsurgeon/profiling.py` (lines 70-138)
- Why fragile: Code relies on `pstats.Stats.stats` dict structure `{(filename, lineno, funcname): (prim_calls, calls, tt, ct, callers)}`. If cProfile internals change in future Python versions, parsing breaks. Currently assumes callers is a dict; could be `None`.
- Safe modification: Add schema validation of `pstats.Stats.stats` output; version-gate on Python version if needed; add fallback for unknown structures.
- Test coverage: No tests for different Python versions (3.9, 3.10, 3.11, 3.12); behavior may differ.

**SQLite Schema Migrations Use Try-Except for Column Existence Check:**
- Files: `src/flowsurgeon/storage/sqlite.py` (lines 54-58)
- Why fragile: Catches all `OperationalError` indiscriminately; fails silently if error is due to lock, permission, or syntax issue, not column existence.
- Safe modification: Check `PRAGMA table_info()` to verify column existence explicitly instead of relying on exception.
- Test coverage: No tests for concurrent initialization; concurrent access to DB during migration could corrupt state.

**Panel Injection Assumes `</body>` Exists in HTML:**
- Files: `src/flowsurgeon/middleware/asgi.py` (lines 368-371), `src/flowsurgeon/middleware/wsgi.py` (lines 326-329)
- Why fragile: If `</body>` is not found, panel is appended at end; works but silhouette is wrong if HTML is malformed. No validation that replacement actually occurred.
- Safe modification: Log a warning if `</body>` is not found; validate that panel was inserted correctly; consider HTML parser library if accuracy is critical.
- Test coverage: Only happy path (valid HTML with body tag) tested; no tests for edge cases (no body tag, multiple bodies, XHTML, XML).

## Scaling Limits

**SQLite Single-File Bottleneck:**
- Current capacity: ~10,000 requests in default storage (line 33 in `config.py`, `max_stored_requests=1000` is default but typically increased).
- Limit: SQLite write throughput under high concurrency (~1,000 writes/sec on typical SSD); WAL mode helps but still serialized by single writer thread.
- Scaling path: Implement pluggable storage backend (already has `StorageBackend` interface); add PostgreSQL, MySQL, or in-memory backends. Consider ring buffer for ultra-high throughput scenarios.

**Memory Bloat with Large Request Bodies:**
- Current capacity: Response bodies up to 128 KB stored in memory; with 1,000 records and average 50 KB bodies, ~50 MB memory per process.
- Limit: If `capture_response_body=True` and many large responses, memory usage becomes significant; no eviction policy except by request count.
- Scaling path: Implement LRU cache or memory-bounded storage; store bodies on disk or in separate blob storage; compress stored bodies.

**Profiling Top-N Hardcoded to 50 Functions:**
- Current capacity: `profile_top_n=50` (line 48 in `config.py`) is fixed; UI shows top 50 regardless of actual hotspots.
- Limit: For large applications with many hot functions, top 50 misses important functions; for small apps, 50 is excessive.
- Scaling path: Make top-N dynamic based on cProfile output size; provide UI sliders to filter by threshold instead of fixed count.

**String Repr of Query Parameters Unbounded:**
- Current capacity: Line 116 in `trackers/dbapi.py` uses `repr(parameters)` which can be very large for bulk inserts.
- Limit: Very large parameter lists (e.g., batch INSERT with 10,000 rows) create huge strings stored in database; no truncation.
- Scaling path: Truncate parameter repr to max 1,000 chars; detect bulk operations and summarize instead of storing full params.

## Dependencies at Risk

**SQLAlchemy Import Optional but Not Clearly Documented:**
- Risk: `src/flowsurgeon/trackers/sqlalchemy.py` imports SQLAlchemy conditionally; if user tries to use `SQLAlchemyTracker` without installing, error is raised at tracker instantiation time (line 58).
- Impact: Harder to debug; user might not realize SQLAlchemy is required for that tracker.
- Migration plan: Add SQLAlchemy as an optional dependency (`pip install flowsurgeon[sqlalchemy]`); improve error message to suggest installation command.

**Jinja2 Dependency for UI:**
- Risk: `src/flowsurgeon/ui/panel.py` imports Jinja2 unconditionally (line 10); if UI is not used (e.g., headless API mode), Jinja2 is still required.
- Impact: Larger dependency tree; bloats minimal deployments that only track queries.
- Migration plan: Make UI optional; lazy-import Jinja2 on first use; provide alternative rendering backend (e.g., string formatting).

## Missing Critical Features

**No Request Filtering by Response Status:**
- Problem: Debug panel shows all requests; no easy way to focus on errors or slow requests.
- Blocks: Quick debugging of production issues; must manually scan through history.
- Impact: Medium - workaround is manual filtering; nice-to-have feature.

**No Automatic Query Explanation or Index Suggestions:**
- Problem: Slow queries are highlighted but not analyzed; no EXPLAIN output or hints.
- Blocks: Users must manually run EXPLAIN outside FlowSurgeon.
- Impact: Medium - reduces value of query profiling; requires integration with specific databases.

**No Middleware Stack Tracing:**
- Problem: If multiple middlewares are chained, FlowSurgeon doesn't show which middleware modified the response.
- Blocks: Debugging middleware interactions; useful for complex setups.
- Impact: Low - edge case; mostly useful for framework debugging.

## Test Coverage Gaps

**No Async Concurrency Tests:**
- What's not tested: Multiple concurrent requests in ASGI mode; queue flushing under load; race conditions in async writer.
- Files: `src/flowsurgeon/storage/async_sqlite.py` (lines 30-87), `src/flowsurgeon/middleware/asgi.py` (lines 265-384)
- Risk: Async startup race conditions, writer task crashes, lost writes during high throughput.
- Priority: HIGH - concurrency is core to ASGI usage.

**No Integration Tests with Real Frameworks:**
- What's not tested: FlowSurgeon actually integrated into Flask, FastAPI, or Starlette apps; route discovery accuracy.
- Files: `src/flowsurgeon/ui/panel.py` (lines 131-169)
- Risk: Route discovery fails silently; middleware doesn't work with specific framework versions.
- Priority: HIGH - integration is the main use case.

**No Performance Regression Tests:**
- What's not tested: Overhead of middleware itself; memory leaks under sustained load; profiling accuracy.
- Files: `src/flowsurgeon/middleware/asgi.py`, `src/flowsurgeon/middleware/wsgi.py`
- Risk: Silent slowdowns; memory leaks accumulate over time.
- Priority: MEDIUM - important for production use but harder to automate.

**No Error Injection Tests:**
- What's not tested: Behavior when database is locked, query tracker fails, asset loading fails, profile parsing throws.
- Files: `src/flowsurgeon/storage/sqlite.py`, `src/flowsurgeon/profiling.py`, `src/flowsurgeon/ui/panel.py`
- Risk: Unhandled exceptions leak through to user app; requests fail silently.
- Priority: MEDIUM - robustness is important but currently assumed to work.

**No Binary/Large Response Tests:**
- What's not tested: Streaming binary responses, very large text responses, responses without body.
- Files: `src/flowsurgeon/middleware/asgi.py`, `src/flowsurgeon/middleware/wsgi.py`
- Risk: Memory bloat, response corruption, panel injection on wrong content types.
- Priority: MEDIUM - edge case but impacts real applications.

---

*Concerns audit: 2026-03-14*
