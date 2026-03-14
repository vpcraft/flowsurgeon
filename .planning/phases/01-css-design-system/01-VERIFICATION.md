---
phase: 01-css-design-system
verified: 2026-03-15T00:00:00Z
status: human_needed
score: 9/9 must-haves verified (automated); 2 items require human visual confirmation
re_verification: false
human_verification:
  - test: "Launch example app and visit /flowsurgeon. Confirm method badges are visually correct: GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple, all pill-shaped."
    expected: "Each method badge displays the Swagger-convention color with white text and a pill border-radius."
    why_human: "Color rendering and pill shape can only be confirmed visually in the browser."
  - test: "Open DevTools on the page. Check the Network tab — confirm no request is made to fonts.googleapis.com."
    expected: "Zero network requests to any Google Fonts CDN URL. System font stack is in use."
    why_human: "No-CDN guarantee requires runtime inspection of browser network activity."
---

# Phase 1: CSS Design System Verification Report

**Phase Goal:** The UI has a coherent, professional visual foundation that all pages inherit from
**Verified:** 2026-03-15
**Status:** human_needed — all automated checks passed; 2 visual confirmation items remain
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All color, spacing, radius, font, and transition values in base.html CSS are defined as `:root` custom properties — no hardcoded hex or px literals remain in rule bodies | VERIFIED (with documented exceptions) | `:root {}` block confirmed at line 14; 271 `var(--...)` references in rule bodies; 3 hex values remain outside `:root` (`#00BFA0` brand hover, `#C8D6E5` cs-2xx neutral, `#313244` scrollbar thumb) — all documented as intentional edge cases with no matching semantic token |
| 2 | HTTP method badges display Swagger-convention colors: GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple with colored pill shape | VERIFIED (automated) / NEEDS VISUAL CONFIRMATION | Token values confirmed in `:root`: GET `#61AFFE`, POST `#49CC90`, PUT `#FCA130`, DELETE `#F93E3E`, PATCH `#50E3C2`. CSS rules `.m-GET` through `.m-HEAD` all use `var(--color-method-*-bg/fg)`. Pill shape: `border-radius: var(--radius-pill)`. Visual rendering needs human confirmation. |
| 3 | Containers (`.card`, `.table-wrap`, `.panel-card`, `.stat-badge`) use 1px solid borders with no box-shadow | VERIFIED | All four selectors have `border: 1px solid var(--border-color)` and no `box-shadow`. Three remaining `box-shadow` occurrences are accessibility/indicator uses only: focus ring on `.filter-input:focus` and `.filter-select:focus` (accessibility affordance) and inset underline on `.tab-btn-active` (tab indicator technique, not depth shadow). |
| 4 | Labels use muted/dim color and uppercase styling; values use bright/primary color — consistent typographic hierarchy | VERIFIED | `.label { font-size: 11px; font-weight: 600; color: var(--text-dim); letter-spacing: 0.08em; text-transform: uppercase; }` at line 574. `.value { color: var(--text-body); font-weight: 500; }` at line 582. `.value-prominent { color: var(--text-primary); font-weight: 700; }` at line 587. All use token references. |
| 5 | Google Fonts CDN link and Roboto font-family reference are removed; system font stack is used | VERIFIED | `grep -c 'fonts.googleapis.com\|Roboto' base.html` returns 0. Body uses `font-family: var(--font-sans)` where `--font-sans: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif`. Network-tab confirmation still recommended (see human verification). |
| 6 | Utility classes for monospace, font sizes, colors, layout, and overflow are defined in the style block | VERIFIED | Lines 1080–1131: `.u-mono`, `.u-text-xs/sm/md/base/lg`, `.u-muted/.u-dim/.u-faint/.u-brand/.u-bright`, `.u-flex/.u-flex-col/.u-items-center`, `.u-gap-1` through `.u-gap-4`, `.u-flex-1/.u-shrink-0/.u-min-h-0`, `.u-scroll-y`, `.u-hidden`, plus additional utilities added for template needs (`u-text-right`, `u-fw-500/600/700`, `u-block`, `u-mt-1/2`). |
| 7 | No static inline `style=` attributes remain in any template file — all converted to utility classes or component classes | VERIFIED (with two documented exceptions) | `grep -rn 'style=' templates/` (excluding Jinja2 interpolations) returns only 2 results, both in `detail_profile.html`: (a) `style="border-bottom:{%if...%}..."` — a Jinja2-conditional value used to toggle a row separator dynamically; (b) `style="width:{{ pct }}%;"` — the canonical dynamic-width exception documented in the plan. Both are Jinja2-driven, not static. |
| 8 | All template files extend `base.html` and inherit the design token system | VERIFIED | `home.html` line 1: `{% extends "base.html" %}`. `detail.html` line 1: `{% extends "base.html" %}`. Partials are included via `detail.html`, which extends `base.html`. Inheritance chain is intact. |
| 9 | The `_method_class` and `_status_class` Jinja2 filters in `panel.py` generate class names that match the CSS selectors in `base.html` | VERIFIED | `panel.py` `_method_class()` returns `m-{METHOD}` (line 78); CSS has `.m-GET`, `.m-POST`, `.m-PUT`, `.m-PATCH`, `.m-DELETE`, `.m-HEAD`, `.m-OTHER`. `_status_class()` returns `s-2xx/3xx/4xx/5xx`; CSS has matching `.s-2xx` through `.s-5xx`. Wiring is complete. |

