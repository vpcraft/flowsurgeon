---
phase: 01-css-design-system
plan: 01
subsystem: ui
tags: [css, design-tokens, custom-properties, jinja2, alpine, dark-theme, swagger-convention]

# Dependency graph
requires: []
provides:
  - CSS design token system in base.html :root {} (primitives + semantic tokens)
  - Swagger-convention method badge colors (GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple)
  - Method-colored row backgrounds in list view (.m-{METHOD}-row classes)
  - List/card layout toggle in home.html (list view is default)
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
    - "Row coloring: .tr.m-{METHOD}-row overrides background; .td override ensures white-on-color text"
    - "Alpine layout state: x-data layout='list' for persistent view toggle"

key-files:
  created: []
  modified:
    - src/flowsurgeon/ui/templates/base.html
    - src/flowsurgeon/ui/templates/home.html

key-decisions:
  - "Three out-of-token-system hex values remain: #00BFA0 (brand hover variant), #C8D6E5 (cs-2xx neutral), #313244 (scrollbar thumb) — no semantic tokens map to these edge cases"
  - "focus ring box-shadow on inputs kept — accessibility affordance, not a container depth shadow"
  - "inset box-shadow on .tab-btn-active kept — underline indicator technique, not a container depth shadow"
  - "panel.css kept independent per locked decision — not touched"
  - "List view is default per user feedback (Swagger UI pattern); card view accessible via toggle icon"
  - "Method row backgrounds reuse --color-method-*-bg tokens (dark tints) for visual continuity with badges"

patterns-established:
  - "Token naming: --color-* for primitives, --bg-* / --text-* / --border-* for semantic tokens"
  - "Method badge tokens: --color-method-{method}-bg and --color-method-{method}-fg pairs"
  - "Status badge tokens: --color-status-{range}-bg and --color-status-{range}-fg pairs"
  - "Spacing: var(--space-N) where N=1..8 maps to 4/8/12/16/20/24/32/48px"
  - "Row coloring: .tr.m-{METHOD}-row uses compound selector to avoid specificity conflicts"

requirements-completed: [UIDS-01, UIDS-02, UIDS-03, UIDS-04]

# Metrics
duration: 45min
completed: 2026-03-15
---

# Phase 1 Plan 01: CSS Design System Summary

**Token-driven CSS design system in base.html with Swagger-convention method badges, method-colored list view rows as default, and list/card toggle — replacing all hardcoded hex/px values with :root custom properties**

## Performance

- **Duration:** ~45 min (two sessions: Task 1 + feedback iteration)
- **Started:** 2026-03-14T21:29:09Z
- **Completed:** 2026-03-15
- **Tasks:** 2 of 2 (complete — including user feedback changes)
- **Files modified:** 2

## Accomplishments

- Built complete :root {} token layer: 11 gray primitives, brand color, 12 method badge tokens, 8 status badge tokens, 3 duration tokens, 6 semantic bg tokens, 6 semantic text tokens, 8 spacing tokens, 4 radius tokens, 2 font stacks, 2 transition tokens
- Replaced all ~40 hardcoded hex values with var() token references; only 3 documented edge cases remain outside :root
- Removed Google Fonts CDN links and Roboto font-family; body now uses var(--font-sans) system stack
- Fixed method badges to Swagger convention: GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple with pill border-radius
- Removed box-shadow from .card, .table-wrap, .panel-card, .stat-badge, .req-card; all now use 1px solid var(--border-color)
- Added .label/.value/.value-prominent typographic hierarchy classes
- Added full utility class set (29 classes) and code { font-family: var(--font-mono) } reset
- Added list view as default in home.html with method-colored row backgrounds (full row = method color)
- Added list/card toggle icons in filter bar; Alpine layout state persisted in component scope

## Task Commits

Each task was committed atomically:

1. **Task 1: Build token layer and refactor all base.html CSS** - `2d31f94` (feat)
2. **Task 2 feedback: Add list view default with method row backgrounds** - `530c49b` (feat)

## Files Created/Modified

- `src/flowsurgeon/ui/templates/base.html` - Complete CSS design system refactor: token layer, badge colors, border-only containers, typography hierarchy, utility classes, method row background CSS (.m-{METHOD}-row)
- `src/flowsurgeon/ui/templates/home.html` - Added list view (table layout), list/card toggle buttons, method-colored rows using .tr.m-{METHOD}-row compound class

## Decisions Made

- Three hex values retained outside :root as edge cases: `#00BFA0` (brand hover variant), `#C8D6E5` (cs-2xx neutral blue-grey), `#313244` (scrollbar thumb)
- Focus ring `box-shadow` on `.filter-input:focus` and `.filter-select:focus` retained — accessibility affordance
- Inset `box-shadow` on `.tab-btn-active` retained — underline indicator technique (inset 0 -2px 0), not a depth shadow
- List view is default per user feedback matching Swagger UI visual convention
- Method row backgrounds use the same `--color-method-*-bg` dark tints as method badges for visual continuity

## Deviations from Plan

### User-Requested Changes at Checkpoint

**1. Default view changed to list view**
- **Requested during:** Task 2 visual verification checkpoint
- **Change:** Added Alpine `layout: 'list'` default; table/list view rendered before card grid
- **Files modified:** `src/flowsurgeon/ui/templates/home.html`, `src/flowsurgeon/ui/templates/base.html`

**2. Method colors applied as row background (not just badge)**
- **Requested during:** Task 2 visual verification checkpoint
- **Change:** Added `.tr.m-{METHOD}-row` CSS rules (background = method bg token); `.td` color override to `var(--text-primary)` for legibility; `color-mix()` hover brightening
- **Files modified:** `src/flowsurgeon/ui/templates/base.html`, `src/flowsurgeon/ui/templates/home.html`

---

**Total deviations:** 0 auto-fix rule violations. 2 user-requested feedback changes applied at checkpoint.
**Impact on plan:** Both changes directly improve visual quality. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Token layer fully defined; ready for Plan 02 (inline style replacement)
- All utility classes available for Plan 02 template work
- List view established as the canonical request display pattern
- Phase 2 pages will inherit complete token system automatically via base.html extension

---
*Phase: 01-css-design-system*
*Completed: 2026-03-15*
