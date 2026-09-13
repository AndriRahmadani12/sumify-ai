"""Router untuk transkrip manual, ringkasan, dan pengambilan PDF."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse

from src.core.database.postgree import async_session_maker
from src.core.logging.logger import get_logger
from src.prompts.prompt_handler import available_types
from src.repositories import MeetingRepository, TranscriptionRepository
from src.services.pipeline.main_pipeline import PipelineError, summarize_and_generate_pdf

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["summary"])


@router.get("/templates")
async def list_templates():
    """Jenis ringkasan yang tersedia."""
    return {"templates": available_types()}


@router.post("/meetings/{meeting_id}/transcript")
async def set_transcript(meeting_id: int, full_text: str = Form(...)):
    """Isi transkrip meeting secara manual.

    Sementara dipakai selama modul transkripsi otomatis (Whisper) belum ada,
    supaya alur ringkasan sampai PDF bisa diuji.
    """
    if not full_text.strip():
        raise HTTPException(status_code=400, detail="Transkrip kosong")

    async with async_session_maker() as session:
        meeting_repo = MeetingRepository(session)
        transcription_repo = TranscriptionRepository(session)

        meeting = await meeting_repo.get_by_id(meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="Meeting tidak ditemukan")

        existing = await transcription_repo.get_by_meeting_id(meeting_id)
        if existing is None:
            row = await transcription_repo.create(
                meeting_id=meeting_id,
                full_text=full_text,
                language=meeting.language or "id",
            )
        else:
            row = await transcription_repo.update(existing.id, full_text=full_text)

    return {
        "message": "Transkrip tersimpan",
        "meeting_id": meeting_id,
        "transcription_id": row.id,
        "length": len(full_text),
    }


@router.post("/meetings/{meeting_id}/summarize")
async def summarize(meeting_id: int, template_type: str = Form("simple")):
    """Ringkas transkrip meeting lalu hasilkan PDF."""
    try:
        result = await summarize_and_generate_pdf(
            meeting_id=meeting_id,
            template_type=template_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PipelineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "message": "Ringkasan dan PDF berhasil dibuat",
        "meeting_id": result.meeting_id,
        "template_type": result.template_type,
        "summary_id": result.summary_id,
        "pdf_path": result.pdf_path,
        "pdf_url": result.pdf_url,
    }


@router.get("/meetings/{meeting_id}/pdf")
async def download_pdf(meeting_id: int):
    """Unduh PDF hasil ringkasan dari disk lokal."""
    matches = sorted(Path("generated_pdfs").glob(f"meeting-{meeting_id}-*.pdf"))
    if not matches:
        raise HTTPException(status_code=404, detail="PDF belum dibuat")

    latest = matches[-1]
    return FileResponse(path=latest, media_type="application/pdf", filename=latest.name)