# Phase 4: Announcement Assets - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce compelling visual assets (screenshots, demo GIF) and update README for a public launch on Reddit, X, and Hacker News. Also produce announcement post drafts. No new features, no Python code changes — this is content production on top of the completed v0.6.0 UI.

</domain>

<decisions>
## Implementation Decisions

### Screenshot selection
- 2 screenshots total: routes home page + request detail view (SQL tab)
- Use existing example app data (/books, /books/{id}, /books/duplicates, /books/slow, /slow, /boom) — matches what users see when they try the examples
- SQL tab chosen for detail screenshot — shows query tracking with slow/dup badges, the most visually distinctive feature
- Images hosted in the repo (e.g., docs/ or assets/ folder), not on external services

### Demo GIF
- GIF format — autoplays on GitHub/PyPI without clicking, maximum first-impression impact
- UI walkthrough flow only: routes home → click route → request detail → SQL tab (~20-30 seconds)
- No terminal/install portion in the GIF — install instructions stay as README text
- Produced via scripted browser automation (Playwright/Selenium) — reproducible, consistent

### README layout
- Hero screenshot (routes home) stays in current position: below intro paragraph + badges, before Features section
- Replace the existing dev.to-hosted screenshot entirely — fully remove all dev.to image references
- Second screenshot (SQL tab detail) + demo GIF placed under the Debug UI section where they illustrate the described features
- No new README sections or summary blocks added

### Announcement framing
- Primary pitch: "django-debug-toolbar for everyone" — framework-agnostic alternative that resonates with Python devs
- Target platforms: Reddit (r/Python, r/flask, r/FastAPI), X (Python/webdev audience), Hacker News (Show HN)
- Announcement post drafts included as deliverables — markdown files ready to copy-paste on launch day
- No comparison table or TL;DR block in README — posts are written separately with platform-appropriate tone

### Claude's Discretion
- Exact image dimensions and cropping
- Browser automation tool choice (Playwright vs Selenium)
- GIF compression and optimization approach
- Screenshot file naming and folder structure within repo
- Draft post tone and length per platform (Reddit long-form, X thread, HN concise)
- Whether to add captions/alt text to README images

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing README and assets
- `README.md` — Current README with old dev.to screenshots to replace; Security section, Features, Debug UI section are placement targets
- `examples/fastapi/demo_fastapi.py` — FastAPI demo app that provides the realistic data for screenshots
- `examples/flask/demo_flask.py` — Flask demo app (alternative data source)

### Prior phase context
- `.planning/phases/01-css-design-system/01-CONTEXT.md` — Design system decisions (dark theme, Swagger badges, shadcn aesthetic)
- `.planning/phases/02-routes-pages/02-CONTEXT.md` — Routes home layout, route detail navigation, breadcrumb design
- `.planning/phases/03-security-documentation/03-CONTEXT.md` — README Security section placement and structure

### UI templates (for understanding what to screenshot)
- `src/flowsurgeon/ui/templates/base.html` — Base template with CSS design system
- `src/flowsurgeon/ui/templates/home.html` — Routes home page template
- `src/flowsurgeon/ui/templates/detail.html` — Request detail page with 4 tabs

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `examples/fastapi/demo_fastapi.py`: Demo app with /books CRUD routes, slow queries, duplicates, errors — provides all the realistic data needed for screenshots
- `examples/flask/demo_flask.py`: Alternative demo app with same route patterns
- README.md already has `<div align="center"><img>` pattern for centered screenshots

### Established Patterns
- README uses GitHub-flavored markdown with centered image blocks (`<div align="center">`)
- Current hero image: `<img src="https://dev-to-uploads.s3.amazonaws.com/..." alt="Home Screen">`
- Badge row uses standard shields.io markdown format
- No existing docs/ or assets/ folder for images — will need to create

### Integration Points
- README.md hero image reference (line 18) — replace URL with repo-relative path
- README.md logo reference (line 2) — currently dev.to hosted, also needs replacing
- Debug UI section (lines 258-277) — placement target for detail screenshot and demo GIF

</code_context>

<specifics>
## Specific Ideas

- "django-debug-toolbar for everyone" is the announcement hook — immediately positions FlowSurgeon for Python devs who know DDT
- Screenshots must look impressive on dark backgrounds (GitHub dark mode, Reddit dark mode) — the dark UI theme helps here
- Demo GIF should feel smooth and purposeful, not rushed — scripted automation allows consistent timing
- Example app data is authentic and matches what users will see — builds trust when they try it themselves

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-announcement-assets*
*Context gathered: 2026-03-16*
