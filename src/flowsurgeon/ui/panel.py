from __future__ import annotations

import importlib.resources
from html import escape

from flowsurgeon.core.records import RequestRecord


def _load_asset(name: str) -> str:
    pkg = importlib.resources.files("flowsurgeon.ui.assets")
    return (pkg / name).read_text(encoding="utf-8")


def _status_badge_class(status: int) -> str:
    if status < 400:
        return "fs-ok"
    if status < 500:
        return "fs-warn"
    return "fs-err"


def render_panel(record: RequestRecord, debug_route: str) -> str:
    """Return the HTML fragment for the inline debug panel."""
    css = _load_asset("panel.css")
    js = _load_asset("panel.js")

    badge_cls = _status_badge_class(record.status_code)
    qs = f"?{escape(record.query_string)}" if record.query_string else ""

    req_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{escape(v)}</td></tr>"
        for k, v in record.request_headers.items()
    )
    resp_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{escape(v)}</td></tr>"
        for k, v in record.response_headers.items()
    )

    return f"""
<style>{css}</style>
<div id="fs-root">
  <div id="fs-toolbar">
    <span class="fs-title">FlowSurgeon</span>
    <span class="fs-badge {badge_cls}">{record.status_code}</span>
    <span class="fs-badge">{record.duration_ms:.1f} ms</span>
    <span class="fs-badge">{escape(record.method)}</span>
    <a class="fs-link" href="{escape(debug_route)}" target="_blank">history</a>
    <button id="fs-toggle" title="Toggle panel">▼</button>
  </div>
  <div id="fs-body">
    <div class="fs-section">
      <div class="fs-section-title">Request</div>
      <table class="fs-table">
        <tr><td>ID</td><td>{escape(record.request_id)}</td></tr>
        <tr><td>Path</td><td>{escape(record.path)}{qs}</td></tr>
        <tr><td>Client</td><td>{escape(record.client_host)}</td></tr>
        <tr><td>Time</td><td>{record.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</td></tr>
      </table>
    </div>
    <div class="fs-section">
      <div class="fs-section-title">Request Headers</div>
      <table class="fs-table">{req_rows or "<tr><td colspan='2'>—</td></tr>"}</table>
    </div>
    <div class="fs-section">
      <div class="fs-section-title">Response Headers</div>
      <table class="fs-table">{resp_rows or "<tr><td colspan='2'>—</td></tr>"}</table>
    </div>
  </div>
</div>
<script>{js}</script>
"""


