"""Async database core: engine, session factory, declarative Base.

Repo ini memakai stack async (asyncpg), jadi koneksi DB pun async (SQLAlchemy 2.0
AsyncEngine + AsyncSession). URL diambil dari Settings (src/core/config/setting.py).
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config.setting import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base untuk semua model ORM."""
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI: satu AsyncSession per request, ditutup otomatis."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_models() -> None:
    """Buat semua tabel dari metadata (untuk dev/test cepat). Produksi pakai Alembic."""
    from src import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