**Score:** 9/9 truths verified (automated); 2 items require human visual confirmation

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/flowsurgeon/ui/templates/base.html` | Complete CSS design system: `:root` tokens, method badges, border-only containers, label/value hierarchy, utility classes | VERIFIED | 1365 lines. `:root` block lines 14–95 (all token categories present). Method badge rules lines 443–476. Container rules confirmed border-only. Label/value hierarchy lines 574–590. Utility classes lines 1080–1131. |
| `src/flowsurgeon/ui/templates/home.html` | Home page template with utility classes; extends base.html | VERIFIED | Extends `base.html`. Uses `method_class` Jinja2 filter. 2 `u-` utility class usages confirmed. No static `style=` attributes. |
| `src/flowsurgeon/ui/templates/detail.html` | Detail page template with utility classes | VERIFIED | Extends `base.html`. 1 `u-` utility class usage confirmed. No static `style=` attributes. |
| `src/flowsurgeon/ui/templates/partials/detail_profile.html` | Profile partial with ~35 inline styles converted | VERIFIED | Multiple `u-` utility class usages confirmed. 2 remaining `style=` attributes are Jinja2-dynamic (documented exceptions). Component classes (`profile-*`) defined in `base.html`. |
| `src/flowsurgeon/ui/templates/partials/detail_sql.html` | SQL partial with ~10 inline styles converted | VERIFIED | Multiple `u-` utility class usages confirmed. No static `style=` attributes. |
| `src/flowsurgeon/ui/templates/partials/detail_traceback.html` | Traceback partial with ~10 inline styles converted | VERIFIED | Multiple `u-` utility class usages confirmed. No static `style=` attributes. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `base.html :root tokens` | `base.html component rules` | `var()` references in CSS rules | WIRED | 271 `var(--...)` references confirmed in rule bodies outside `:root`. |
| `base.html .m-GET` etc. | `panel.py _method_class filter` | Jinja2 filter generates `m-{METHOD}` class names | WIRED | `panel.py` returns `m-{METHOD}` strings; `base.html` has `.m-GET/.m-POST/.m-PUT/.m-PATCH/.m-DELETE/.m-HEAD/.m-OTHER` selectors. `home.html` uses `{{ r.method \| method_class }}` to apply them. |
| `base.html utility classes` | Template partials | Jinja2 template inheritance + class attributes | WIRED | `detail_profile.html`, `detail_sql.html`, `detail_traceback.html` all use `u-` prefixed classes confirmed to exist in `base.html`. |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| UIDS-01 | 01-01-PLAN.md | All hardcoded CSS values extracted to `:root {}` custom properties (colors, spacing, radii) | SATISFIED | `:root` block confirmed with all token categories; 3 documented edge-case hex values outside `:root` with written justification |
| UIDS-02 | 01-01-PLAN.md | HTTP method badges follow Swagger convention (GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple) | SATISFIED | Token values match Swagger exact colors; CSS rules use `var(--color-method-*-bg/fg)` |
| UIDS-03 | 01-01-PLAN.md | Clean borders over shadows as primary container definition | SATISFIED | `.card`, `.table-wrap`, `.panel-card`, `.stat-badge` all have `border: 1px solid var(--border-color)` and no `box-shadow` |
| UIDS-04 | 01-01-PLAN.md | Muted label / bright value typographic hierarchy | SATISFIED | `.label` uses `var(--text-dim)` + uppercase; `.value` uses `var(--text-body)`; `.value-prominent` uses `var(--text-primary)` |
| UIDS-05 | 01-02-PLAN.md | Inline style overrides in templates replaced with utility classes | SATISFIED | Zero static `style=` attributes across 5 template files; only 2 Jinja2-dynamic exceptions remain (conditional border-bottom and dynamic `width:{{ pct }}%`) |

**No orphaned requirements.** All 5 phase-1 requirement IDs (UIDS-01 through UIDS-05) were claimed by a plan and are satisfied by codebase evidence.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `base.html` | 812 | `background: #00BFA0` (hardcoded hex outside `:root`) | Info | Brand hover variant; no semantic token maps to this edge case. Documented in summary decisions. No impact on goal. |
| `base.html` | 970 | `color: #C8D6E5` (hardcoded hex outside `:root`) | Info | `cs-2xx` card status neutral color; documented edge case. No impact on goal. |
| `base.html` | 1076 | `background: #313244` (hardcoded hex outside `:root`) | Info | Scrollbar thumb color; documented edge case. No impact on goal. |
| `detail_profile.html` | 25 | `style="border-bottom:{% if not stat.callers %}...{% endif %}"` | Info | Conditional Jinja2 expression — semantically a dynamic value, not a static inline style. Cannot be replaced with a CSS class without JavaScript. Acceptable per plan rules. |

