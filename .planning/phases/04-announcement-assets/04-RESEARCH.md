# Phase 04: Announcement Assets - Research

**Researched:** 2026-03-16
**Domain:** Screenshot capture, GIF production, README image integration, announcement copywriting
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Screenshot selection:** 2 screenshots — routes home page + request detail SQL tab
- **Data source:** Existing FastAPI example app (`examples/fastapi/demo_fastapi.py`) with routes /books, /books/{id}, /books/duplicates, /books/slow, /slow, /boom
- **Image hosting:** Repo-relative paths in a new `docs/` or `assets/` folder — NO external services
- **GIF format:** GIF (not MP4/WebM) for autoplay on GitHub and PyPI without user action
- **GIF content:** UI walkthrough only — routes home → click route → request detail → SQL tab (~20-30 seconds). No terminal/install portion.
- **GIF production:** Scripted browser automation (Playwright or Selenium) — reproducible and consistent
- **README hero placement:** Below intro paragraph + badges, before Features section (current position); replace existing dev.to-hosted screenshot entirely
- **Second screenshot + GIF placement:** Under the Debug UI section
- **No new README sections** — no comparison table, no TL;DR block
- **Announcement framing:** "django-debug-toolbar for everyone" as primary pitch
- **Target platforms:** Reddit (r/Python, r/flask, r/FastAPI), X (Python/webdev), Hacker News (Show HN)
- **Announcement deliverables:** Markdown files ready to copy-paste on launch day

### Claude's Discretion

- Exact image dimensions and cropping
- Browser automation tool choice (Playwright vs Selenium)
- GIF compression and optimization approach
- Screenshot file naming and folder structure within repo
- Draft post tone and length per platform (Reddit long-form, X thread, HN concise)
- Whether to add captions/alt text to README images

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ANMT-01 | Fresh README screenshots showing redesigned UI with realistic data | Playwright scripted capture; FastAPI demo provides realistic data; repo `docs/screenshots/` folder; README `<div align="center"><img>` pattern already established |
| ANMT-02 | Demo GIF or video (30-60 seconds) showing install, wrap app, browse debug UI | Playwright scripted recording → frames → GIF via ffmpeg (available) + convert (ImageMagick, available); gifsicle absent but convert covers optimization |
</phase_requirements>

---

## Summary

Phase 4 is content production, not code production. The deliverables are two static PNG screenshots, one animated GIF, an updated README.md, and three platform-specific announcement post drafts. No Python source changes are needed.

