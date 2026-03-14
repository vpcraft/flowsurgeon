---
phase: 01-css-design-system
plan: 02
subsystem: ui
tags: [css, jinja2, templates, design-system, utility-classes]

requires:
  - phase: 01-css-design-system/01-01
    provides: "Design token system, utility classes, and component classes in base.html"

provides:
  - "All static inline style= attributes removed from home.html, detail.html, and all three partials"
  - "Method badges use Swagger solid-color scheme (colored background, white text)"
  - "Professional bordered-row table style replacing colored-row approach"
  - "Simplified home.html: no tab system, no profiling panel, no Requests nav item"
  - "Simplified detail.html: Details, SQL, Traceback tabs only (Profile tab removed)"

affects:
  - 02-routes-page
  - any future template work

tech-stack:
  added: []
  patterns:
    - "No static inline style= attributes in templates — all styling via utility/component classes"
    - "Dynamic Jinja2-interpolated inline styles (e.g., width:{{ pct }}%) are documented exceptions"
    - "Method badges: Swagger solid-color convention — colored bg, white text, pill shape"
    - "List table rows: bordered rows via CSS border-bottom on .tr, hover background only"

key-files:
  created: []
  modified:
    - src/flowsurgeon/ui/templates/base.html
    - src/flowsurgeon/ui/templates/home.html
    - src/flowsurgeon/ui/templates/detail.html
    - src/flowsurgeon/ui/templates/partials/detail_profile.html
    - src/flowsurgeon/ui/templates/partials/detail_sql.html
    - src/flowsurgeon/ui/templates/partials/detail_traceback.html

key-decisions:
  - "Method badge tokens updated to Swagger solid-color palette (blue/green/orange/red/teal/purple) with white text — replaces dark translucent background + colored text approach"
  - "Row background colors removed entirely — .m-*-row classes deleted; professional bordered-row style used instead"
  - "Latency & Queries tab removed from home.html — list view is the only view; tab system was unnecessary complexity"
  - "Profiling tab and placeholder panel removed from home.html — feature not yet shipped, no value as placeholder"
  - "Profile tab removed from detail.html — feature not yet shipped"
  - "Requests nav item removed from home.html topbar — redundant when there is only one page"

patterns-established:
  - "Admin-table pattern: .tr has border-bottom: 1px solid var(--border-color); hover changes background only"
  - "Method badge pattern: solid Swagger color as background, white text, pill border-radius"

requirements-completed:
  - UIDS-05

duration: 45min
completed: 2026-03-15
---

# Phase 1 Plan 2: Replace Inline Styles with Utility Classes Summary

**All static inline styles removed from 5 templates and replaced with utility/component classes; method badges updated to Swagger solid-color scheme; home page simplified to clean admin-style list with bordered rows.**

## Performance

- **Duration:** ~45 min (including checkpoint iteration)
- **Started:** 2026-03-15
- **Completed:** 2026-03-15
- **Tasks:** 2 (Task 1 automated, Task 2 checkpoint with feedback applied)
- **Files modified:** 6 templates + base.html

## Accomplishments

- Converted all static `style=` attributes across 5 template files to utility/component classes from the design system
- Applied user feedback from checkpoint: removed method row backgrounds, updated badges to Swagger solid colors, removed 3 UI elements (Latency & Queries tab, Profiling tab, Requests navbar), removed Profile tab from detail page
- Left only documented exceptions: dynamic Jinja2-interpolated `style="width:{{ pct }}%"` on profile bar fills
- Home page is now a clean, focused admin-table with bordered rows and no unnecessary tab complexity

## Task Commits

1. **Task 1: Replace inline styles with utility classes** - `bb34bb5` (feat)
2. **Task 2 (checkpoint feedback): UI polish — method badges, bordered rows, tab removal** - `60b80d1` (fix)

## Files Created/Modified