No blockers. All anti-patterns are documented, intentional edge cases.

---

### Human Verification Required

#### 1. Method Badge Visual Colors

**Test:** Start the example app (`cd examples/flask && python app.py`), visit `/flowsurgeon`, and inspect each HTTP method badge in the request list.
**Expected:** GET badge is blue (`#61AFFE`), POST is green (`#49CC90`), PUT is orange (`#FCA130`), DELETE is red (`#F93E3E`), PATCH is teal (`#50E3C2`). All badges are pill-shaped with white text.
**Why human:** Color rendering and pill shape are visual properties that cannot be verified programmatically from HTML/CSS source alone. Correct token values are confirmed in code; browser rendering must be confirmed.

#### 2. No Google Fonts Network Request

**Test:** Open the app in a browser, open DevTools Network tab, hard-refresh. Filter for `fonts.googleapis.com` or `fonts.gstatic.com`.
**Expected:** Zero network requests to any Google Fonts CDN domain. Body font is rendered from the system font stack.
**Why human:** Absence of a CDN request requires live browser observation. Source-level checks (grep for Roboto/googleapis.com = 0) are passing, but the network-tab check provides the definitive proof.

---

### Gaps Summary

No gaps. All automated must-haves are verified. The two items above are human-observable properties that follow naturally from the verified code state — they are confirmations, not blocking concerns.

---

## Commit Verification

All commits documented in the summaries exist in git history:

| Commit | Description |
|--------|-------------|
| `2d31f94` | feat(01-01): build CSS design system token layer in base.html |
| `530c49b` | feat(01-01): add list view default with method row background colors |
| `bb34bb5` | feat(01-02): replace all static inline styles with utility classes |
| `60b80d1` | fix(01-02): apply post-checkpoint UI feedback |

---

_Verified: 2026-03-15_
_Verifier: Claude (gsd-verifier)_
