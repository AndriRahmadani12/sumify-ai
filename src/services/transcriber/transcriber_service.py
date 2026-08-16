from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgree import async_session_maker
from src.core.exceptions import NotFoundException, ProcessingException
from src.models import Transcription
from src.repositories.meeting import MeetingRepository
from src.repositories.transcription import TranscriptionRepository
from src.services.storage.storage import StorageService
from src.services.transcriber.whisper_model_manager import WhisperModelManager


class TranscriptionError(Exception):
    """Error spesifik saat proses transkripsi."""


class TranscriberService:

    def __init__(
        self,
        whisper_manager: WhisperModelManager | None = None,
        storage_service: StorageService | None = None,
    ) -> None:
        self.whisper_manager = whisper_manager or WhisperModelManager.get_instance()
        self.storage_service = storage_service or StorageService()

    async def transcribe_audio(
        self,
        audio_path: str | Path,
        language: str | None = None,
    ) -> dict[str, Any]:
        options: dict[str, Any] = {"task": "transcribe"}
        if language:
            options["language"] = language

        return await asyncio.to_thread(
            self.whisper_manager.transcribe,
            str(audio_path),
            **options,
        )

    async def transcribe_meeting(
        self,
        meeting_id: int,
        session: AsyncSession,
    ) -> Transcription:
        meeting_repo = MeetingRepository(session)
        transcription_repo = TranscriptionRepository(session)

        meeting = await meeting_repo.get_with_relations(meeting_id)
        if meeting is None:
            raise NotFoundException("Meeting", meeting_id)
        if not meeting.storage_path:
            raise TranscriptionError(
                f"Meeting {meeting_id} tidak memiliki file audio"
            )

        existing = await transcription_repo.get_by_meeting_id(meeting_id)
        if existing is not None:
            return existing

        audio_bytes = await self.storage_service.download_file(meeting.storage_path)

        suffix = Path(meeting.storage_path).suffix or ".tmp"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = Path(tmp.name)

        try:
            language = meeting.language or "id"
            result = await self.transcribe_audio(tmp_path, language=language)

            segments = result.get("segments", [])
            full_text = result.get("text", "").strip()
            detected_language = result.get("language", language)

            transcription = await transcription_repo.create(
                meeting_id=meeting_id,
                full_text=full_text,
                segments=segments,
                language=detected_language,
            )
            return transcription

        finally:
            tmp_path.unlink(missing_ok=True)

    @classmethod
    async def run_standalone(cls, meeting_id: int) -> Transcription:
        async with async_session_maker() as session:
            service = cls()
            return await service.transcribe_meeting(meeting_id, session)
