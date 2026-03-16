---
phase: 04-announcement-assets
plan: 01
subsystem: ui
tags: [playwright, chromium, ffmpeg, screenshots, gif, demo]

# Dependency graph
requires:
  - phase: 03.1-ui-polish
    provides: dark-themed UI with toggle-group filters, light mode, breadcrumb fix
  - phase: 02-routes-pages
    provides: routes home page, route detail page, request detail with SQL tab
provides:
  - docs/screenshots/routes-home.png — dark-themed routes home hero screenshot at 1280px
  - docs/screenshots/request-detail-sql.png — SQL tab screenshot for /books/slow request
  - docs/demo/demo.gif — 75-frame animated walkthrough at 10fps, 0.2 MB
  - scripts/capture_assets.py — reproducible Playwright+ffmpeg capture script
affects: [04-02-readme-update, announcement-posts]

# Tech tracking
tech-stack:
  added: [playwright>=1.40, chromium (headless), ffmpeg two-pass palette GIF]
  patterns:
    - Playwright sync_api with color_scheme=dark to force dark mode regardless of system preference
    - subprocess.Popen with try/finally for guaranteed server cleanup
    - ffmpeg two-pass palette GIF (palettegen + paletteuse with bayer dithering) for quality output
    - Frame hold pattern (capture N identical frames) for smooth GIF pacing

key-files:
  created:
    - scripts/capture_assets.py
    - docs/screenshots/routes-home.png
    - docs/screenshots/request-detail-sql.png
    - docs/demo/demo.gif
  modified:
    - pyproject.toml (screenshots dependency group added)
    - uv.lock (updated with playwright)

key-decisions:
  - "screenshots dependency group isolates Playwright from dev/examples groups to avoid polluting CI"
  - "Port 8765 chosen for demo server to avoid conflicts with default 8000"
  - "Frame cleanup after GIF assembly to keep repo clean (no frames/ or palette.png committed)"

patterns-established:
  - "Asset capture script pattern: server lifecycle via subprocess.Popen + try/finally, data seeding via page.goto(), dark mode via color_scheme"

requirements-completed: [ANMT-01, ANMT-02]

# Metrics
duration: 3min
completed: 2026-03-16
---

# Phase 04 Plan 01: Announcement Assets Summary

**Playwright + ffmpeg asset capture producing dark-themed hero screenshot, SQL tab screenshot, and 0.2 MB animated demo GIF for v0.6.0 announcement**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-16T06:08:40Z
- **Completed:** 2026-03-16T06:11:55Z
- **Tasks:** 1 of 2 (Task 2 is human-verify checkpoint)
- **Files modified:** 6

## Accomplishments
- Added `screenshots` dependency group with `playwright>=1.40` to pyproject.toml
- Created `scripts/capture_assets.py` — fully reproducible Playwright+ffmpeg capture (server lifecycle, data seeding, dark mode, GIF assembly)
- Produced `docs/screenshots/routes-home.png` — 1280x800 dark-themed routes home with method badges, route groups, traffic stats (reqs/ms/queries/status)
- Produced `docs/screenshots/request-detail-sql.png` — 1280x800 dark-themed SQL tab for `/books/slow` request showing 2 queries
- Produced `docs/demo/demo.gif` — 75-frame walkthrough at 10fps, 172KB (0.2 MB, well under 10 MB limit)
- All 86 existing tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Playwright dependency group and create capture script** - `e7f2c43` (feat)

**Plan metadata:** (pending human verify checkpoint)

## Files Created/Modified
- `pyproject.toml` - Added `screenshots = ["playwright>=1.40"]` dependency group
- `uv.lock` - Updated with playwright and pyee transitive dependencies
- `scripts/capture_assets.py` - 180-line reproducible asset capture script
- `docs/screenshots/routes-home.png` - Routes home hero screenshot (68,000 bytes)
- `docs/screenshots/request-detail-sql.png` - SQL tab detail screenshot (31,274 bytes)
- `docs/demo/demo.gif` - Animated demo walkthrough (172,652 bytes, 0.2 MB)

## Decisions Made
- Port 8765 chosen for demo server to avoid conflicts with default uvicorn port 8000
- `screenshots` dependency group isolates Playwright from `dev` and `examples` groups
- Frames and palette.png cleaned up after GIF assembly (not committed to repo)
- `/boom` route excluded from data seeding (500 error would contaminate request data visible in screenshots)

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three visual assets ready for use in README hero section and Debug UI section
- Capture script is reproducible: re-running `uv run --group screenshots python scripts/capture_assets.py` will regenerate all assets after UI changes
- Task 2 (human visual verify) pending — human must confirm dark theme, realistic data, and GIF walkthrough quality before continuing to Plan 02

---
*Phase: 04-announcement-assets*
*Completed: 2026-03-16*