The toolchain splits cleanly into two tracks. The **capture track** uses Playwright (to be installed via uv's `screenshots` dependency group) to drive a real Chromium browser against the running FastAPI demo server, capture screenshots as PNG, and record a sequence of frames for the GIF. The **assembly track** uses ffmpeg and ImageMagick `convert` (both confirmed present on this machine) to assemble frames into a GIF. gifsicle is not available, but `convert`'s `-layers Optimize` flag provides adequate compression for README use.

The README already has a working `<div align="center"><img>` pattern. The only structural change is replacing the two dev.to-hosted URLs with repo-relative paths and adding a second image + GIF block in the Debug UI section. Announcement posts are plain markdown files — no tooling required.

**Primary recommendation:** Use Playwright (sync API) for screenshot and GIF frame capture; ffmpeg to convert frames to a palette-optimized GIF; store assets in `docs/screenshots/` and `docs/demo/`; write three announcement files in `docs/announcements/`.

---

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| playwright (Python) | 1.x current | Headless Chromium browser automation for screenshots and frame capture | Industry standard for reproducible browser automation; sync API is simpler than Selenium for scripted capture |
| ffmpeg | system (confirmed present: `/usr/bin/ffmpeg`) | Convert PNG frame sequence to GIF with palette optimization | Gold standard for video/GIF conversion; `palettegen`+`paletteuse` filters produce high-quality GIFs |
| ImageMagick convert | system (confirmed present: `/usr/bin/convert`) | Alternative/fallback GIF assembly; PNG optimization | Reliable for GIF from frames; `-coalesce -layers Optimize` reduces file size |
| uvicorn | already in `examples` group | Serve FastAPI demo app during capture | Already declared as project dependency |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| gifsicle | not installed | GIF frame optimization | Not available; skip; ffmpeg palette approach is sufficient |
| Pillow | optional | Resize/crop PNG screenshots | Only needed if ffmpeg resize isn't sufficient |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Playwright | Selenium | Selenium requires separate WebDriver binary management; Playwright bundles browsers; Playwright sync API is simpler for a one-shot script |
| ffmpeg palette GIF | ImageMagick only | Both available; ffmpeg produces smaller, smoother GIFs; ImageMagick is adequate fallback |
| repo `docs/` folder | `assets/` folder | Both work; `docs/` already exists in this project (analysis.md, plan.md, etc.); subfolder avoids top-level clutter |

### Installation

```bash
# Add to pyproject.toml screenshots group
uv add --group screenshots playwright

# Install Chromium browser binary
uv run --group screenshots playwright install chromium
```

---

## Architecture Patterns

### Recommended Asset Structure

```
docs/
├── screenshots/
│   ├── routes-home.png          # Hero screenshot (routes home page)
│   └── request-detail-sql.png  # Detail screenshot (SQL tab)
├── demo/
│   └── demo.gif                 # Demo walkthrough GIF
└── announcements/
    ├── reddit.md                # r/Python, r/flask, r/FastAPI post
    ├── x-thread.md              # X thread (3-5 tweets)
    └── hacker-news.md           # Show HN submission
```

### Pattern 1: Scripted Playwright Screenshot Capture

**What:** A single Python script starts uvicorn in a subprocess, drives Chromium to the correct pages, waits for Alpine.js content to render, captures PNG screenshots, then tears down.

**When to use:** Any reproducible screenshot capture — re-runnable after UI changes.

**Key script skeleton:**

```python
# scripts/capture_assets.py
import subprocess, time, asyncio
from playwright.sync_api import sync_playwright

SERVER = "http://127.0.0.1:8765"

def main():
    # Start demo server on a fixed port to avoid conflicts
    server = subprocess.Popen([
        "uv", "run", "--group", "examples",
        "uvicorn", "examples.fastapi.demo_fastapi:app",
        "--host", "127.0.0.1", "--port", "8765"
    ])
    time.sleep(2)  # wait for server startup

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        # Seed data: hit a few routes first so the UI shows realistic data
        for path in ["/books", "/books/1", "/books/duplicates", "/books/slow", "/slow"]:
            page.goto(f"{SERVER}{path}")

        # Screenshot 1: routes home
        page.goto(f"{SERVER}/flowsurgeon")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="docs/screenshots/routes-home.png", full_page=False)

        # Screenshot 2: request detail SQL tab
        # Navigate to a /books/slow request (has slow + dup badges)
        page.goto(f"{SERVER}/flowsurgeon")
        page.wait_for_load_state("networkidle")
        # Click first route row that has data
        page.locator(".tr:not(.tr-no-traffic)").first.click()
        page.wait_for_load_state("networkidle")
        # Click SQL tab
        page.locator(".subnav-item", has_text="SQL").click()
        page.screenshot(path="docs/screenshots/request-detail-sql.png", full_page=False)

        browser.close()
    server.terminate()
```

### Pattern 2: GIF from PNG Frame Sequence via ffmpeg

**What:** Playwright captures a sequence of PNG frames at regular intervals during a scripted walkthrough. ffmpeg converts them to a palette-optimized GIF.

**Two-pass ffmpeg palette GIF (HIGH quality, smaller file):**

```bash
# Pass 1: generate palette
ffmpeg -framerate 10 -i docs/demo/frames/frame_%04d.png \
  -vf "scale=1280:-1:flags=lanczos,palettegen=max_colors=256" \
  docs/demo/palette.png

# Pass 2: produce GIF using palette
ffmpeg -framerate 10 -i docs/demo/frames/frame_%04d.png \
  -i docs/demo/palette.png \
  -lavfi "scale=1280:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5" \
  docs/demo/demo.gif
```

**Target specs:**
- Width: 1280px (matches screenshot width; GitHub README max display ~860px but source at 1280 is fine)
- Frame rate: 8-10 fps — smooth enough, keeps file size manageable
- Duration: 20-30 seconds → 160-300 frames at 10fps
- Expected file size: 2-6 MB at these settings (acceptable for GitHub README)

### Pattern 3: Frame Capture During GIF Walkthrough

**What:** During the GIF walkthrough, Playwright screenshots each "moment" manually rather than using a video recorder — gives full control over timing and pauses.

```python
frame_num = 0

def capture_frame(page, frames_dir, count=10):
    """Capture `count` identical frames to hold on current state."""
    global frame_num
    for _ in range(count):
        page.screenshot(path=f"{frames_dir}/frame_{frame_num:04d}.png")
        frame_num += 1

# Walkthrough:
# 1. Routes home — hold 2s (20 frames at 10fps)
page.goto(f"{SERVER}/flowsurgeon")
page.wait_for_load_state("networkidle")
capture_frame(page, frames_dir, count=20)

# 2. Click a route with data
page.locator(".tr:not(.tr-no-traffic)").first.click()
page.wait_for_load_state("networkidle")
capture_frame(page, frames_dir, count=15)

# 3. SQL tab — slow/dup badges visible
page.locator(".subnav-item", has_text="SQL").click()
capture_frame(page, frames_dir, count=25)
```

### Pattern 4: README Image Replacement

**Current state (lines 2, 17-19 in README.md):**
- Line 2: logo from dev.to S3 — replace with repo-relative path if logo is saved locally, or remove if no local logo
- Lines 17-19: hero screenshot from dev.to S3 — replace with `docs/screenshots/routes-home.png`

**Replace pattern:**
```html
<!-- Before -->
<img src="https://dev-to-uploads.s3.amazonaws.com/uploads/articles/ztt5...png" alt="Home Screen">

<!-- After -->
<img src="docs/screenshots/routes-home.png" alt="FlowSurgeon routes home page" width="900">
```

**Debug UI section addition (after line 277):**
```html
<div align="center">
  <img src="docs/screenshots/request-detail-sql.png" alt="Request detail SQL tab with slow and dup badges" width="900">
  <br>
  <img src="docs/demo/demo.gif" alt="FlowSurgeon demo walkthrough" width="900">
</div>
```

### Pattern 5: Announcement Post Structure

**Reddit (r/Python, r/flask, r/FastAPI) — long-form:**
- Title: "Show r/Python: FlowSurgeon — django-debug-toolbar for everyone (FastAPI + Flask)"
- Body: problem → solution → screenshot/GIF embed → quick start code snippet → links
- Length: 300-500 words; code blocks; genuine tone

**Hacker News (Show HN) — concise:**
- Title: "Show HN: FlowSurgeon – django-debug-toolbar for Flask and FastAPI"
- Body: 2-3 sentences max; link to GitHub; let the UI screenshots speak
- No markdown (HN renders plain text)

**X thread — punchy:**
- Tweet 1: hook + screenshot
- Tweet 2: one-line install
- Tweet 3: GIF walkthrough
- Tweet 4: link + call to action

### Anti-Patterns to Avoid

- **Capturing screenshots before seeding data:** The routes home page shows "No requests" for routes with no traffic — must hit the demo routes first so stats appear (count, duration, status)
- **Not waiting for Alpine.js to render:** Alpine.js drives the method filter toggle and x-show directives; `page.wait_for_load_state("networkidle")` is required after navigation
- **Using the default demo port (8000) during capture:** The FastAPI demo runs on 8000 by default; if a user already has it running, port collision. Script should use a non-standard port (e.g., 8765)
- **Running capture script without the `examples` group:** The demo app requires fastapi, sqlalchemy, uvicorn which are in the `examples` dependency group
- **GIF without palette generation:** Default ffmpeg GIF conversion produces 256-color banding; two-pass palette approach is required for a visually acceptable result
- **External image hosting:** dev.to S3 URLs can 404 — all images must be in-repo

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Browser screenshot capture | Custom HTTP + HTML-to-image library | Playwright | Playwright renders actual CSS, Alpine.js, dark theme correctly; custom solutions won't execute JS |
| GIF from PNG frames | Python `PIL.Image` GIF encoder | ffmpeg two-pass palette | PIL GIF encoder produces large, low-quality output; ffmpeg palette approach is the standard |
| Demo server lifecycle | Manual socket checking | `subprocess.Popen` + `time.sleep(2)` + `server.terminate()` in `finally` | Simple, reliable for a one-shot script |

---

## Common Pitfalls

### Pitfall 1: Alpine.js State Not Rendered When Screenshotting

**What goes wrong:** Screenshot shows the loading state or wrong tab content; `x-cloak` hides elements that should be visible.
**Why it happens:** Playwright's `wait_for_load_state("networkidle")` fires before Alpine.js finishes evaluating `x-data` and `x-show` directives.
**How to avoid:** After navigation, add `page.wait_for_timeout(500)` or wait for a specific visible element using `page.wait_for_selector(".tr:not(.tr-no-traffic)")`.
**Warning signs:** Screenshots show empty containers or wrong tab.

### Pitfall 2: No Traffic Data on Routes Home

**What goes wrong:** Routes home shows all rows with "No requests" in muted style — unimpressive screenshot.
**Why it happens:** Fresh demo server database has no request history.
**How to avoid:** Before capturing screenshots, make HTTP requests to all demo routes to seed data. Use `page.goto()` to each route or `requests.get()` in the capture script.

### Pitfall 3: GIF File Too Large for GitHub README

**What goes wrong:** GIF is 15-30 MB; GitHub renders it slowly or fails to load inline.
**Why it happens:** High frame rate, no palette optimization, large canvas.
**How to avoid:** Cap width at 1280px; use 8-10 fps; use two-pass ffmpeg palette; target <8 MB. Test by loading the raw GitHub URL in a browser.
**Warning signs:** GIF file >10 MB after conversion.

### Pitfall 4: Dark Theme Not Rendering in Headless Browser

**What goes wrong:** Chromium uses light mode by default; screenshots show light-mode fallback if `@media (prefers-color-scheme: light)` is active.
**Why it happens:** The project added light mode via `@media (prefers-color-scheme: light)` in Phase 3.1. Headless Chromium may default to light.
**How to avoid:** Force dark color scheme in Playwright: `page = browser.new_page(color_scheme="dark")`.
**Warning signs:** Screenshot background is white/light instead of the dark design.

### Pitfall 5: Demo Script Leaves Zombie Processes

**What goes wrong:** `uvicorn` subprocess left running after script error; next run fails with port-in-use error.
**Why it happens:** Unhandled exception before `server.terminate()`.
**How to avoid:** Use `try/finally` to guarantee `server.terminate()` and `server.wait()` are always called.

### Pitfall 6: Logo Image URL Also Points to dev.to

**What goes wrong:** Logo at README line 2 is also dev.to-hosted (`4ulii4nulch2u8qopdec.png`). It will still 404 if dev.to clears the S3 bucket.
**How to avoid:** Either save the logo locally as `docs/screenshots/logo.png` or remove the `<img>` logo entirely; the `<h1>FlowSurgeon</h1>` heading is sufficient.

---

## Code Examples

Verified patterns based on current project templates and system tools:

### Playwright Install in uv

```toml
# pyproject.toml addition
[dependency-groups]
screenshots = ["playwright>=1.40"]
```

```bash
uv sync --group screenshots
uv run --group screenshots playwright install chromium
```

### Force Dark Mode in Playwright

```python
page = browser.new_page(
    viewport={"width": 1280, "height": 800},
    color_scheme="dark",
)
```

### Wait for Alpine.js-rendered Content

```python
page.goto(f"{SERVER}/flowsurgeon")
page.wait_for_load_state("networkidle")
page.wait_for_selector(".tr", timeout=5000)  # wait for route rows
page.wait_for_timeout(300)                   # extra settle time for Alpine
```

### Two-Pass ffmpeg Palette GIF

```bash
mkdir -p docs/demo/frames

# After frames are captured as docs/demo/frames/frame_0000.png etc.
ffmpeg -y -framerate 10 -i docs/demo/frames/frame_%04d.png \
  -vf "scale=1280:-1:flags=lanczos,palettegen=max_colors=256:stats_mode=diff" \
  docs/demo/palette.png

ffmpeg -y -framerate 10 -i docs/demo/frames/frame_%04d.png \
  -i docs/demo/palette.png \
  -lavfi "fps=10,scale=1280:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" \
  docs/demo/demo.gif
```

### README Hero Image Block (replacement)

```html
<div align="center">
    <img src="docs/screenshots/routes-home.png" alt="FlowSurgeon routes home page" width="900">
</div>
```

### README Debug UI Section Addition

```html
<div align="center">
  <img src="docs/screenshots/request-detail-sql.png" alt="Request detail — SQL tab with slow and dup badges" width="900">
</div>

<div align="center">
  <img src="docs/demo/demo.gif" alt="FlowSurgeon walkthrough" width="900">
</div>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual browser screenshots via OS screenshot tool | Playwright scripted capture | ~2022 | Reproducible, consistent framing, automatable |
| Screen recording + hand-edited GIF | Playwright frame capture + ffmpeg palette | ~2021 | No manual editing; deterministic timing |
| External image hosting (Imgur, dev.to S3) | In-repo images | Best practice since GitHub LFS | No external dependencies; images version with code |

**Deprecated/outdated:**
- `selenium` + ChromeDriver for scripted screenshots: replaced by Playwright which bundles browser binaries and has cleaner Python API
- `imageio` Python GIF writing: produces larger files than ffmpeg; not the current standard for high-quality GIF

---

## Open Questions

1. **Logo image: save locally or drop?**
   - What we know: README line 2 references a dev.to-hosted logo PNG (`4ulii4nulch2u8qopdec.png`)
   - What's unclear: Whether there is a canonical SVG/PNG logo in the repo anywhere
   - Recommendation: Check `src/flowsurgeon/ui/` for any logo asset; if none found, remove the `<img>` tag and keep only the `<h1>` heading

2. **GIF walkthrough: which specific request to click into?**
   - What we know: Routes home shows all routes; clicking a route goes to detail; SQL tab requires a request that has SQL queries
   - What's unclear: Which route row provides the most visually compelling SQL tab (slow + dup badges together)
   - Recommendation: Navigate to `/books/slow` before the GIF walkthrough (it triggers a slow query), then click that route row to get a detail page with the `slow` badge visible

3. **`x-cloak` visibility on first render**
   - What we know: The SQL tab panel has `x-cloak` on its container; the Details tab is shown by default
   - What's unclear: Whether clicking the SQL subnav item in Playwright triggers Alpine's `@click.prevent` handler correctly
   - Recommendation: In the capture script, use `page.locator(".subnav-item", has_text="SQL").click()` and add `page.wait_for_timeout(300)` before screenshotting

---

## Validation Architecture

nyquist_validation is enabled in `.planning/config.json`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run --group dev pytest tests/ -x -q` |
| Full suite command | `uv run --group dev pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANMT-01 | Screenshot PNG files exist in docs/screenshots/ with correct names | smoke (file existence) | `python -c "import os; assert os.path.exists('docs/screenshots/routes-home.png'); assert os.path.exists('docs/screenshots/request-detail-sql.png')"` | ❌ Wave 0 |
| ANMT-01 | README no longer references dev.to URLs | smoke (content check) | `python -c "assert 'dev-to-uploads.s3.amazonaws.com' not in open('README.md').read()"` | ❌ Wave 0 |
| ANMT-01 | README references new repo-relative image paths | smoke (content check) | `python -c "assert 'docs/screenshots/routes-home.png' in open('README.md').read()"` | ❌ Wave 0 |
| ANMT-02 | GIF file exists in docs/demo/ | smoke (file existence) | `python -c "import os; assert os.path.exists('docs/demo/demo.gif')"` | ❌ Wave 0 |
| ANMT-02 | Announcement files exist | smoke (file existence) | `python -c "import os; [assert os.path.exists(f) for f in ['docs/announcements/reddit.md','docs/announcements/x-thread.md','docs/announcements/hacker-news.md']]"` | ❌ Wave 0 |

**Note:** ANMT-01 and ANMT-02 are primarily asset-production requirements. The "automated tests" are lightweight file existence and README content checks — not behavior tests. No pytest test files need to be created; these are inline one-liners suitable as verification commands in the plan.

### Sampling Rate

- **Per task commit:** inline assertion commands above
- **Per wave merge:** `uv run --group dev pytest tests/ -x -q` (existing unit tests must remain green)
- **Phase gate:** All file existence checks pass + full pytest suite green

### Wave 0 Gaps

- [ ] `scripts/capture_assets.py` — GIF/screenshot capture script (not a test file; a production script)
- [ ] `pyproject.toml` — add `screenshots` dependency group with `playwright`
- [ ] `docs/screenshots/` directory — created by capture script
- [ ] `docs/demo/` directory — created by capture script
- [ ] `docs/announcements/` directory — created manually

*(No new pytest test files required; existing test infrastructure covers all source code. Phase 4 verifies asset existence via inline file checks.)*

---

## Sources

### Primary (HIGH confidence)

- Playwright Python docs (playwright.dev) — sync API, `new_page(color_scheme=)`, `wait_for_load_state`, `screenshot()`
- ffmpeg documentation — `palettegen`, `paletteuse`, `-framerate`, palette-based GIF encoding
- Project source: `src/flowsurgeon/ui/templates/home.html`, `detail.html`, `partials/detail_sql.html` — CSS class names for Playwright selectors
- Project source: `examples/fastapi/demo_fastapi.py` — demo routes and startup command
- `README.md` — current image placement pattern, dev.to URLs to replace (lines 2, 17-19)
- `pyproject.toml` — dependency group structure, uv invocation pattern

### Secondary (MEDIUM confidence)

- ffmpeg two-pass GIF palette approach: widely documented in ffmpeg wiki and open-source tooling; consistent with ImageMagick fallback available on this machine
- Playwright `color_scheme="dark"` parameter: standard Playwright API for emulating `prefers-color-scheme`

### Tertiary (LOW confidence)

- GIF file size estimates (2-6 MB): based on typical 1280px/10fps GIF with palette optimization; actual size depends on animation complexity and content

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — ffmpeg and ImageMagick confirmed present; Playwright is the current standard for scripted browser capture
- Architecture: HIGH — based on direct inspection of project templates, README, and demo app
- Pitfalls: HIGH — dark mode pitfall directly verified from Phase 3.1 STATE.md decision; Alpine.js timing verified from template inspection
- Announcement structure: MEDIUM — platform conventions are well-known but post tone is Claude's discretion

**Research date:** 2026-03-16
**Valid until:** 2026-06-16 (stable domain — Playwright API and ffmpeg GIF encoding do not change frequently)
