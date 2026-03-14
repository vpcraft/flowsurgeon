"""Call-stack profiling utilities for FlowSurgeon.

Uses ``cProfile`` (stdlib) to capture per-function timing for each profiled
request.  Both the WSGI and ASGI middlewares import from this module so the
parse logic lives in one place.

ASGI note: ``cProfile`` measures CPU time while the coroutine is *on-thread*.
I/O-wait time (e.g. awaiting a DB or HTTP call) appears as event-loop
internals rather than in the awaited coroutine's frame.  For CPU-bound
hotspot analysis this is accurate and sufficient.
"""

from __future__ import annotations

import cProfile
import io
import logging
import os
import pstats
import sys
from typing import TYPE_CHECKING

_log = logging.getLogger(__name__)

from flowsurgeon.core.records import ProfileStat

if TYPE_CHECKING:
    from flowsurgeon.core.config import Config


def _short_path(filepath: str, cwd: str) -> str:
    """Return *filepath* relative to *cwd* when possible."""
    if not filepath or filepath.startswith("<"):
        return filepath
    try:
        return os.path.relpath(filepath, cwd)
    except ValueError:
        # Different drive on Windows
        return filepath


def _is_stdlib_or_thirdparty(filepath: str, cwd: str) -> bool:
    """Return True if *filepath* belongs to stdlib or an installed package.

    Keeps only files that are *inside* the current working directory and are
    not within a ``site-packages`` / ``dist-packages`` tree (which covers
    virtualenv dependencies).
    """
    if not filepath or filepath.startswith("<"):
        return True

    # Python installation directories (stdlib + stdlib extensions)
    for prefix in {sys.prefix, sys.base_prefix, sys.exec_prefix}:
        if prefix and filepath.startswith(prefix):
            return True

    # site-packages / dist-packages (covers venvs inside the project too)
    for path in sys.path:
        if ("site-packages" in path or "dist-packages" in path) and filepath.startswith(path):
            return True

    # Anything outside the project root is third-party / system code
    try:
        rel = os.path.relpath(filepath, cwd)
        return rel.startswith("..")
    except ValueError:
        return True


def _parse_profile(prof: cProfile.Profile, config: "Config") -> list[ProfileStat]:
    """Extract, filter, and return top-N ``ProfileStat`` entries.

    Uses ``pstats.Stats`` which provides the callers relationship
    (inverse of the callees list in ``cProfile.Profile.getstats()``).

    ``pstats.Stats.stats`` is a dict::

        {(filename, lineno, funcname): (prim_calls, calls, tt, ct, callers)}

    where ``callers`` is itself a dict::

        {(filename, lineno, funcname): (prim_calls, calls, tt, ct)}

    Note: in pstats, ``tt`` = own time (exclusive of callees),
    ``ct`` = cumulative time (inclusive of callees).  Both are in **seconds**;
    we convert to ms here.
    """
    cwd = os.getcwd()
    results: list[ProfileStat] = []

    stream = io.StringIO()
    try:
        ps = pstats.Stats(prof, stream=stream)
    except Exception:
        _log.exception("FlowSurgeon: failed to parse cProfile stats")
        return []

    for (filename, lineno, func_name), (
        prim_calls,
        calls,
        tt,
        ct,
        callers_dict,
    ) in ps.stats.items():
        if config.profile_user_code_only and _is_stdlib_or_thirdparty(filename, cwd):
            continue

        tt_ms = tt * 1000.0
        ct_ms = ct * 1000.0

        # Build top-3 callers sorted by their ct contribution to this function
        callers: list[tuple[str, str, int, float]] = []
        if callers_dict:
            raw: list[tuple[str, str, int, float]] = []
            for (c_file, c_line, c_func), (_cp, _cc, _ctt, c_ct) in callers_dict.items():
                if config.profile_user_code_only and _is_stdlib_or_thirdparty(c_file, cwd):
                    continue
                raw.append((_short_path(c_file, cwd), c_func, c_line, c_ct * 1000.0))
            raw.sort(key=lambda x: x[3], reverse=True)
            callers = raw[:3]

        results.append(
            ProfileStat(
                file=_short_path(filename, cwd),
                line=lineno,
                func=func_name,
                prim_calls=prim_calls,
                calls=calls,
                tt_ms=tt_ms,
                ct_ms=ct_ms,
                callers=callers,
            )
        )

    # Sort by cumulative time descending, keep top N
    results.sort(key=lambda s: s.ct_ms, reverse=True)
    top_n = config.profile_top_n
    return results[:top_n] if top_n > 0 else results
