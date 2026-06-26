"""Repository untuk entitas Transcription."""
from __future__ import annotations

from src.models import Transcription
from src.repositories.base import BaseRepository


class TranscriptionRepository(BaseRepository[Transcription]):
    model = Transcription

    async def get_by_meeting_id(self, meeting_id: int) -> Transcription | None:
        """Ambil transkrip milik sebuah meeting (relasi 1:1)."""
        return await self.get_by(meeting_id=meeting_id)
