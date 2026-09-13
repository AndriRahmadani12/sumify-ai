"""Router untuk transkripsi otomatis dengan Whisper."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException

from src.core.logging.logger import get_logger
from src.services.pipeline.main_pipeline import PipelineError, transcribe_meeting_audio

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["transcribe"])


@router.post("/meetings/{meeting_id}/transcribe")
async def transcribe_meeting(meeting_id: int, language: str | None = Form(None)):
    """Unduh audio meeting dari storage lalu transkripsikan dengan Whisper.

    Pemanggilan pertama akan mengunduh model Whisper (~150 MB untuk 'base'),
    jadi bisa memakan waktu beberapa menit. Pemanggilan berikutnya lebih cepat
    karena model sudah tersimpan di cache.
    """
    try:
        result = await transcribe_meeting_audio(meeting_id, language=language)
    except PipelineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"message": "Transkripsi selesai", "meeting_id": meeting_id, **result}
