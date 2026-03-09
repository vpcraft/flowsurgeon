"""Tests for call-stack profiling: _parse_profile, _is_stdlib_or_thirdparty,
and end-to-end profiling via WSGI and ASGI middlewares."""

from __future__ import annotations

import cProfile
import os
import sys

import pytest

from flowsurgeon.core.config import Config
from flowsurgeon.core.records import ProfileStat, RequestRecord
from flowsurgeon.profiling import _is_stdlib_or_thirdparty, _parse_profile, _short_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fib(n: int) -> int:
    """A simple recursive function used as a profiling target."""
    if n <= 1:
        return n
    return _fib(n - 1) + _fib(n - 2)


def _run_and_profile(target, config: Config | None = None) -> list[ProfileStat]:
    """Profile *target()* and return parsed stats."""
    cfg = config or Config(enable_profiling=True, profile_user_code_only=False, profile_top_n=0)
    prof = cProfile.Profile()
    prof.enable()
    try:
        target()
    finally:
        prof.disable()
    return _parse_profile(prof, cfg)


# ---------------------------------------------------------------------------
# _short_path
# ---------------------------------------------------------------------------


def test_short_path_relative():
    cwd = os.getcwd()
    abs_path = os.path.join(cwd, "src", "foo.py")
    result = _short_path(abs_path, cwd)
    assert not os.path.isabs(result)
    assert "foo.py" in result


def test_short_path_builtin():
    assert _short_path("<built-in>", os.getcwd()) == "<built-in>"


def test_short_path_empty():
    assert _short_path("", os.getcwd()) == ""


# ---------------------------------------------------------------------------
# _is_stdlib_or_thirdparty
# ---------------------------------------------------------------------------


def test_stdlib_detected():
    import pathlib

    filepath = pathlib.__file__
    assert _is_stdlib_or_thirdparty(filepath, os.getcwd()) is True


def test_builtin_str_detected():
    assert _is_stdlib_or_thirdparty("<built-in method>", os.getcwd()) is True


def test_empty_path_detected():
    assert _is_stdlib_or_thirdparty("", os.getcwd()) is True


def test_project_file_not_filtered():
    # A file inside the project directory should NOT be filtered
    cwd = os.getcwd()
    local_file = os.path.join(cwd, "src", "flowsurgeon", "profiling.py")
    # It exists on disk — should be treated as user code
    assert _is_stdlib_or_thirdparty(local_file, cwd) is False


def test_site_packages_detected():
    # Find any installed package file path
    for path in sys.path:
        if "site-packages" in path:
            candidate = os.path.join(path, "some_pkg", "mod.py")
            assert _is_stdlib_or_thirdparty(candidate, os.getcwd()) is True
            break


def test_outside_cwd_detected():
    cwd = os.getcwd()
    outside = os.path.join(os.path.dirname(cwd), "other_project", "module.py")
    assert _is_stdlib_or_thirdparty(outside, cwd) is True


# ---------------------------------------------------------------------------
# _parse_profile — basic shape
# ---------------------------------------------------------------------------


def test_parse_profile_returns_list():
    stats = _run_and_profile(lambda: _fib(10))
    assert isinstance(stats, list)
    assert len(stats) > 0


def test_parse_profile_stat_fields():
    stats = _run_and_profile(lambda: _fib(10))
    stat = stats[0]
    assert isinstance(stat, ProfileStat)
    assert isinstance(stat.file, str)
    assert isinstance(stat.line, int)
    assert isinstance(stat.func, str)
    assert stat.calls > 0
    assert stat.ct_ms >= 0.0
    assert stat.tt_ms >= 0.0
    assert isinstance(stat.callers, list)


def test_parse_profile_sorted_by_ct_ms():
    stats = _run_and_profile(lambda: _fib(15))
    ct_values = [s.ct_ms for s in stats]
    assert ct_values == sorted(ct_values, reverse=True)


def test_parse_profile_fib_appears():
    """_fib must appear in the profile when user_code_only=False."""
    stats = _run_and_profile(lambda: _fib(10))
    func_names = [s.func for s in stats]
    assert "_fib" in func_names


