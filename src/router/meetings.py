"""Router yang mengikuti kontrak API aplikasi Android (sumify-ai-fe).

Berbeda dengan router lain yang memecah prosesnya per tahap, di sini upload
langsung memicu seluruh pipeline di latar belakang lalu mengembalikan id.
Aplikasi kemudian melakukan polling ke GET /meetings/{id} sampai statusnya
`completed` atau `failed`.

Catatan: aplikasi belum punya sistem login sehingga tidak mengirim user_id.
Sementara ini semua meeting dicatat ke satu user bawaan. Ini utang teknis
yang perlu dibereskan begitu autentikasi tersedia.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from src.core.database.postgree import async_session_maker
from src.core.logging.logger import get_logger
from src.repositories import (
    MeetingRepository,
    SummaryRepository,
    TranscriptionRepository,
    UserRepository,
)
from src.schemas.common import ProcessingStatus
from src.services.storage.storage import storage_service

logger = get_logger(__name__)

router = APIRouter(prefix="/meetings", tags=["meetings (mobile)"])

DEFAULT_USER_EMAIL = "app@sumify.ai"


async def _get_default_user_id(session) -> int:
    """Ambil user bawaan, buat kalau belum ada."""
    repo = UserRepository(session)
    user = await repo.get_by_email(DEFAULT_USER_EMAIL)
    if user is None:
        user = await repo.create(
            email=DEFAULT_USER_EMAIL,
            name="Sumify App User",
            password_hash="-",
        )
        logger.info(f"User bawaan dibuat: id={user.id}")
    return user.id


def _enqueue_pipeline(meeting_id: int, template_type: str) -> bool:
    """Kirim pekerjaan ke Celery. Mengembalikan False kalau broker tidak siap."""
    try:
        from src.worker.calery_task import full_pipeline_task

        full_pipeline_task.delay(meeting_id=meeting_id, template_type=template_type)
        return True
    except Exception as exc:
        logger.warning(f"Gagal mengirim task ke Celery untuk meeting {meeting_id}: {exc}")
        return False


async def _run_pipeline_inline(meeting_id: int, template_type: str) -> None:
    """Cadangan kalau Celery tidak tersedia: jalankan di background task asyncio.

    Prosesnya tetap tidak memblokir respons upload, tapi terikat pada umur
    proses server. Untuk produksi, Celery yang dipakai.
    """
    from src.services.pipeline.main_pipeline import (
        summarize_and_generate_pdf,
        transcribe_meeting_audio,
    )

    try:
        await transcribe_meeting_audio(meeting_id)
        await summarize_and_generate_pdf(meeting_id, template_type)
    except Exception as exc:
        logger.error(f"Pipeline inline gagal untuk meeting {meeting_id}: {exc}")


@router.post("")
async def create_meeting(
    audio: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    language: str | None = Form(None),
    template_type: str = Form("business"),
):
    """Terima audio, catat meeting, lalu proses di latar belakang.

    Mengembalikan id dan status secepatnya tanpa menunggu proses selesai.
    """
    file_bytes = await audio.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Berkas audio kosong")

    async with async_session_maker() as session:
        user_id = await _get_default_user_id(session)

    try:
        await storage_service.initialize()
        info = await storage_service.upload_audio(
            file_data=file_bytes,
            filename=audio.filename or "audio.mp3",
            user_id=user_id,
            content_type=audio.content_type or "audio/mpeg",
        )
    except Exception as exc:
        logger.error(f"Gagal menyimpan audio ke storage: {exc}")
        raise HTTPException(
            status_code=502, detail="Gagal menyimpan berkas ke storage"
        ) from exc

    async with async_session_maker() as session:
        meeting = await MeetingRepository(session).create(
            user_id=user_id,
            title=title,
            # description dipakai ganda: catatan pengguna bila ada, kalau tidak
            # nama berkas asli supaya tampil di PDF.
            description=description or audio.filename,
            language=language or "id",
            storage_path=info.storage_path,
            storage_bucket=info.storage_bucket,
            status=ProcessingStatus.QUEUED,
        )
        meeting_id = meeting.id

    if not _enqueue_pipeline(meeting_id, template_type):
        # Celery tidak siap, jalankan sebagai background task biasa.
        asyncio.create_task(_run_pipeline_inline(meeting_id, template_type))

    return {"id": str(meeting_id), "status": ProcessingStatus.QUEUED.value}


@router.get("/{meeting_id}/download")
async def download_meeting_pdf(meeting_id: str):
    """Alirkan PDF hasil ringkasan lewat API.

    Sengaja tidak memakai presigned URL MinIO, karena URL itu menunjuk ke
    host storage (localhost:9000) yang tidak terjangkau dari perangkat lain.
    Dengan dialirkan lewat endpoint ini, satu alamat backend sudah cukup.
    """
    try:
        numeric_id = int(meeting_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="id meeting tidak valid")

    async with async_session_maker() as session:
        meeting = await MeetingRepository(session).get_by_id(numeric_id)

    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting tidak ditemukan")
    if not meeting.pdf_url:
        raise HTTPException(status_code=404, detail="PDF belum tersedia")

    try:
        pdf_bytes = await storage_service.download_file(meeting.pdf_url)
    except Exception as exc:
        logger.error(f"Gagal mengambil PDF meeting {numeric_id}: {exc}")
        raise HTTPException(status_code=502, detail="Gagal mengambil PDF") from exc

    filename = meeting.pdf_url.rsplit("/", 1)[-1] or f"meeting-{numeric_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{meeting_id}")
async def get_meeting_detail(meeting_id: str, request: Request):
    """Status dan hasil satu meeting. Dipakai untuk polling oleh aplikasi."""
    try:
        numeric_id = int(meeting_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="id meeting tidak valid")

    async with async_session_maker() as session:
        meeting = await MeetingRepository(session).get_by_id(numeric_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="Meeting tidak ditemukan")

        transcription = await TranscriptionRepository(session).get_by_meeting_id(
            numeric_id
        )
        summary = await SummaryRepository(session).get_by_meeting_id(numeric_id)

    # URL dibangun dari host permintaan, jadi otomatis benar baik saat diakses
    # lewat localhost maupun lewat tunnel/domain publik.
    download_url: str | None = None
    if meeting.pdf_url:
        download_url = str(request.url_for("download_meeting_pdf", meeting_id=meeting_id))

    status = meeting.status
    status_value = status.value if hasattr(status, "value") else str(status)

    return {
        "id": str(meeting.id),
        "title": meeting.title,
        "description": meeting.description,
        "language": meeting.language,
        "status": status_value,
        "download_url": download_url,
        "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
        "transcript": transcription.full_text if transcription else None,
        "summary": summary.summary if summary else None,
    }
