# Phase 3: Security Documentation - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Document FlowSurgeon's security posture so users understand it is a development tool and how to keep it safe. Covers `allowed_hosts`, header redaction, `FLOWSURGEON_ENABLED` kill switch, and `.gitignore` guidance. All content lives in README.md — no new pages, no new Python logic.

</domain>

<decisions>
## Implementation Decisions

### Doc placement & structure
- Dedicated "Security" section in README.md (not a separate SECURITY.md)
- Positioned right after Quick Start section — devs see it immediately after setup
- Consolidate all scattered security mentions from other README sections into this one section
- Subsection order: Kill Switch → Allowed Hosts → Header Redaction → Database File (risk-priority order)

### Tone & audience
- Friendly but clear — informative, not scary. "FlowSurgeon is a development tool. Here's how to keep it safe."
- Primary audience: solo devs and small teams adding FlowSurgeon to their projects
- "Do this" examples only — no anti-pattern examples
- Brief "why" + "how" for each topic: one sentence explaining the risk, then the config/code

### Coverage depth
- Consistent "defaults + customize" depth across all subsections (~5 lines each + code block)
- Kill Switch: fully documented in Security section (not just a cross-reference), show env var and code approaches
- Allowed Hosts: state defaults (127.0.0.1, ::1, localhost), show how to add hosts
- Header Redaction: list default redacted headers (Authorization, Cookie, Set-Cookie), show how to add custom ones
- Database File: one sentence why + ready-to-copy .gitignore entry

### Quick Start warning
- GitHub-flavored `[!WARNING]` blockquote callout
- Positioned after `pip install` command but before the code example
- Links to Security section for details — keeps Quick Start concise
- Text: "FlowSurgeon is a development tool. Do not enable in production. See Security for details."

### Claude's Discretion
- Exact wording of each subsection's "why" sentence
- Whether to include `enabled=True` in code example alongside env var approach
- How to handle the existing scattered security mentions when consolidating (remove vs shorten to one-liner with link)
- Markdown formatting details within the Security section

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/config.py`: Defines all security-relevant config fields — `enabled`, `allowed_hosts`, `db_path`, `redact_headers` with their defaults
- README.md already has inline security mentions: line 33 (header redaction), line 34 (env var), lines 137-152 (config example with allowed_hosts, redact_headers)

### Established Patterns
- README uses standard GitHub markdown with code blocks, bullet lists, and section headers
- Config examples show both ASGI and WSGI patterns
- `FLOWSURGEON_ENABLED` env var already documented in Quick Start run commands (line 210, 244)

### Integration Points
- README.md is the sole documentation target — no docs site exists yet (DOCS-01 is v2)
- Phase 4 (Announcement Assets) depends on this phase — screenshots/demo should show the final documented state
- Existing README structure: Features → Quick Start → Configuration → (Security goes here) → ...

</code_context>

<specifics>
## Specific Ideas

- GitHub `[!WARNING]` callout renders prominently on both GitHub and PyPI — good for visibility
- The previewed subsection formats were approved: each follows "one sentence context → code block" pattern
- Security section should feel like a natural part of the README, not a bolted-on compliance doc

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-security-documentation*
*Context gathered: 2026-03-16*