def test_parse_profile_top_n():
    """profile_top_n limits the returned list length."""
    cfg = Config(enable_profiling=True, profile_user_code_only=False, profile_top_n=3)
    stats = _run_and_profile(lambda: _fib(10), config=cfg)
    assert len(stats) <= 3


def test_parse_profile_top_n_zero_means_all():
    """profile_top_n=0 returns all frames."""
    cfg = Config(enable_profiling=True, profile_user_code_only=False, profile_top_n=0)
    stats_all = _run_and_profile(lambda: _fib(10), config=cfg)
    cfg_limited = Config(enable_profiling=True, profile_user_code_only=False, profile_top_n=3)
    stats_limited = _run_and_profile(lambda: _fib(10), config=cfg_limited)
    assert len(stats_all) >= len(stats_limited)


def test_parse_profile_user_code_only_filters_stdlib():
    """With user_code_only=True, stdlib frames must not appear."""
    cfg = Config(enable_profiling=True, profile_user_code_only=True, profile_top_n=0)
    stats = _run_and_profile(lambda: _fib(10), config=cfg)
    cwd = os.getcwd()
    for stat in stats:
        assert not _is_stdlib_or_thirdparty(
            os.path.join(cwd, stat.file) if not os.path.isabs(stat.file) else stat.file,
            cwd,
        ), f"Stdlib frame leaked: {stat.file}:{stat.func}"


def test_parse_profile_callers_are_tuples():
    """Each caller entry must be a list/tuple of (file, func, line, ct_ms)."""
    stats = _run_and_profile(lambda: _fib(10))
    for stat in stats:
        for caller in stat.callers:
            assert len(caller) == 4
            c_file, c_func, c_line, c_ct = caller
            assert isinstance(c_file, str)
            assert isinstance(c_func, str)
            assert isinstance(c_line, int)
            assert isinstance(c_ct, float)


def test_parse_profile_empty_profile():
    """A profile with no calls (only cProfile overhead) should not crash."""
    cfg = Config(enable_profiling=True, profile_user_code_only=False, profile_top_n=0)
    prof = cProfile.Profile()
    prof.enable()
    prof.disable()
    result = _parse_profile(prof, cfg)
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# WSGI integration
# ---------------------------------------------------------------------------


def test_wsgi_profiling_populates_record(tmp_path):
    """With enable_profiling=True, the RequestRecord must have profile_stats."""
    from flowsurgeon import Config, FlowSurgeonWSGI

    # captured: list[RequestRecord] = []

    def inner_app(environ, start_response):
        _fib(8)
        start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", "2")])
        return [b"ok"]

    storage_path = str(tmp_path / "test.db")
    mw = FlowSurgeonWSGI(
        inner_app,
        config=Config(
            enabled=True,
            enable_profiling=True,
            profile_user_code_only=False,
            db_path=storage_path,
        ),
    )

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/test",
        "QUERY_STRING": "",
        "REMOTE_ADDR": "127.0.0.1",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.input": __import__("io").BytesIO(b""),
    }

    def start_response(status, headers):
        pass

    list(mw(environ, start_response))

    records = mw._storage.list_recent(limit=1)
    assert len(records) == 1
    record = records[0]
    assert record.profile_stats is not None
    assert len(record.profile_stats) > 0
    func_names = [s.func for s in record.profile_stats]
    assert "_fib" in func_names


def test_wsgi_profiling_disabled_no_stats(tmp_path):
    """With enable_profiling=False (default), profile_stats must be None."""
    from flowsurgeon import Config, FlowSurgeonWSGI

    def inner_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", "2")])
        return [b"ok"]

    storage_path = str(tmp_path / "test.db")
    mw = FlowSurgeonWSGI(
        inner_app,
        config=Config(enabled=True, enable_profiling=False, db_path=storage_path),
    )

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/test",
        "QUERY_STRING": "",
        "REMOTE_ADDR": "127.0.0.1",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.input": __import__("io").BytesIO(b""),
    }

    list(mw(environ, lambda s, h: None))
    records = mw._storage.list_recent(limit=1)
    assert records[0].profile_stats is None


