# Phase 1: CSS Design System - Research

**Researched:** 2026-03-15
**Domain:** CSS custom properties, design tokens, Jinja2 template refactoring
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Keep current dark color structure (#0D0F12 background, #131720 surfaces, #00D4AA brand green) — refine tones only
- Extract ALL hardcoded hex values to `:root {}` CSS custom properties with semantic names
- Remove Google Fonts CDN dependency (Roboto) — switch to system font stack: `-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif`
- No external network requests from the debug UI
- Method badges: GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple; colored background + white text + rounded pill
- Pure borders-only containers — no box shadows. Clean 1px borders as primary container definition
- Remove all existing box-shadow usage from cards, panels, containers
- Replace all inline `style=` attributes in templates with utility classes
- Define utility classes in base.html for common overrides (monospace, small text, muted color, fixed widths)
- Single `<style>` block in base.html — no external CSS files for the UI
- `panel.css` stays independent from the base.html redesign

### Claude's Discretion
- Exact color refinement values (how much to adjust existing tones)
- Spacing scale values (--space-1 through --space-8)
- Animation/transition timing
- Exact border-radius values
- Utility class naming conventions

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UIDS-01 | All hardcoded CSS values extracted to `:root {}` custom properties (colors, spacing, radii) | Token inventory below; every hex/px literal in base.html identified |
| UIDS-02 | HTTP method badges follow Swagger convention (GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple) | Current `.m-GET` etc. classes identified; Swagger color mapping documented |
| UIDS-03 | Clean borders over shadows as primary container definition | Current shadow usage catalogued; border-only pattern documented |
| UIDS-04 | Muted label / bright value typographic hierarchy | `.card-label` / `.card-value` pattern already exists; needs to be consistent and token-driven |
| UIDS-05 | Inline style overrides in templates replaced with utility classes | Full inventory of inline `style=` attributes captured across all templates |
</phase_requirements>

---

## Summary

Phase 1 is a pure CSS refactor with no Python logic changes. The primary file is `base.html`, which contains ~970 lines of CSS in a single `<style>` block. The task has three distinct workstreams: (1) build a token layer in `:root {}`, (2) rewrite method/status badges to Swagger convention colors, and (3) replace inline `style=` attributes across five template files with named utility classes.

The existing CSS is well-structured with clear class naming conventions already in place. The primary problems are: hardcoded hex colors appear in ~40+ locations, method badge colors do not match Swagger convention (current GET is green, should be blue; POST is amber, should be green), the `.card` components use background fills but no explicit borders, and the partial templates (`detail_profile.html`, `detail_sql.html`, `detail_traceback.html`) are almost entirely inline styles.

**Primary recommendation:** Build the token system first (`:root {}`), then do a single pass replacing hardcoded values with tokens, then fix badge colors, then convert inline styles to utility classes. Do not interleave these steps — they are separable and should be committed independently for clean diffs.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| CSS Custom Properties | Native (all browsers) | Design tokens / theming | No build step, works in any `<style>` block |
| Jinja2 | Already in project | Template rendering | Already used; `{% block %}` inheritance propagates CSS automatically |

### No New Dependencies

This phase introduces zero new libraries. The entire implementation is plain CSS and Jinja2 template edits.

**Key constraint from REQUIREMENTS.md:** "No build step" — Tailwind is explicitly out of scope. No PostCSS, no npm.

---

## Architecture Patterns

### Token Naming Convention (shadcn-inspired)

Use semantic layering: primitive tokens (raw values) defined first, semantic tokens (named by role) reference primitives.

```css
/* Source: shadcn/ui design token convention */
:root {
  /* ── Primitives ── */
  --color-gray-950: #0D0F12;
  --color-gray-900: #131720;
  --color-gray-850: #161A22;
  --color-gray-800: #0D1117;
  --color-gray-700: #1E2328;
  --color-gray-500: #4B5563;
  --color-gray-400: #6B7280;
  --color-gray-300: #9CA3AF;
  --color-gray-100: #E5E7EB;
  --color-white:    #FFFFFF;

  --color-brand:    #00D4AA;

  /* Method badge colors (Swagger convention) */
  --color-method-get-bg:    #1a3a5c;
  --color-method-get-fg:    #60A5FA;
  --color-method-post-bg:   #1a3b2a;
  --color-method-post-fg:   #34D399;
  --color-method-put-bg:    #3b2a1a;
  --color-method-put-fg:    #FB923C;
  --color-method-delete-bg: #3b1a1a;
  --color-method-delete-fg: #F87171;
  --color-method-patch-bg:  #2a1a3b;
  --color-method-patch-fg:  #A78BFA;
  --color-method-head-bg:   #1E2328;
  --color-method-head-fg:   #9CA3AF;

  /* Status badge colors */
  --color-status-2xx-bg:    #1a3b2a;
  --color-status-2xx-fg:    #34D399;
  --color-status-3xx-bg:    #3b2a1a;
  --color-status-3xx-fg:    #FB923C;
  --color-status-4xx-bg:    #3b2a1a;
  --color-status-4xx-fg:    #FB923C;
  --color-status-5xx-bg:    #3b1a1a;
  --color-status-5xx-fg:    #F87171;

  /* Duration colors */
  --color-dur-fast:   #34D399;
  --color-dur-medium: #FB923C;
  --color-dur-slow:   #F87171;

  /* ── Semantic tokens ── */
  --bg-base:      var(--color-gray-950);
  --bg-surface:   var(--color-gray-900);
  --bg-elevated:  var(--color-gray-850);
  --bg-sunken:    var(--color-gray-800);
  --border-color: var(--color-gray-700);

  --text-primary:  var(--color-white);
  --text-body:     var(--color-gray-100);
  --text-muted:    var(--color-gray-300);
  --text-dim:      var(--color-gray-400);
  --text-faint:    var(--color-gray-500);
  --text-brand:    var(--color-brand);

  /* ── Spacing scale ── */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-7:  32px;
  --space-8:  48px;

  /* ── Radii ── */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-pill: 999px;

  /* ── Typography ── */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace;

  /* ── Transitions ── */
  --transition-fast: 0.12s ease;
  --transition-base: 0.15s ease;
}
```

### Swagger-Convention Method Badge Colors

The current implementation uses green for GET and amber for POST/PUT/PATCH — this is NOT Swagger convention.

| Method | Swagger Reference Color | Suggested Token BG | Suggested Token FG |
|--------|------------------------|--------------------|--------------------|
| GET | Blue | `#1a3a5c` | `#60A5FA` |
| POST | Green | `#1a3b2a` | `#34D399` |
| PUT | Orange/Amber | `#3b2a1a` | `#FB923C` |
| DELETE | Red | `#3b1a1a` | `#F87171` |
| PATCH | Purple | `#2a1a3b` | `#A78BFA` |
| HEAD/OTHER | Gray | `#1E2328` | `#9CA3AF` |

All background values use a dark tint of the foreground hue (consistent with current pattern but with correct hue mapping).

Swagger's "bold pill" badge shape: `border-radius: var(--radius-pill)` + `padding: 3px 10px` + `font-weight: 700`.

### Border-Only Container Pattern (shadcn aesthetic)

Replace background-filled cards with bordered containers:

```css
/* BEFORE */
.card {
  background: #131720;
  border-radius: 12px;
  /* no border */
}

/* AFTER */
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}
```

Remove all `box-shadow` rules. The `.table-wrap`, `.panel-card`, `.card`, and `.stat-badge` components are the main targets.

### Label/Value Typographic Hierarchy

The `.card-label` / `.card-value` pattern already exists in base.html. It needs to become the universal pattern, applied consistently via utility classes across all templates.

```css
/* Labels: muted, uppercase, spaced */
.label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* Values: bright, weighted */
.value {
  color: var(--text-body);
  font-weight: 500;
}

.value-prominent {
  color: var(--text-primary);
  font-weight: 700;
}
```

### Utility Classes for Inline Style Replacement

Based on the full inventory of inline `style=` attributes found across templates, define these utility classes in base.html:

```css
/* Monospace */
.u-mono { font-family: var(--font-mono); }

/* Font sizes */
.u-text-xs  { font-size: 11px; }
.u-text-sm  { font-size: 12px; }
.u-text-md  { font-size: 13px; }
.u-text-base { font-size: 14px; }
.u-text-lg  { font-size: 20px; }

/* Colors */
.u-muted  { color: var(--text-muted); }
.u-dim    { color: var(--text-dim); }
.u-faint  { color: var(--text-faint); }
.u-brand  { color: var(--text-brand); }
.u-bright { color: var(--text-primary); }

/* Layout */
.u-flex        { display: flex; }
.u-flex-col    { display: flex; flex-direction: column; }
.u-items-center { align-items: center; }
.u-gap-1       { gap: var(--space-1); }
.u-gap-2       { gap: var(--space-2); }
.u-gap-3       { gap: var(--space-3); }
.u-gap-4       { gap: var(--space-4); }
.u-flex-1      { flex: 1; }
.u-shrink-0    { flex-shrink: 0; }
.u-min-h-0     { min-height: 0; }

/* Overflow */
.u-scroll-y    { overflow-y: auto; }

/* Display: none helper (complement to x-cloak) */
.u-hidden      { display: none; }
```

### Anti-Patterns to Avoid

- **Using `var()` inside `calc()` with unitless values:** CSS custom properties must carry units when used in `calc()`. `--space-4: 16px` works; `--space-4: 16` does not.
- **Mixing token layers:** Don't reference `--color-gray-900` directly in component CSS — always reference the semantic token (`--bg-surface`). This keeps theming clean.
- **Replacing inline styles in partials without adding the utility class to base.html first:** The partial is rendered inside base.html's inheritance chain, so base.html's `<style>` block covers it — but the class must be defined there first.
- **Forgetting `detail_profile.html` is almost entirely inline styles:** This partial has ~35 inline style attributes, the most of any file. Plan for it to require the most utility class work.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS variable fallbacks | Custom JS polyfill | Native CSS custom properties | 100% browser support; no polyfill needed |
| Design token system | Complex JS-driven theming | Plain `:root {}` custom properties | Project constraint: no build step |
| Font loading | Custom font CDN or base64 embed | System font stack | Per locked decision; zero network requests |

---

## Common Pitfalls

### Pitfall 1: Broken `.m-GET` class references after badge refactor
**What goes wrong:** Templates reference `.m-GET`, `.m-POST` etc. by name. If the class names change, badges break silently (no visible error, just unstyled).
**Why it happens:** Class names are generated in `ui/panel.py` via Jinja2 filters; the filter output must match the CSS class names.
**How to avoid:** Keep class names identical (`m-GET`, `m-POST`, etc.) — only change the CSS rules inside them. Check `ui/panel.py` `_status_class` filter before and after.
**Warning signs:** Badges appear unstyled (no background/color) after changes.

### Pitfall 2: CSS custom property not inheriting in `<code>` elements
**What goes wrong:** Inline `style="font-family:monospace"` on `<code>` tags in partials is replaced with `.u-mono`, but the monospace font doesn't apply if the `<code>` element resets `font-family`.
**Why it happens:** Some browser UA stylesheets set `font-family` on `code` elements.
**How to avoid:** Add explicit `code { font-family: var(--font-mono); }` reset in the base CSS alongside the utility class.

### Pitfall 3: Inline styles with dynamic values cannot be fully replaced
**What goes wrong:** `detail_profile.html` line 63 has `style="width:{{ pct }}%; ..."` — the `pct` value is Jinja2-rendered dynamically. This cannot be replaced with a static utility class.
**Why it happens:** The width is data-driven.
**How to avoid:** Inline styles with Jinja2 interpolation are acceptable exceptions to UIDS-05. Replace everything that is static; leave dynamic width/color values as inline styles. Document the exceptions.

### Pitfall 4: Missing Google Fonts removal causing flash of unstyled text
**What goes wrong:** Removing the `<link>` to Google Fonts without updating `font-family` on `body` causes a brief flash or unexpected font rendering in dev.
**Why it happens:** Browser still requests the font if `font-family: 'Roboto'` appears first in the stack.
**How to avoid:** Remove both the `<link rel="preconnect">` tags AND the `font-family: 'Roboto', ...` reference on `body` in the same commit.

---

## Inline Style Inventory

Full count of inline `style=` attributes requiring conversion, by file:

| File | Inline Style Count | Notes |
|------|--------------------|-------|
| `home.html` | 5 | width on inputs/selects, display:none on button, color in spans |
| `detail.html` | 5 | margin-top, font-family, color, max-height |
| `partials/detail_profile.html` | ~35 | Almost entirely inline — largest workload |
| `partials/detail_sql.html` | ~10 | flex layout, padding, color |
| `partials/detail_traceback.html` | ~10 | flex layout, color, font-family |

**Exceptions (dynamic inline styles that must remain):**
- `detail_profile.html:63` — `style="width:{{ pct }}%..."` — Jinja2 interpolated width for progress bar

---

## Existing Color Inventory (tokens to create)

All unique hardcoded hex values found in base.html CSS and templates:

| Value | Current Usage | Proposed Token |
|-------|--------------|----------------|
| `#0D0F12` | body background | `--bg-base` |
| `#131720` | topbar, surfaces, cards | `--bg-surface` |
| `#161A22` | hover states, stat-badge | `--bg-elevated` |
| `#0D1117` | table head, panel head | `--bg-sunken` |
| `#1E2328` | separators, borders | `--border-color` |
| `#4B5563` | faint text, breadcrumb sep | `--text-faint` |
| `#6B7280` | dim text, labels | `--text-dim` |
| `#9CA3AF` | muted text | `--text-muted` |
| `#E5E7EB` | body text | `--text-body` |
| `#FFFFFF` | headings, active nav | `--text-primary` |
| `#00D4AA` | brand, nav underline, logo | `--text-brand` / `--color-brand` |
| `#10B981` | old GET/2xx green (replace) | retire → use new method tokens |
| `#F59E0B` | old amber badges (replace) | retire → use new method tokens |
| `#EF4444` | old DELETE/5xx red (replace) | retire → use new status tokens |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SASS/LESS variables | CSS custom properties in `:root {}` | ~2017, universal support by 2020 | No build step needed |
| Google Fonts CDN | System font stack | Best practice ~2023 | Removes external dependency, faster load |
| Box shadows for depth | 1px borders (shadcn aesthetic) | Design trend ~2022-2024 | Cleaner, more readable on dark backgrounds |

**Deprecated in this phase:**
- `font-family: 'Roboto'` reference — replaced by system stack
- Google Fonts `<link>` tags — removed entirely
- All `box-shadow` rules on containers — replaced by `border: 1px solid var(--border-color)`

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected — CSS/template refactor; no automated tests exist |
| Config file | none |
| Quick run command | Manual browser inspection |
| Full suite command | Manual browser inspection of all routes |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UIDS-01 | No hardcoded hex in CSS | manual-only | `grep -r '#[0-9a-fA-F]\{3,6\}' src/flowsurgeon/ui/templates/base.html` | N/A |
| UIDS-02 | GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple | manual-only | Visual inspection in browser | N/A |
| UIDS-03 | No box-shadow on containers | manual-only | `grep -n 'box-shadow' src/flowsurgeon/ui/templates/base.html` | N/A |
| UIDS-04 | Labels muted, values bright | manual-only | Visual inspection in browser | N/A |
| UIDS-05 | No static inline style= attributes | manual-only | `grep -n 'style=' src/flowsurgeon/ui/templates/**/*.html` | N/A |

### Wave 0 Gaps

None — this phase has no automated test requirements. Verification is via grep-based spot checks and browser visual inspection.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `src/flowsurgeon/ui/templates/base.html` — full CSS inventory
- Direct code inspection of all template files — inline style inventory
- `01-CONTEXT.md` — locked decisions
- `REQUIREMENTS.md` — UIDS-01 through UIDS-05

### Secondary (MEDIUM confidence)
- Swagger UI source (swagger-ui.github.io) — method badge color convention; GET=blue, POST=green, PUT=orange, DELETE=red, PATCH=purple is the well-established standard
- shadcn/ui design system (ui.shadcn.com) — border-over-shadow, token naming conventions

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Token inventory: HIGH — derived from direct file inspection
- Badge color mapping: HIGH — Swagger convention is stable and well-documented
- Utility class naming: MEDIUM — Claude's discretion; names chosen for clarity
- Inline style count: HIGH — derived from direct grep across all template files

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable domain — plain CSS)
