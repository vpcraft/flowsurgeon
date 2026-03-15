---
phase: 2
slug: routes-pages
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-asyncio |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/test_asgi.py tests/test_wsgi.py -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | RHOM-01 | integration | `uv run pytest tests/test_asgi.py -k "routes_home" -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 0 | RHOM-02 | integration | `uv run pytest tests/test_asgi.py -k "route_row" -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 0 | RHOM-03 | integration | `uv run pytest tests/test_asgi.py -k "method_filter" -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 0 | RHOM-04 | integration | `uv run pytest tests/test_asgi.py -k "no_traffic" -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 0 | RHOM-05 | manual | visual inspection | N/A | ⬜ pending |
| 02-01-06 | 01 | 0 | RDET-01 | integration | `uv run pytest tests/test_asgi.py -k "route_detail" -x` | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 0 | RDET-02 | integration | `uv run pytest tests/test_asgi.py -k "route_detail_filters" -x` | ❌ W0 | ⬜ pending |
| 02-01-08 | 01 | 0 | RDET-03 | integration | `uv run pytest tests/test_asgi.py -k "breadcrumb" -x` | ❌ W0 | ⬜ pending |
| 02-01-09 | 01 | 0 | DPOL-01 | integration | `uv run pytest tests/test_asgi.py -k "detail_css" -x` | ❌ W0 | ⬜ pending |
| 02-01-10 | 01 | 0 | DPOL-02 | integration | `uv run pytest tests/test_asgi.py -k "detail_profile_tab" -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_asgi.py` — extend with routes-home and route-detail test cases (file exists, needs new test functions)
- [ ] `tests/test_wsgi.py` — same as ASGI tests but for WSGI middleware (file exists, needs new test functions)
- [ ] Test helper: `_make_route_detail_scope(method, path)` — convenience for constructing route-detail request scopes

*Core test infrastructure exists. Only new test functions needed, not new files.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No-traffic routes muted style | RHOM-04 | CSS visual styling | Inspect route rows with `has_data=false` in browser |
| RHOM-05 satisfied by design | RHOM-05 | Design decision removed requests grid | Verify route detail view shows filtered requests list |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
