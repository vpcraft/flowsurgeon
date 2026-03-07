"""FlowSurgeon v0.3.0 — Flask demo (API-first, DBAPITracker).

Run:
    uv run --group examples python examples/flask/demo_flask.py

Then hit the API at http://127.0.0.1:5000 and inspect query tracking at:
    http://127.0.0.1:5000/__flowsurgeon__/

Routes:
    GET /books                 list books   (1 SQL query)
    GET /books/<id>            book detail  (1 SQL query, parametrised)
    GET /books/duplicates      same query twice → "dup" badge
    GET /books/slow            80 ms sleep between queries → "slow" badge
    GET /slow                  300 ms sleep, no DB queries
    GET /boom                  500 error
"""

import sqlite3
import time

from flask import Flask, abort, jsonify

from flowsurgeon import Config, FlowSurgeonWSGI
from flowsurgeon.trackers import DBAPITracker

# ---------------------------------------------------------------------------
# Demo database
# ---------------------------------------------------------------------------

_raw_conn = sqlite3.connect("books_flask.db", check_same_thread=False)
_raw_conn.row_factory = sqlite3.Row
_raw_conn.executescript("""
    CREATE TABLE IF NOT EXISTS books (
        id     INTEGER PRIMARY KEY,
        title  TEXT NOT NULL,
        author TEXT NOT NULL,
        year   INTEGER NOT NULL
    );
    DELETE FROM books;
    INSERT INTO books (title, author, year) VALUES
        ('Clean Code',               'Robert C. Martin', 2008),
        ('The Pragmatic Programmer', 'Andy Hunt',        1999),
        ('Design Patterns',          'Gang of Four',     1994),
        ('Refactoring',              'Martin Fowler',    1999),
        ('You Don''t Know JS',       'Kyle Simpson',     2015);
""")
_raw_conn.commit()

_tracker = DBAPITracker(_raw_conn)
_conn = _tracker.connection

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)

app.wsgi_app = FlowSurgeonWSGI(
    app.wsgi_app,
    config=Config(
        enabled=True,
        db_path="flowsurgeon_flask.db",
        allowed_hosts=["127.0.0.1", "::1", "localhost"],
        slow_query_threshold_ms=50.0,
    ),
    trackers=[_tracker],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/books")
def books():
    cur = _conn.cursor()
    cur.execute("SELECT id, title, author, year FROM books ORDER BY year")
    return jsonify({"books": [dict(r) for r in cur.fetchall()]})


@app.get("/books/duplicates")
def books_duplicates():
    """Runs the same query twice — panel shows 'dup' badge."""
    cur = _conn.cursor()
    cur.execute("SELECT id, title FROM books WHERE year < 2000")
    first = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT id, title FROM books WHERE year < 2000")
    _ = cur.fetchall()
    return jsonify({"books": first, "note": "same query ran twice — check /__flowsurgeon__/"})


@app.get("/books/slow")
def books_slow():
    """Adds an 80 ms sleep between two queries; one will exceed slow_query_threshold_ms=50."""
    cur = _conn.cursor()
    cur.execute("SELECT id, title FROM books")
    rows = [dict(r) for r in cur.fetchall()]
    time.sleep(0.08)
    cur.execute("SELECT COUNT(*) AS total FROM books")
    total = cur.fetchone()["total"]
    return jsonify({"books": rows, "total": total, "note": "check /__flowsurgeon__/ for slow badge"})


@app.get("/books/<int:book_id>")
def book_detail(book_id: int):
    cur = _conn.cursor()
    cur.execute("SELECT id, title, author, year FROM books WHERE id = ?", (book_id,))
    row = cur.fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))


@app.get("/slow")
def slow():
    time.sleep(0.3)
    return jsonify({"message": "delayed 300ms", "note": "no SQL queries on this route"})


@app.get("/boom")
def boom():
    abort(500)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("FlowSurgeon Flask demo running at http://127.0.0.1:5000")
    print("Query tracking UI: http://127.0.0.1:5000/__flowsurgeon__/")
    app.run(host="127.0.0.1", port=5000, debug=False)
