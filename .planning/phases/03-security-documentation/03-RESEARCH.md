# Phase 3: Security Documentation - Research

**Researched:** 2026-03-16
**Domain:** Technical writing — README.md security section, GitHub-flavored Markdown
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Doc placement & structure**
- Dedicated "Security" section in README.md (not a separate SECURITY.md)
- Positioned right after Quick Start section — devs see it immediately after setup
- Consolidate all scattered security mentions from other README sections into this one section
- Subsection order: Kill Switch → Allowed Hosts → Header Redaction → Database File (risk-priority order)

**Tone & audience**
- Friendly but clear — informative, not scary. "FlowSurgeon is a development tool. Here's how to keep it safe."
- Primary audience: solo devs and small teams adding FlowSurgeon to their projects
- "Do this" examples only — no anti-pattern examples
- Brief "why" + "how" for each topic: one sentence explaining the risk, then the config/code

**Coverage depth**
- Consistent "defaults + customize" depth across all subsections (~5 lines each + code block)
- Kill Switch: fully documented in Security section (not just a cross-reference), show env var and code approaches
- Allowed Hosts: state defaults (127.0.0.1, ::1, localhost), show how to add hosts
- Header Redaction: list default redacted headers (Authorization, Cookie, Set-Cookie), show how to add custom ones
- Database File: one sentence why + ready-to-copy .gitignore entry

**Quick Start warning**
- GitHub-flavored `[!WARNING]` blockquote callout
- Positioned after `pip install` command but before the code example
- Links to Security section for details — keeps Quick Start concise
- Text: "FlowSurgeon is a development tool. Do not enable in production. See Security for details."

### Claude's Discretion
- Exact wording of each subsection's "why" sentence
- Whether to include `enabled=True` in code example alongside env var approach
- How to handle the existing scattered security mentions when consolidating (remove vs shorten to one-liner with link)
- Markdown formatting details within the Security section

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SDOC-01 | Security section documenting allowed_hosts, header redaction, env var kill switch | Covered by: existing code defaults in config.py, current README structure analysis, GFM callout syntax |
| SDOC-02 | Production warning: "FlowSurgeon is a development tool. Do not enable in production." | Covered by: GFM `[!WARNING]` alert syntax, Quick Start section position (line 48) |
| SDOC-03 | Guidance on .gitignore for flowsurgeon.db | Covered by: .gitignore analysis (no current flowsurgeon.db entry), db_path default value from config.py |
</phase_requirements>

## Summary

This phase is pure documentation work — editing README.md to add a Security section and a production warning callout in Quick Start. No new Python code, no new files. The scope is narrow: two README edits, guided entirely by decisions already locked in CONTEXT.md.

The research goal is to verify the exact technical facts (config field names, default values, actual behavior) so documentation is accurate, and to confirm GitHub-flavored Markdown syntax for the `[!WARNING]` callout renders correctly on both GitHub and PyPI.

The existing README already has security content scattered across lines 33–34 (Features), 137–153 (Configuration), 210 and 244 (environment variables section). The plan must consolidate these into one Security section without losing coverage.

**Primary recommendation:** Write the Security section directly against `src/flowsurgeon/core/config.py` as the source of truth, not against the README's existing Configuration block, which uses different field names (`strip_sensitive_headers` in code vs `redact_headers` in prose).

## Technical Facts Verified

These are the authoritative values from `src/flowsurgeon/core/config.py`:

| Config Field | Type | Default Value | Security Relevance |
|---|---|---|---|
| `enabled` | `bool` | `False` (env: `FLOWSURGEON_ENABLED`) | Kill switch — disabled by default |
| `allowed_hosts` | `list[str]` | `["127.0.0.1", "::1", "localhost"]` | Restricts which clients see the debug panel |
| `db_path` | `str` | `"flowsurgeon.db"` | File written in project root — needs .gitignore |
| `strip_sensitive_headers` | `list[str]` | `["authorization", "cookie", "set-cookie"]` | Headers redacted before storage |

**Discrepancy to fix (HIGH confidence):** The README Configuration block at line 153 shows `strip_sensitive_headers=["authorization", "cookie", "set-cookie"]` but the Features list at line 33 mentions "Authorization, Cookie, Set-Cookie" (title case). The source of truth is config.py: field name is `strip_sensitive_headers`, values are lowercase strings. The Security section should show the correct lowercase field name.

**Env var behavior (from config.py):** `FLOWSURGEON_ENABLED` accepts `"1"`, `"true"`, or `"yes"` (case-insensitive). The env section at line 244 only shows `FLOWSURGEON_ENABLED=1` — this is sufficient.

