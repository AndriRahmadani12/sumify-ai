"""BaseRepository: CRUD generik async untuk semua entitas (Repository Pattern).

Setiap repository spesifik mewarisi kelas ini, cukup menyetel atribut `model`,
lalu otomatis dapat create/read/update/delete/list/count/exists. Query khusus
per-entitas ditambahkan di subclass-nya.
"""
from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgree import Base
from src.schemas.common import PaginationParams, SortOrder

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """CRUD dasar yang dipakai bersama semua entitas.

    Cara pakai:
        class MeetingRepository(BaseRepository[Meeting]):
            model = Meeting
        repo = MeetingRepository(session)
        meeting = await repo.create(title="Rapat Q1", language="id")
    """

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: AsyncSession aktif (di-inject dari dependency / pemanggil).
        """
        self.session = session

    # ── CREATE ──
    async def create(self, **values: Any) -> ModelType:
        """Buat satu baris baru, commit, lalu kembalikan objeknya (sudah ber-id)."""
        obj = self.model(**values)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def bulk_create(self, items: Sequence[dict[str, Any]]) -> list[ModelType]:
        """Buat banyak baris sekaligus dalam satu commit."""
        objs = [self.model(**item) for item in items]
        self.session.add_all(objs)
        await self.session.commit()
        for obj in objs:
            await self.session.refresh(obj)
        return objs

    # ── READ ──
    async def get_by_id(self, id_: Any) -> ModelType | None:
        """Ambil satu baris berdasarkan primary key, atau None bila tidak ada."""
        return await self.session.get(self.model, id_)

    async def get_by(self, **filters: Any) -> ModelType | None:
        """Ambil satu baris pertama yang cocok dengan filter (mis. email=...)."""
        stmt = select(self.model).filter_by(**filters).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """Ambil daftar baris dengan filter, limit/offset, dan pengurutan opsional."""
        stmt = select(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            stmt = stmt.order_by(col.desc() if descending else col.asc())
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list(
        self, pagination: PaginationParams, **filters: Any
    ) -> tuple[Sequence[ModelType], int]:
        """Versi berhalaman: kembalikan (items, total) sesuai PaginationParams."""
        total = await self.count(**filters)
        items = await self.get_all(
            limit=pagination.page_size,
            offset=pagination.offset,
            order_by=pagination.sort_by,
            descending=pagination.sort_order == SortOrder.DESC,
            **filters,
        )
        return items, total

    # ── UPDATE ──
    async def update(self, id_: Any, **values: Any) -> ModelType | None:
        """Ubah field suatu baris. Kembalikan objek terbaru, atau None bila tak ada."""
        obj = await self.get_by_id(id_)
        if obj is None:
            return None
        for key, value in values.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    # ── DELETE ──
    async def delete(self, id_: Any) -> bool:
        """Hapus satu baris. True bila terhapus, False bila baris tak ditemukan."""
        obj = await self.get_by_id(id_)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True

    # ── UTIL ──
    async def count(self, **filters: Any) -> int:
        """Hitung jumlah baris (dengan filter opsional)."""
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def exists(self, **filters: Any) -> bool:
        """Cek apakah ada minimal satu baris yang cocok dengan filter."""
        stmt = select(self.model.id).filter_by(**filters).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
