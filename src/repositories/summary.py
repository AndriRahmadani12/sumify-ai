"""Repository untuk entitas Summary."""
from __future__ import annotations

from src.models import Summary
from src.repositories.base import BaseRepository


class SummaryRepository(BaseRepository[Summary]):
    model = Summary

    async def get_by_meeting_id(self, meeting_id: int) -> Summary | None:
        """Ambil ringkasan milik sebuah meeting (relasi 1:1)."""
        return await self.get_by(meeting_id=meeting_id)
