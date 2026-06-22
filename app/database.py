"""Database initialization and session management."""

import os
from sqlalchemy import create_engine, event
from sqlmodel import SQLModel, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cloudspend.db")

# Create engine with connection pooling (adjust for SQLite)
if DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't support connection pooling
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL and other databases support pooling
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DATABASE_POOL_MAX_OVERFLOW", "15")),
        pool_pre_ping=True,
    )

# Enable WAL mode for SQLite (better concurrency)
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def init_db():
    """Create all tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: get database session."""
    with Session(engine) as session:
        yield session