- `src/flowsurgeon/ui/templates/base.html` - Updated method badge tokens to Swagger solid colors; removed .m-*-row CSS; added border-bottom to .tr
- `src/flowsurgeon/ui/templates/home.html` - Removed Requests navbar, Latency & Queries tab, Profiling tab/panel; simplified to clean list + layout toggle
- `src/flowsurgeon/ui/templates/detail.html` - Removed Profile tab from subnav and content
- `src/flowsurgeon/ui/templates/partials/detail_profile.html` - ~35 inline styles converted to utility classes
- `src/flowsurgeon/ui/templates/partials/detail_sql.html` - ~10 inline styles converted to utility classes
- `src/flowsurgeon/ui/templates/partials/detail_traceback.html` - ~10 inline styles converted to utility classes

## Decisions Made

- Method badge tokens updated to Swagger palette (solid colors, white text) — the previous dark translucent backgrounds felt inconsistent with the rest of the UI
- Row backgrounds removed entirely — bordered rows are the professional admin pattern; colored rows added visual noise without semantic value
- Latency & Queries tab removed — with only one view available, a tab system was redundant scaffolding
- Profiling and Profile tabs removed — not yet implemented, placeholder state adds confusion

## Deviations from Plan

The plan only covered inline style removal. Post-checkpoint user feedback triggered 6 additional changes applied in a single fix commit:

**1. [Post-checkpoint] Removed method row background colors**
- **Found during:** Task 2 (visual review checkpoint)
- **Issue:** Colored row backgrounds (`.m-GET-row`, etc.) were visually heavy; not a professional admin pattern
- **Fix:** Deleted all `.m-*-row` CSS rules from base.html; removed class from `<a class="tr">` in home.html
- **Files modified:** base.html, home.html
- **Committed in:** 60b80d1

**2. [Post-checkpoint] Updated method badges to Swagger solid-color scheme**
- **Found during:** Task 2 (visual review checkpoint)
- **Issue:** Dark translucent badge backgrounds did not match Swagger UI convention
- **Fix:** Updated token values to Swagger exact colors (GET #61AFFE, POST #49CC90, PUT #FCA130, DELETE #F93E3E, PATCH #50E3C2, HEAD #9012FE); set fg tokens to #FFFFFF
- **Files modified:** base.html
- **Committed in:** 60b80d1

**3. [Post-checkpoint] Added bordered admin-table row style**
- **Issue:** Rows had no separator after removing background colors
- **Fix:** Added `border-bottom: 1px solid var(--border-color)` to `.tr` in base.html; removed explicit `<div class="sep">` dividers from home.html loop
- **Committed in:** 60b80d1

**4. [Post-checkpoint] Removed Latency & Queries and Profiling tabs from home.html**
- **Fix:** Deleted tab-btn anchors, `x-data` tab state, profiling placeholder panel; simplified to single panel with no tab system
- **Committed in:** 60b80d1

**5. [Post-checkpoint] Removed Requests navbar link from home.html topbar**
- **Fix:** Removed `<a class="nav-item active">` Requests link; topbar now shows logo only
- **Committed in:** 60b80d1

**6. [Post-checkpoint] Removed Profile tab from detail.html**
- **Fix:** Removed subnav item and `x-show="tab === 'profile'"` panel
- **Committed in:** 60b80d1

---

**Total deviations:** 6 post-checkpoint UI changes (all user-directed feedback)
**Impact on plan:** UI improvements reducing complexity and aligning with professional admin patterns. No scope creep — changes align with the design system objective.

## Issues Encountered

None beyond the checkpoint feedback round.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All templates now fully utility-class-based — ready for Phase 2 routes page work
- Method badge and status badge systems are complete and consistent
- Detail page has Details, SQL, and Traceback tabs — Profile tab removed pending implementation
- home.html passes extra `active_view` and `profiling_enabled` template vars from Python backend that are no longer consumed by the template — these can be cleaned up in a future maintenance pass but cause no runtime errors

---
*Phase: 01-css-design-system*
*Completed: 2026-03-15*
