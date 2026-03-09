"""FlowSurgeon v0.5.0 — FastAPI demo (API-first, SQLAlchemyTracker + profiling).

Run:
    uv run --group examples uvicorn examples.fastapi.demo_fastapi:app --reload

Debug UI → http://127.0.0.1:8000/flowsurgeon
  - Latency tab: request grid
  - Profile tab on each request: call-stack profiling (enable_profiling=True)

Routes:
    GET /books                 list books   (1 SQL query)
    GET /books/{id}            book detail  (1 SQL query, parametrised)
    GET /books/duplicates      same query twice → "dup" badge
    GET /books/slow            80 ms sleep between queries → "slow" badge
    GET /slow                  300 ms sleep, no DB queries
    GET /boom                  500 error
"""

import asyncio

from fastapi import FastAPI, HTTPException
from sqlalchemy import Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from flowsurgeon import Config, FlowSurgeon
from flowsurgeon.trackers.sqlalchemy import SQLAlchemyTracker

# ---------------------------------------------------------------------------
# SQLAlchemy setup
# ---------------------------------------------------------------------------

engine = create_engine("sqlite:///books_fastapi.db", echo=False)


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)


Base.metadata.create_all(engine)

with Session(engine) as _seed:
    if _seed.execute(text("SELECT COUNT(*) FROM books")).scalar() == 0:
        _seed.execute(
            text(
                "INSERT INTO books (title, author, year) VALUES "
                "('Clean Code', 'Robert C. Martin', 2008), "
                "('The Pragmatic Programmer', 'Andy Hunt', 1999), "
                "('Design Patterns', 'Gang of Four', 1994), "
                "('Refactoring', 'Martin Fowler', 1999), "
                "('You Don''t Know JS', 'Kyle Simpson', 2015)"
            )
        )
        _seed.commit()

_tracker = SQLAlchemyTracker(engine, capture_stacktrace=False)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

_inner = FastAPI()

app = FlowSurgeon(
    _inner,
    config=Config(
        enabled=True,
        enable_profiling=True,
        db_path="flowsurgeon_fastapi.db",
        allowed_hosts=["127.0.0.1", "::1", "localhost"],
        slow_query_threshold_ms=50.0,
    ),
    trackers=[_tracker],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@_inner.get("/books")
async def books():
    with Session(engine) as session:
        rows = session.execute(
            text("SELECT id, title, author, year FROM books ORDER BY year")
        ).fetchall()
    return {"books": [r._asdict() for r in rows]}


@_inner.get("/books/duplicates")
async def books_duplicates():
    """Runs the same query twice — panel shows 'dup' badge."""
    with Session(engine) as session:
        first = session.execute(text("SELECT id, title FROM books WHERE year < 2000")).fetchall()
        _ = session.execute(text("SELECT id, title FROM books WHERE year < 2000")).fetchall()
    return {
        "books": [r._asdict() for r in first],
        "note": "same query ran twice — check /__flowsurgeon__/",
    }


@_inner.get("/books/slow")
async def books_slow():
    """Adds an 80 ms async sleep between two queries; one will exceed slow_query_threshold_ms=50."""
    with Session(engine) as session:
        rows = session.execute(text("SELECT id, title FROM books")).fetchall()
        await asyncio.sleep(0.08)
        total = session.execute(text("SELECT COUNT(*) FROM books")).scalar()
    return {
        "books": [r._asdict() for r in rows],
        "total": total,
        "note": "check /__flowsurgeon__/ for slow badge",
    }


@_inner.get("/books/{book_id}")
async def book_detail(book_id: int):
    with Session(engine) as session:
        row = session.execute(
            text("SELECT id, title, author, year FROM books WHERE id = :id"),
            {"id": book_id},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return row._asdict()


@_inner.get("/slow")
async def slow():
    await asyncio.sleep(0.3)
    return {"message": "delayed 300ms", "note": "no SQL queries on this route"}


@_inner.get("/boom")
async def boom():
    raise HTTPException(status_code=500, detail="Intentional server error")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print("FlowSurgeon FastAPI demo running at http://127.0.0.1:8000")
    print("Query tracking UI: http://127.0.0.1:8000/__flowsurgeon__/")
    uvicorn.run(app, host="127.0.0.1", port=8000)
