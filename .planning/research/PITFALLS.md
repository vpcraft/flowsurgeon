# Pitfalls Research

**Domain:** Python debug middleware public launch
**Researched:** 2026-03-15
**Scope:** What commonly goes wrong when launching open-source Python dev tools. Critical mistakes in UI, docs, CI/CD, packaging, and community engagement.

---

## Security Pitfalls

### PITFALL-1: Response Body Capture Enabled by Default

**Risk:** Response bodies may contain sensitive data (auth tokens, PII). Storing them in an unencrypted SQLite file is a data leak if the db file is committed or shared.

**Warning signs:** No opt-out for body capture; db file in git; no mention in docs.

**Prevention:**
- Document the security implications of response body capture
- Ensure `flowsurgeon.db` is in `.gitignore` examples
- Consider adding `capture_response_body` config option (default True for dev, but documented)

**Phase:** Documentation

### PITFALL-2: SQLite Database File Permissions

**Risk:** The `flowsurgeon.db` file is created with default permissions. On shared dev machines, other users could read captured request data.

**Warning signs:** No mention of file permissions in docs or config.

**Prevention:**
- Document that the db file contains request/response data
- Add `.gitignore` recommendation to docs
- Consider `os.umask` or explicit file permissions on creation

**Phase:** Documentation

---

## UI Launch Pitfalls

### PITFALL-3: Screenshot Gap

**Risk:** Announcing on Reddit/X without compelling screenshots means the post gets scrolled past. Debug tools are visual — the UI IS the pitch.

**Warning signs:** README screenshots are outdated or missing; UI doesn't look professional in dark mode.

**Prevention:**
- Take fresh screenshots after UI redesign
- Include both the routes list AND a detail view screenshot
- Use a real-looking app with realistic data, not "Hello World"

**Phase:** UI Redesign (must complete before announcement)

### PITFALL-4: CDN Dependency in Self-Contained Tool

**Risk:** Loading fonts or scripts from external CDNs means the debug UI breaks in air-gapped/corporate environments.

**Warning signs:** `<link>` to fonts.googleapis.com or CDN scripts in templates.

**Prevention:**
- Use system font stack only
- Bundle all JS (Alpine.js already bundled)
- No external network requests from the debug UI

**Phase:** UI Redesign

---

## Packaging Pitfalls

### PITFALL-5: Python Version Floor Too High

**Risk:** Python 3.12+ excludes users on 3.10/3.11 (still widely used in 2025). First impression on Reddit: "can't even install it."

**Warning signs:** Comments on announcement saying "doesn't work with my Python version."

**Prevention:**
- Consider lowering to 3.10+ if no 3.12-specific features are actually used
- If 3.12+ is intentional, document WHY in docs (which 3.12 features are used)
- At minimum, document the requirement prominently

**Phase:** CI/CD & Packaging

### PITFALL-6: Missing py.typed Marker

**Risk:** Type-checking users (mypy, pyright) get "missing stubs" warnings when importing FlowSurgeon.

**Warning signs:** No `py.typed` file in the package root.

**Prevention:**
- Verify `py.typed` exists and is included in the built package
- Test with `mypy` that imports resolve cleanly

**Phase:** CI/CD & Packaging

---

## Documentation Pitfalls

### PITFALL-7: No Security Section in Docs

**Risk:** Users deploy to staging/production without understanding that FlowSurgeon exposes request internals. Gets flagged in security reviews.

**Warning signs:** No "Security" page in docs; no warnings about production use.

**Prevention:**
- Add a dedicated Security page covering: allowed_hosts, header redaction, env var kill switch, response body implications
- Add a warning banner to the Quick Start: "FlowSurgeon is a development tool. Do not enable in production."

**Phase:** Documentation

### PITFALL-8: No .gitignore Guidance for DB File

**Risk:** Users accidentally commit `flowsurgeon.db` with captured request data to version control.

**Warning signs:** No mention of gitignore in installation docs.

**Prevention:**
- Add `.gitignore` recommendation to Quick Start
- Consider auto-creating `.gitignore` entry or warning when db is in a git-tracked directory

**Phase:** Documentation

---

## CI/CD Pitfalls

### PITFALL-9: False-Green CI (Tests Pass but Quality Unchecked)

**Risk:** CI only runs tests, not linting or formatting. Code quality drifts. PRs merge with style issues.

**Warning signs:** CI badge is green but code has inconsistent formatting.

**Prevention:**
- Add `ruff check` and `ruff format --check` to CI pipeline
- Add coverage reporting to catch untested code paths

**Phase:** CI/CD

### PITFALL-10: No Integration Tests with Real Frameworks

**Risk:** Unit tests pass but FlowSurgeon breaks with actual Flask/FastAPI apps due to middleware ordering or response handling edge cases.

**Warning signs:** Tests only use mock WSGI/ASGI apps, not real framework instances.

**Prevention:**
- Ensure integration tests exist for both Flask and FastAPI
- Test with the example apps in `examples/`

**Phase:** CI/CD

---

## Community Engagement Pitfalls

### PITFALL-11: Announcement Framing as "Another Debug Toolbar"

**Risk:** Reddit/HN dismisses FlowSurgeon as "just another django-debug-toolbar clone." The differentiation (framework-agnostic, ASGI support, cProfile integration) gets lost.

**Warning signs:** Title doesn't mention what's unique; comments ask "how is this different from X?"

**Prevention:**
- Lead with the unique angle: "Framework-agnostic profiling for Flask AND FastAPI"
- Prepare a comparison table: FlowSurgeon vs django-debug-toolbar vs Flask-DebugToolbar vs Sentry
- Have the comparison ready in docs, link to it from the announcement

**Phase:** Pre-announcement preparation

### PITFALL-12: Announcing Without a Demo or GIF

**Risk:** Text-only announcement on Reddit gets minimal engagement. Dev tools need visual proof.

**Warning signs:** No GIF/video showing the tool in action.

**Prevention:**
- Record a short GIF or video (30-60 seconds) showing: install, wrap app, browse debug UI
- Use a tool like `vhs` or screen recording
- Host on GitHub (in README) so it loads inline on Reddit

**Phase:** Pre-announcement preparation

### PITFALL-13: No "Getting Started in 30 Seconds" Path

**Risk:** Interested developers bounce because setup seems complex.

**Warning signs:** Quick Start requires more than 3 steps; no copy-pasteable example.

**Prevention:**
- Ensure Quick Start is: `pip install flowsurgeon`, wrap app (2 lines), run, visit URL
- The current README Quick Start is already good — preserve this clarity in docs site

**Phase:** Documentation

---

## Summary: Phase Mapping

| Pitfall | Phase |
|---------|-------|
| PITFALL-3: Screenshot gap | UI Redesign |
| PITFALL-4: CDN dependency | UI Redesign |
| PITFALL-1: Response body default | Documentation |
| PITFALL-2: SQLite permissions | Documentation |
| PITFALL-7: No security section | Documentation |
| PITFALL-8: No gitignore guidance | Documentation |
| PITFALL-13: Getting started path | Documentation |
| PITFALL-5: Python version floor | CI/CD & Packaging |
| PITFALL-6: py.typed marker | CI/CD & Packaging |
| PITFALL-9: False-green CI | CI/CD & Packaging |
| PITFALL-10: No integration tests | CI/CD & Packaging |
| PITFALL-11: Announcement framing | Pre-announcement |
| PITFALL-12: No demo GIF | Pre-announcement |

---

*Research date: 2026-03-15*