def render_history_page(records: list[RequestRecord], debug_route: str) -> str:
    """Return a full HTML page listing recent requests."""
    css = _load_asset("panel.css")

    rows = ""
    for r in records:
        badge_cls = _status_badge_class(r.status_code)
        qs = f"?{escape(r.query_string)}" if r.query_string else ""
        detail_url = f"{escape(debug_route)}/{escape(r.request_id)}"
        rows += f"""
        <tr>
          <td>{r.timestamp.strftime("%H:%M:%S")}</td>
          <td><span class="fs-badge">{escape(r.method)}</span></td>
          <td><a class="fs-link" href="{detail_url}">{escape(r.path)}{qs}</a></td>
          <td><span class="fs-badge {badge_cls}">{r.status_code}</span></td>
          <td>{r.duration_ms:.1f} ms</td>
        </tr>"""

    if not rows:
        rows = "<tr><td colspan='5' style='color:#6c7086;padding:8px'>No requests recorded yet.</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>FlowSurgeon — Request History</title>
  <style>
    {css}
    body {{ background: #1e1e2e; color: #cdd6f4; margin: 0; padding: 20px; }}
    #fs-root {{ position: static; width: 100%; max-height: unset; border: 1px solid #313244;
                border-radius: 6px; box-shadow: none; }}
    h1 {{ color: #89b4fa; font-family: ui-monospace, monospace; font-size: 16px; margin: 0 0 16px; }}
    table.history {{ width: 100%; border-collapse: collapse; }}
    table.history th {{
      text-align: left; padding: 4px 8px; color: #6c7086;
      font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px;
      border-bottom: 1px solid #313244;
    }}
    table.history td {{ padding: 5px 8px; border-bottom: 1px solid #181825; }}
    table.history tr:hover td {{ background: #181825; }}
    .fs-badge {{ display: inline-block; }}
  </style>
</head>
<body>
  <h1>FlowSurgeon — Request History</h1>
  <table class="history">
    <thead>
      <tr>
        <th>Time</th><th>Method</th><th>Path</th><th>Status</th><th>Duration</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""


def render_detail_page(record: RequestRecord, debug_route: str) -> str:
    """Return a full HTML page for a single request detail."""
    css = _load_asset("panel.css")
    badge_cls = _status_badge_class(record.status_code)
    qs = f"?{escape(record.query_string)}" if record.query_string else ""

    req_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{escape(v)}</td></tr>"
        for k, v in record.request_headers.items()
    ) or "<tr><td colspan='2'>—</td></tr>"

    resp_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{escape(v)}</td></tr>"
        for k, v in record.response_headers.items()
    ) or "<tr><td colspan='2'>—</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>FlowSurgeon — {escape(record.request_id)}</title>
  <style>
    {css}
    body {{ background: #1e1e2e; color: #cdd6f4; margin: 0; padding: 20px; }}
    h1 {{ color: #89b4fa; font-family: ui-monospace, monospace; font-size: 16px; margin: 0 0 4px; }}
    .back {{ color: #89b4fa; font-family: ui-monospace, monospace; font-size: 12px;
             text-decoration: none; display: inline-block; margin-bottom: 16px; }}
    .back:hover {{ text-decoration: underline; }}
    .section {{ margin-bottom: 20px; }}
    .section-title {{
      color: #89b4fa; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.8px; font-size: 10px; margin-bottom: 6px;
      border-bottom: 1px solid #313244; padding-bottom: 3px;
      font-family: ui-monospace, monospace;
    }}
    table.fs-table {{ width: 100%; border-collapse: collapse; font-family: ui-monospace, monospace; }}
    table.fs-table td {{ padding: 4px 6px; vertical-align: top; font-size: 12px; }}
    table.fs-table td:first-child {{ color: #6c7086; white-space: nowrap; padding-right: 16px; }}
    .fs-badge {{ display: inline-block; padding: 1px 6px; border-radius: 99px; font-size: 11px;
                 font-family: ui-monospace, monospace; }}
    .fs-ok   {{ background: #a6e3a1; color: #1e1e2e; }}
    .fs-warn {{ background: #f9e2af; color: #1e1e2e; }}
    .fs-err  {{ background: #f38ba8; color: #1e1e2e; }}
  </style>
</head>
<body>
  <a class="back" href="{escape(debug_route)}">&larr; back to history</a>
  <h1>
    <span class="fs-badge">{escape(record.method)}</span>
    {escape(record.path)}{qs}
    <span class="fs-badge {badge_cls}">{record.status_code}</span>
  </h1>

  <div class="section">
    <div class="section-title">Overview</div>
    <table class="fs-table">
      <tr><td>Request ID</td><td>{escape(record.request_id)}</td></tr>
      <tr><td>Timestamp</td><td>{record.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</td></tr>
      <tr><td>Duration</td><td>{record.duration_ms:.2f} ms</td></tr>
      <tr><td>Client</td><td>{escape(record.client_host)}</td></tr>
    </table>
  </div>

  <div class="section">
    <div class="section-title">Request Headers</div>
    <table class="fs-table">{req_rows}</table>
  </div>

  <div class="section">
    <div class="section-title">Response Headers</div>
    <table class="fs-table">{resp_rows}</table>
  </div>
</body>
</html>"""
