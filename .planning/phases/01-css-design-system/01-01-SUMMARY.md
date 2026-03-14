---
phase: 01-css-design-system
plan: 01
subsystem: ui
tags: [css, design-tokens, custom-properties, jinja2, dark-theme]

# Dependency graph
requires: []
provides:
  - CSS design token system in base.html :root {} (primitives + semantic tokens)
  - Swagger-convention method badge colors (GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple)
  - Border-only containers (no box-shadow) on .card, .table-wrap, .panel-card, .stat-badge
  - Label/value typographic hierarchy classes (.label, .value, .value-prominent)
  - Full utility class set (.u-mono, .u-text-*, .u-muted/.u-dim/.u-faint/.u-brand/.u-bright, .u-flex, .u-gap-*, etc.)
  - System font stack replacing Google Fonts CDN
affects:
  - 01-02 (inline style replacement — uses utility classes defined here)
  - 02-* (all Phase 2 pages inherit base.html token layer)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "shadcn-inspired semantic token layering: primitive → semantic tokens in :root {}"
    - "Swagger-convention badge colors: dark tint background with bright foreground"
    - "Border-only container aesthetic: 1px solid var(--border-color), no box-shadow for depth"
    - "Utility class prefix: .u- for all utility helpers"

key-files:
  created: []
  modified:
    - src/flowsurgeon/ui/templates/base.html

key-decisions:
  - "Three out-of-token-system hex values remain: #00BFA0 (brand hover variant), #C8D6E5 (cs-2xx neutral), #313244 (scrollbar thumb) — no semantic tokens map to these edge cases"
  - "focus ring box-shadow on inputs kept — accessibility affordance, not a container depth shadow"
  - "inset box-shadow on .tab-btn-active kept — underline indicator technique, not a container depth shadow"
  - "panel.css kept independent per locked decision — not touched"

patterns-established:
  - "Token naming: --color-* for primitives, --bg-* / --text-* / --border-* for semantic tokens"
  - "Method badge tokens: --color-method-{method}-bg and --color-method-{method}-fg pairs"
  - "Status badge tokens: --color-status-{range}-bg and --color-status-{range}-fg pairs"
  - "Spacing: var(--space-N) where N=1..8 maps to 4/8/12/16/20/24/32/48px"

requirements-completed: [UIDS-01, UIDS-02, UIDS-03, UIDS-04]

# Metrics
duration: 2min
completed: 2026-03-15
---

# Phase 1 Plan 01: CSS Design System Summary

**Token-driven CSS design system in base.html: :root primitive/semantic tokens, Swagger-convention method badges (GET=blue), border-only containers, label/value hierarchy, utility classes, system fonts**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-14T21:29:09Z
- **Completed:** 2026-03-14T21:31:09Z
- **Tasks:** 1 of 2 (checkpoint reached — awaiting visual verification)
- **Files modified:** 1

## Accomplishments

- Built complete :root {} token layer: 11 gray primitives, brand color, 12 method badge tokens, 8 status badge tokens, 3 duration tokens, 6 semantic bg tokens, 6 semantic text tokens, 8 spacing tokens, 4 radius tokens, 2 font stacks, 2 transition tokens
- Replaced all ~40 hardcoded hex values with var() token references; only 3 edge cases remain outside :root (hover variant, scrollbar, one neutral card status color)
- Removed Google Fonts CDN links and Roboto font-family; body now uses var(--font-sans) system stack
- Fixed method badges to Swagger convention: GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple with pill border-radius
- Removed box-shadow from .card, .table-wrap, .panel-card, .stat-badge, .req-card; all now use 1px solid var(--border-color)
- Added .label/.value/.value-prominent typographic hierarchy classes
- Added full utility class set (29 classes) and code { font-family: var(--font-mono) } reset

## Task Commits

Each task was committed atomically:

1. **Task 1: Build token layer and refactor all base.html CSS** - `2d31f94` (feat)

## Files Created/Modified

- `src/flowsurgeon/ui/templates/base.html` - Complete CSS design system refactor: token layer, badge colors, border-only containers, typography hierarchy, utility classes

## Decisions Made

- Three hex values retained outside :root as edge cases: `#00BFA0` (brand hover variant — no hover token defined), `#C8D6E5` (cs-2xx neutral blue-grey — not in semantic token system), `#313244` (scrollbar thumb — vendor-specific, no token)
- Focus ring `box-shadow` on `.filter-input:focus` and `.filter-select:focus` retained — accessibility affordance, not a depth shadow per the plan's intent
- Inset `box-shadow` on `.tab-btn-active` retained — it's an underline indicator technique (inset 0 -2px 0), not a container shadow

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Token layer is fully defined and ready for Plan 02 (inline style replacement)
- All utility classes defined that Plan 02 needs for replacing inline style= attributes
- Plan 02 can begin immediately after human visual verification of this plan's output
- Phase 2 pages will inherit the complete token system automatically via base.html

---
*Phase: 01-css-design-system*
*Completed: 2026-03-15*
