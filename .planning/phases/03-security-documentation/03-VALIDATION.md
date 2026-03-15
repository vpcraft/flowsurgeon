---
phase: 3
slug: security-documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Manual review of README.md changes
- **After every plan wave:** Run `uv run pytest -x -q` (confirms underlying security code still works)
- **Before `/gsd:verify-work`:** README reviewed against all three SDOC requirements
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | SDOC-01 | manual | README review | N/A | ⬜ pending |
| 03-01-02 | 01 | 1 | SDOC-02 | manual | README review | N/A | ⬜ pending |
| 03-01-03 | 01 | 1 | SDOC-03 | manual | README review | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Documentation phase requires no new test files.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Security section in README with kill switch, allowed_hosts, redaction, .gitignore | SDOC-01 | Documentation content | Read Security section, verify all 4 subsections present with correct field names and defaults |
| `[!WARNING]` callout in Quick Start | SDOC-02 | Documentation content | Read Quick Start section, verify warning callout present after install command |
| .gitignore guidance present | SDOC-03 | Documentation content | Read Database File subsection, verify copy-paste .gitignore entry present |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Note:** This is a documentation-only phase. All requirements are manual-only verification. The existing 86-test suite covers the underlying security behaviors. No new automated tests needed.

**Approval:** pending