**`flowsurgeon.db` in .gitignore:** The project's own `.gitignore` currently has `*.db*` on line matching Django stuff (`db.sqlite3`), and a separate `*.db*` glob pattern. Checking the actual .gitignore: the pattern `*.db*` is present under the Django section. However, the SDOC-03 requirement is about guiding *users* to add `flowsurgeon.db` to *their* project's `.gitignore` — not the FlowSurgeon repo's own `.gitignore`. This distinction must be clear in the documentation: the `.gitignore` entry is for users' own projects.

## README Structure Analysis

Current section order in README.md:
1. Header / badges (lines 1–13)
2. Features (line 21)
3. Installation (line 36)
4. Quick start (line 48) — ASGI + Flask subsections
5. SQL query tracking (line 92)
6. Configuration (line 131)
7. Debug UI (line 172)
8. Running the examples (line 215)
9. Environment variable (line 240)
10. License (line 249)

**Decision from CONTEXT.md:** Security goes immediately after Quick Start. That means between line ~91 (end of Flask WSGI example) and line 92 (## SQL query tracking).

**The "Environment variable" section (lines 240–248)** currently documents the kill switch in isolation. Per the locked decision to consolidate scattered security mentions into the Security section, this section will either be removed or reduced to a one-liner cross-reference.

## GitHub-Flavored Markdown Alert Syntax

The `[!WARNING]` callout syntax is supported in GitHub-rendered markdown and renders on PyPI via the readme-renderer library (which PyPI uses).

**Correct syntax (HIGH confidence — GFM spec):**
```markdown
> [!WARNING]
> FlowSurgeon is a development tool. Do not enable in production. See [Security](#security) for details.
```

This renders as a yellow/orange warning box on GitHub and PyPI. The anchor `#security` works when the section header is `## Security` — GitHub auto-generates lowercase, hyphenated anchors from heading text.

**CONTEXT.md confirms:** "GitHub `[!WARNING]` callout renders prominently on both GitHub and PyPI — good for visibility."

**Placement:** After the `pip install flowsurgeon` block in Installation, before the Quick Start code examples. Per CONTEXT.md: "Positioned after `pip install` command but before the code example."

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Warning callout styling | Custom HTML `<div>` with inline CSS | GFM `[!WARNING]` alert | Renders natively on GitHub and PyPI; no HTML required |
| Security content | New `SECURITY.md` file | In-README section | Locked decision; keeps docs in one place for a library at this stage |

## Architecture Patterns

### README Section Template

Each Security subsection follows this locked pattern:
```
### [Subsection Name]

[One sentence: what it does and why it matters.]

[Code block showing: defaults first, then how to customize.]
```

### Subsection Order (locked)
1. Kill Switch (highest risk: accidental production enable)
2. Allowed Hosts (network access restriction)
3. Header Redaction (data storage concern)
4. Database File (data at rest / source control concern)

### Handling Existing Scattered Mentions

Three locations to update when consolidating:
- **Features list (lines 33–34):** Keep as-is — these are feature bullet points, not documentation. The Security section supplements them.
- **Configuration block (lines 131–170):** The `strip_sensitive_headers` comment is factual config reference; keep it. The Security section adds narrative context.
- **Environment variable section (lines 240–248):** This overlaps directly with the Kill Switch subsection. Reduce to one-liner pointing to Security, or remove entirely and let Security section carry the content. Claude's discretion per CONTEXT.md.

## Common Pitfalls

### Pitfall 1: Wrong field name in docs
**What goes wrong:** Documentation shows `redact_headers` (made up) or inconsistent casing instead of the actual `strip_sensitive_headers` field name.
**Why it happens:** README prose and config.py use slightly different terminology.
**How to avoid:** Copy field names directly from `src/flowsurgeon/core/config.py`, not from existing README prose.
**Warning signs:** If the Security section's code block cannot be copy-pasted into a `Config()` call and work, the field name is wrong.

### Pitfall 2: Incorrect header value casing in docs
**What goes wrong:** Documentation shows `Authorization`, `Cookie` (title case) instead of `"authorization"`, `"cookie"` (lowercase).
**Why it happens:** HTTP header names are case-insensitive in the protocol, but the config.py stores and matches them lowercase. The Features section at line 33 uses title case for readability but the actual config values are lowercase.
**How to avoid:** The code block showing `strip_sensitive_headers` customization must use lowercase strings matching config.py.

### Pitfall 3: .gitignore guidance aimed at wrong audience
**What goes wrong:** Telling users to add `flowsurgeon.db` to the FlowSurgeon project's own `.gitignore` instead of to their application project's `.gitignore`.
**Why it happens:** The FlowSurgeon repo itself has `*.db*` in its .gitignore, creating confusion.
**How to avoid:** Phrase guidance as "Add to your project's `.gitignore`" with clear copy-pasteable snippet.

### Pitfall 4: Anchor link breaks on PyPI
**What goes wrong:** `[Security](#security)` in the Quick Start warning doesn't navigate anywhere on PyPI.
**Why it happens:** PyPI uses readme-renderer, which strips anchor links in some configurations.
**How to avoid:** The warning text works without the link being functional — it still communicates the message. Keep the link for GitHub; if it breaks on PyPI, it degrades gracefully to plain text.

## Code Examples

Verified directly from `src/flowsurgeon/core/config.py`:

### Kill Switch — env var approach
```bash
# Enable per-session without modifying code
FLOWSURGEON_ENABLED=1 uvicorn myapp:app
```

### Kill Switch — code approach
```python
from flowsurgeon import FlowSurgeon, Config

app = FlowSurgeon(
    _app,
    config=Config(enabled=True),
)
```

### Allowed Hosts — showing defaults and customization
```python
from flowsurgeon import Config

# Default: localhost only
Config(allowed_hosts=["127.0.0.1", "::1", "localhost"])

# Add a VM or container IP
Config(allowed_hosts=["127.0.0.1", "::1", "localhost", "192.168.1.50"])
```

### Header Redaction — showing defaults and customization
```python
from flowsurgeon import Config

# Default: Authorization, Cookie, Set-Cookie are redacted
Config(strip_sensitive_headers=["authorization", "cookie", "set-cookie"])

# Add a custom token header
Config(strip_sensitive_headers=["authorization", "cookie", "set-cookie", "x-api-key"])
```

### Database File — .gitignore entry
```
# .gitignore
flowsurgeon.db
```

### Quick Start Warning Callout
```markdown
> [!WARNING]
> FlowSurgeon is a development tool. Do not enable in production. See [Security](#security) for details.
```

## Validation Architecture

nyquist_validation is enabled in .planning/config.json.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `.venv/bin/pytest tests/ -q` |
| Full suite command | `.venv/bin/pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SDOC-01 | Security section present in README with correct content | manual-only | N/A | N/A |
| SDOC-02 | `[!WARNING]` callout present in Quick Start | manual-only | N/A | N/A |
| SDOC-03 | .gitignore guidance present in README | manual-only | N/A | N/A |

**Justification for manual-only:** This phase produces only documentation changes to README.md. There is no executable code to test. Validation is a manual read of the README to confirm presence of required content. Automated tests for README content (e.g., a Python script checking string presence) would be over-engineering for a single-file edit.

The existing 86-test suite covers the underlying security behaviors (header redaction at line 118–128 in test_wsgi.py, allowed_hosts at line 136 in test_asgi.py). These tests confirm the documented behavior actually works — no new tests needed.

### Sampling Rate
- **Per task commit:** Manual review of README.md changes
- **Per wave merge:** `.venv/bin/pytest tests/ -q` (confirms underlying security code still works)
- **Phase gate:** README reviewed against all three SDOC requirements before `/gsd:verify-work`

### Wave 0 Gaps
None — existing test infrastructure covers all phase requirements. Documentation phase requires no new test files.

## Open Questions

1. **Whether to remove or redirect the "Environment variable" section**
   - What we know: CONTEXT.md flags this as Claude's discretion ("remove vs shorten to one-liner with link")
   - What's unclear: Whether removing it entirely breaks any links from external sources
   - Recommendation: Shorten to a one-liner ("See [Security](#security) → Kill Switch") rather than remove. Lower risk, same outcome.

2. **Whether `enabled=True` code example should appear in Security section**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - What's unclear: Whether showing `enabled=True` in the Security section creates confusion (it already appears in Quick Start)
   - Recommendation: Include both env var and code approaches in Kill Switch subsection — mirrors the approved subsection format from CONTEXT.md ("show env var and code approaches")

## Sources

### Primary (HIGH confidence)
- `src/flowsurgeon/core/config.py` — authoritative source for all field names, defaults, and env var names
- `README.md` — current section structure, line numbers, existing security mentions
- `.planning/phases/03-security-documentation/03-CONTEXT.md` — locked decisions and scope

### Secondary (MEDIUM confidence)
- GitHub GFM alert syntax: `[!WARNING]`, `[!NOTE]` etc. are standard GitHub-flavored Markdown alerts (documented at docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts)
- PyPI readme-renderer: supports GFM alert rendering as of readme-renderer 42.0+ (used by current PyPI)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Technical facts (config defaults): HIGH — read directly from config.py source
- README structure: HIGH — read directly from README.md
- GFM `[!WARNING]` syntax: HIGH — established GFM spec, confirmed by CONTEXT.md
- PyPI rendering compatibility: MEDIUM — based on known readme-renderer support

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable — pure docs, no moving ecosystem parts)
