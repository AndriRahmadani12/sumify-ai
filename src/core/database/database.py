"""Konfigurasi koneksi database (SQLAlchemy 2.0 + PostgreSQL)."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Ambil dari environment. Contoh:
# postgresql+psycopg://user:password@localhost:5432/meeting_summarizer
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/meeting_summarizer",
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class untuk semua model."""
    pass


def get_db():
    """Dependency FastAPI: kasih satu session per request, lalu ditutup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
