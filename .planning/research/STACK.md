# Technology Stack

**Project:** FlowSurgeon v0.6.0 milestone (UI redesign, docs site, CI/CD)
**Researched:** 2026-03-15
**Scope:** This milestone adds docs site, CI/CD polish, and UI redesign to an existing v0.5.0 codebase. No new runtime dependencies are introduced. All additions are dev/docs tooling.

---

## Existing Runtime Stack (Do Not Change)

| Technology | Version (locked) | Purpose | Constraint |
|------------|-----------------|---------|-----------|
| Python | 3.12+ | Runtime | Minimum, test on 3.12 and 3.13 |
| Jinja2 | 3.1.6 | UI template rendering | Only runtime dep; keep it that way |
| SQLite3 | stdlib | Request history storage | No external DB dep |
| Alpine.js | 3.x (bundled) | SPA-like interactivity in debug UI | Bundled inline; no npm/build step |

---

## Documentation Site

### Recommended: MkDocs + Material theme

**Why MkDocs over Sphinx:** MkDocs writes docs in Markdown (which the project already uses for README/CHANGELOG), has a single `mkdocs.yml` config, and deploys to GitHub Pages with one command. Sphinx requires RST or heavy configuration, is aimed at API reference generation from docstrings, and is overkill for a developer tool that needs installation guides and quick-start pages.

**Why Material theme over default MkDocs theme:** Material is the standard for Python OSS projects in 2025 (FastAPI, Typer, SQLModel, Ruff, uv, Pydantic all use it). It provides dark mode out-of-the-box (matches FlowSurgeon's dark UI aesthetic), code tabs, admonition blocks, and search — all without custom CSS.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| mkdocs | >=1.6.0 | Static site generator | Simple Markdown -> HTML, single config file |
| mkdocs-material | >=9.5.0 | Theme | Industry standard for Python OSS docs, dark mode built-in |

**Confidence:** MEDIUM — versions based on training data. Verify current versions on PyPI before pinning.

**Installation:**
```bash
uv add --group docs "mkdocs>=1.6.0" "mkdocs-material>=9.5.0"
```

**Deployment:** GitHub Actions -> `mkdocs gh-deploy --force` publishes to `gh-pages` branch.

### What NOT to use

| Tool | Why Not |
|------|---------|
| Sphinx | RST-first, heavy setup, designed for API autodoc not narrative docs |
| Docusaurus | React/Node.js toolchain — contradicts no-build-step principle |
| ReadTheDocs | Adds external dependency; GitHub Pages is sufficient and free |
| pdoc / pydoc-markdown | Auto-generates from docstrings only — needs installation guides and concept pages |

---

## CI/CD Pipeline

### Existing (already working)

| File | Trigger | What it does |
|------|---------|-------------|
| `.github/workflows/ci.yaml` | push/PR to master | Tests on Python 3.12 and 3.13 using `uv sync --group dev` + `pytest` |
| `.github/workflows/publish.yml` | push tag `v*` | `uv build` -> upload artifact -> `uv publish` via OIDC Trusted Publisher |

### What needs to be added

| Gap | Recommended fix |
|-----|----------------|
| No linting step in CI | Add `ruff check` and `ruff format --check` to `ci.yaml` |
| No docs deployment | Add separate `docs.yml` workflow triggered on push to master |
| No coverage reporting | Add `--cov=src/flowsurgeon` flag to pytest step |

### Linting: Ruff

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| ruff | >=0.5.0 | Linter + formatter | Already configured in pyproject.toml; replaces flake8+black+isort |

**Confidence:** MEDIUM — ruff 0.5+ confirmed from training data. Verify current version.

---

## UI Layer (Server-Rendered Debug Panel)

**No changes to the runtime UI stack.** The existing approach is correct and must remain unchanged per project constraints.

### UI polish approach (shadcn-inspired without React)

shadcn/ui's visual identity is entirely expressible in plain CSS custom properties:

1. Use CSS custom properties (variables) for the color system
2. Define a spacing scale (`--space-1` through `--space-8`)
3. Use `border: 1px solid var(--border)` rather than shadows
4. Use system font stack: `-apple-system, BlinkMacSystemFont, 'Inter', sans-serif`
5. Method badges follow Swagger convention: background color + white text, pill-shaped

**What NOT to introduce:**
- Tailwind CSS — requires a build step (PostCSS)
- Any CSS framework with a CDN link — adds external network dependency
- CSS modules / CSS-in-JS — requires a bundler

---

## Release Packaging

| Item | Current state | Recommendation |
|------|--------------|----------------|
| `pyproject.toml` metadata | Complete | Add `Documentation` URL once docs site is live |
| Build backend | `uv_build>=0.9.17,<0.10.0` | Correct approach |
| CHANGELOG.md | Exists but untracked | Commit it; follow Keep a Changelog format |
| Version bumping | Manual edit | Keep manual for 0.x |
| PyPI badges | In README | Already present |

---

## Full Dependency Group Summary

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.0.0",
    "ruff>=0.5.0",
]
docs = [
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.5.0",
]
examples = [
    "fastapi>=0.135.1",
    "flask>=3.1.3",
    "sqlalchemy>=2.0",
    "uvicorn>=0.41.0",
]
```

---

*Research date: 2026-03-15. Version numbers for mkdocs and ruff marked MEDIUM confidence — verify against PyPI before pinning.*
