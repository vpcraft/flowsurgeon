---
phase: 1
slug: css-design-system
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | 01 | 1 | UIDS-01 | visual | Manual inspection | N/A | ⬜ pending |
| TBD | 01 | 1 | UIDS-02 | visual | Manual inspection | N/A | ⬜ pending |
| TBD | 01 | 1 | UIDS-03 | visual | Manual inspection | N/A | ⬜ pending |
| TBD | 01 | 1 | UIDS-04 | visual | Manual inspection | N/A | ⬜ pending |
| TBD | 01 | 1 | UIDS-05 | grep | `grep -rn 'style=' src/flowsurgeon/ui/templates/ \| grep -v 'width:{{ pct }}'` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

CSS-only changes do not require new test infrastructure. UIDS-05 (no inline styles) can be verified via grep. Visual requirements (UIDS-01 through UIDS-04) are verified by manual inspection.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CSS custom properties used for all colors/spacing | UIDS-01 | Visual/structural — no runtime behavior to test | Grep for hardcoded hex values in templates; inspect `:root {}` block |
| Method badges show correct colors | UIDS-02 | Visual — color correctness is subjective | Run example app, visit /flowsurgeon, verify badge colors |
| Borders instead of shadows | UIDS-03 | Visual | Inspect cards/containers in browser |
| Muted/bright typography hierarchy | UIDS-04 | Visual | Compare labels vs values in detail view |
| No inline style attributes | UIDS-05 | Automated grep possible | `grep -rn 'style=' src/flowsurgeon/ui/templates/` should return only dynamic width |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