# ---------------------------------------------------------------------------
# ASGI integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_asgi_profiling_populates_record(tmp_path):
    """With enable_profiling=True, the ASGI middleware stores profile_stats."""
    from flowsurgeon import Config, FlowSurgeonASGI
    from flowsurgeon.storage.async_sqlite import AsyncSQLiteBackend

    async def inner_app(scope, receive, send):
        _fib(8)
        body = b"ok"
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    storage_path = str(tmp_path / "test.db")
    storage = AsyncSQLiteBackend(storage_path)
    mw = FlowSurgeonASGI(
        inner_app,
        config=Config(
            enabled=True,
            enable_profiling=True,
            profile_user_code_only=False,
            db_path=storage_path,
        ),
        storage=storage,
    )

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "headers": [],
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    messages = []

    async def send_fn(message):
        messages.append(message)

    await mw(scope, receive, send_fn)
    await storage._queue.join()

    records = await storage.list_recent(limit=1)
    assert len(records) == 1
    record = records[0]
    assert record.profile_stats is not None
    assert len(record.profile_stats) > 0
    func_names = [s.func for s in record.profile_stats]
    assert "_fib" in func_names


@pytest.mark.asyncio
async def test_asgi_profiling_disabled_no_stats(tmp_path):
    """With enable_profiling=False, profile_stats must be None for ASGI."""
    from flowsurgeon import Config, FlowSurgeonASGI
    from flowsurgeon.storage.async_sqlite import AsyncSQLiteBackend

    async def inner_app(scope, receive, send):
        body = b"ok"
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain"), (b"content-length", b"2")],
            }
        )
        await send({"type": "http.response.body", "body": body})

    storage_path = str(tmp_path / "test.db")
    storage = AsyncSQLiteBackend(storage_path)
    mw = FlowSurgeonASGI(
        inner_app,
        config=Config(enabled=True, enable_profiling=False, db_path=storage_path),
        storage=storage,
    )

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "headers": [],
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send_fn(message):
        pass

    await mw(scope, receive, send_fn)
    await storage._queue.join()

    records = await storage.list_recent(limit=1)
    assert records[0].profile_stats is None


# ---------------------------------------------------------------------------
# SQLite round-trip
# ---------------------------------------------------------------------------


def test_sqlite_profile_stats_roundtrip(tmp_path):
    """ProfileStat serialises to SQLite and deserialises correctly."""
    from flowsurgeon.core.records import ProfileStat
    from flowsurgeon.storage.sqlite import SQLiteBackend

    db_path = str(tmp_path / "roundtrip.db")
    backend = SQLiteBackend(db_path)

    stats = [
        ProfileStat(
            file="app/views.py",
            line=42,
            func="get_books",
            prim_calls=1,
            calls=1,
            tt_ms=0.3,
            ct_ms=14.2,
            callers=[("app/router.py", "dispatch", 19, 14.2)],
        ),
        ProfileStat(
            file="app/db.py",
            line=18,
            func="execute",
            prim_calls=3,
            calls=3,
            tt_ms=0.8,
            ct_ms=13.9,
            callers=[],
        ),
    ]

    record = RequestRecord(
        method="GET",
        path="/books",
        status_code=200,
        duration_ms=15.0,
        profile_stats=stats,
    )
    backend.save(record)

    loaded = backend.get(record.request_id)
    assert loaded is not None
    assert loaded.profile_stats is not None
    assert len(loaded.profile_stats) == 2

    s0 = loaded.profile_stats[0]
    assert s0.file == "app/views.py"
    assert s0.line == 42
    assert s0.func == "get_books"
    assert s0.calls == 1
    assert abs(s0.ct_ms - 14.2) < 0.001
    assert len(s0.callers) == 1
    assert s0.callers[0][1] == "dispatch"

    s1 = loaded.profile_stats[1]
    assert s1.func == "execute"
    assert s1.callers == []


def test_sqlite_profile_stats_none_roundtrip(tmp_path):
    """A record with profile_stats=None must round-trip to None."""
    from flowsurgeon.storage.sqlite import SQLiteBackend

    db_path = str(tmp_path / "none_roundtrip.db")
    backend = SQLiteBackend(db_path)
    record = RequestRecord(method="GET", path="/ping", status_code=200, profile_stats=None)
    backend.save(record)
    loaded = backend.get(record.request_id)
    assert loaded is not None
    assert loaded.profile_stats is None
