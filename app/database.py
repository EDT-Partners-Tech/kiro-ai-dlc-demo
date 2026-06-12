"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

# Database configuration
DATABASE_URL = "sqlite:///./blog-posts.db"

# Create engine with echo=False (no SQL logging)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # SQLite-specific for threading
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency injection for database session."""
    with Session(engine) as session:
        yield session
