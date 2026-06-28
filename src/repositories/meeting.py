"""Repository untuk entitas Meeting."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import Meeting
from src.repositories.base import BaseRepository
from src.schemas.common import ProcessingStatus


class MeetingRepository(BaseRepository[Meeting]):
    model = Meeting

    async def get_by_user(self, user_id: int) -> Sequence[Meeting]:
        """Semua meeting milik satu user, terbaru di atas."""
        return await self.get_all(user_id=user_id, order_by="created_at", descending=True)

    async def get_by_status(self, status: ProcessingStatus) -> Sequence[Meeting]:
        """Semua meeting pada status tertentu (mis. yang masih TRANSCRIBING)."""
        return await self.get_all(status=status)

    async def update_status(
        self, meeting_id: int, status: ProcessingStatus
    ) -> Meeting | None:
        """Ubah status pemrosesan sebuah meeting."""
        return await self.update(meeting_id, status=status)

    async def get_with_relations(self, meeting_id: int) -> Meeting | None:
        """Ambil meeting beserta transcription, summary, dan jobs sekaligus.

        Pakai selectinload agar relasi ikut ter-load (penting di async, supaya
        tidak terjadi lazy-load yang dilarang di luar session).
        """
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(
                selectinload(Meeting.transcription),
                selectinload(Meeting.summary),
                selectinload(Meeting.jobs),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
