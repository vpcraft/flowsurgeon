# Phase 1: CSS Design System - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactor all UI CSS to use custom properties (shadcn-inspired tokens) with Swagger-convention method badges. This is a visual foundation phase — no new pages, no new Python logic, no route changes. All existing pages inherit the new design system.

</domain>

<decisions>
## Implementation Decisions

### Color palette
- Keep the current dark color structure (#0D0F12 background, #131720 surfaces, #00D4AA brand green) but refine tones for better contrast/consistency
- Extract ALL hardcoded hex values to `:root {}` CSS custom properties with semantic names
- Vibrant, high-contrast accent colors that pop on the dark background (not muted/desaturated)
- Status colors (2xx/3xx/4xx/5xx) should be bright and immediately readable

### Typography
- Remove Google Fonts CDN dependency (Roboto) — switch to system font stack
- Use `-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif` fallback chain
- Self-contained: no external network requests from the debug UI
- Establish tight typographic scale: small labels (uppercase, letter-spacing), body text, headings

### Method badges
- Swagger-style: colored background + white text + rounded pill shape — bold and unmistakable
- GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple
- Should be a visually dominant element in route/request lists

### Component style
- Pure borders-only containers — no box shadows. Clean 1px borders as primary container definition (shadcn aesthetic)
- Remove all existing box-shadow usage from cards, panels, containers
- Subtle hover states with background transition
- Muted label / bright value typographic hierarchy throughout

### Inline style cleanup
- Replace all inline `style=` attributes in templates with utility classes
- Define utility classes in base.html for common overrides (monospace, small text, muted color, fixed widths)

### Claude's Discretion
- Exact color refinement values (how much to adjust existing tones)
- Spacing scale values (--space-1 through --space-8)
- Animation/transition timing
- Exact border-radius values
- Utility class naming conventions

</decisions>

<specifics>
## Specific Ideas

- shadcn/ui is the visual reference — clean, minimal, borders over shadows
- Swagger UI is the reference for method badge styling — bold colored pills
- Current dark color palette is liked and should be preserved in spirit, just refined
- The result must look impressive in screenshots for Reddit/X announcement

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ui/templates/base.html`: Contains ALL CSS in a single `<style>` block (~970 lines). This is the primary file to refactor.
- `ui/assets/panel.css`: Separate CSS for the injected panel button. Keep independent from base.html redesign.

### Established Patterns
- Single `<style>` block in base.html — no external CSS files for the UI (correct for self-contained tool)
- Alpine.js loaded as bundled static asset — no CDN
- Google Fonts CDN link in base.html `<head>` — must be removed
- Templates use Jinja2 `{% block %}` inheritance: base.html -> home.html, detail.html

### Integration Points
- `base.html` is extended by `home.html` and `detail.html` — CSS changes propagate automatically
- `panel.html` (injected panel) uses its own `panel.css` — separate from main UI styles
- Templates have inline `style=` attributes that need to be converted to utility classes
- `ui/panel.py` contains Jinja2 filters (e.g., `_status_class`) that generate CSS class names — these may need updating

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-css-design-system*
*Context gathered: 2026-03-15*
