"""Pipeline utama: transkrip -> ringkasan -> PDF, sambil memperbarui status DB.

Dijalankan sinkron di dalam request (belum lewat Celery). Begitu Redis tersedia,
fungsi `summarize_and_generate_pdf` tinggal dipanggil dari task worker.
"""
from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.core.database.postgree import async_session_maker
from src.core.logging.logger import get_logger
from src.repositories import (
    MeetingRepository,
    SummaryRepository,
    TranscriptionRepository,
)
from src.schemas.common import ProcessingStatus
from src.services.pdf_generator.pdf_generator_service import PDFGeneratorService
from src.services.storage.storage import storage_service
from src.services.summary_generator import get_summary_service
from src.services.transcriber import TranscriptionError, get_transcriber

logger = get_logger(__name__)


class PipelineError(Exception):
    """Pipeline gagal di salah satu tahap."""


@dataclass
class PipelineResult:
    meeting_id: int
    template_type: str
    pdf_path: str
    pdf_url: str | None
    summary_id: int


async def summarize_and_generate_pdf(
    meeting_id: int,
    template_type: str = "simple",
    upload_pdf: bool = True,
) -> PipelineResult:
    """Ambil transkrip meeting, ringkas dengan LLM, lalu hasilkan PDF.

    Prasyarat: meeting sudah punya transcription. Kalau belum ada, angkat error.
    """
    async with async_session_maker() as session:
        meeting_repo = MeetingRepository(session)
        transcription_repo = TranscriptionRepository(session)
        summary_repo = SummaryRepository(session)

        meeting = await meeting_repo.get_by_id(meeting_id)
        if meeting is None:
            raise PipelineError(f"Meeting {meeting_id} tidak ditemukan")

        transcription = await transcription_repo.get_by_meeting_id(meeting_id)
        if transcription is None or not (transcription.full_text or "").strip():
            raise PipelineError(
                f"Meeting {meeting_id} belum punya transkrip. "
                "Jalankan transkripsi lebih dulu."
            )

        audio_filename = Path(meeting.storage_path or "").name or None

        # ── Tahap 1: ringkasan ──
        await meeting_repo.update_status(meeting_id, ProcessingStatus.SUMMARIZING)

        try:
            result = await get_summary_service().generate(
                transcript=transcription.full_text,
                template_type=template_type,
                audio_filename=audio_filename,
                language=meeting.language or "id",
            )
        except Exception as exc:
            await meeting_repo.update_status(meeting_id, ProcessingStatus.FAILED)
            logger.error(f"Ringkasan gagal untuk meeting {meeting_id}: {exc}")
            raise PipelineError(f"Gagal membuat ringkasan: {exc}") from exc

        existing = await summary_repo.get_by_meeting_id(meeting_id)
        summary_values = {
            "summary": result.summary_text,
            "key_points": result.key_points,
            "action_items": result.action_items,
            "decisions": result.decisions,
        }

        if existing is None:
            summary_row = await summary_repo.create(
                meeting_id=meeting_id, **summary_values
            )
        else:
            summary_row = await summary_repo.update(existing.id, **summary_values)

        # ── Tahap 2: PDF ──
        await meeting_repo.update_status(meeting_id, ProcessingStatus.GENERATING_PDF)

        try:
            pdf_path = await asyncio.to_thread(
                PDFGeneratorService().generate_pdf,
                result.pdf_template,
                result.context,
                f"meeting-{meeting_id}-{result.template_type}.pdf",
            )
        except Exception as exc:
            await meeting_repo.update_status(meeting_id, ProcessingStatus.FAILED)
            logger.error(f"PDF gagal untuk meeting {meeting_id}: {exc}")
            raise PipelineError(f"Gagal membuat PDF: {exc}") from exc

        # ── Tahap 3: simpan PDF ke storage (opsional) ──
        pdf_url: str | None = None
        if upload_pdf:
            try:
                info = await storage_service.upload_pdf(
                    file_data=Path(pdf_path).read_bytes(),
                    meeting_id=meeting_id,
                    filename=Path(pdf_path).name,
                )
                pdf_url = await storage_service.get_file_url(info.storage_path)
                await meeting_repo.update(meeting_id, pdf_url=info.storage_path)
            except Exception as exc:
                logger.warning(
                    f"PDF meeting {meeting_id} jadi tapi gagal diunggah: {exc}"
                )

        await meeting_repo.update_status(meeting_id, ProcessingStatus.COMPLETED)
        logger.info(f"Pipeline selesai untuk meeting {meeting_id}: {pdf_path}")

        return PipelineResult(
            meeting_id=meeting_id,
            template_type=result.template_type,
            pdf_path=str(pdf_path),
            pdf_url=pdf_url,
            summary_id=summary_row.id,
        )


async def transcribe_meeting_audio(
    meeting_id: int,
    language: str | None = None,
) -> dict:
    """Unduh audio meeting dari storage lalu transkripsikan dengan Whisper.

    Raises:
        PipelineError: meeting tidak ada, tanpa audio, atau transkripsi gagal.
    """
    async with async_session_maker() as session:
        meeting_repo = MeetingRepository(session)
        meeting = await meeting_repo.get_by_id(meeting_id)

        if meeting is None:
            raise PipelineError(f"Meeting {meeting_id} tidak ditemukan")
        if not meeting.storage_path:
            raise PipelineError(f"Meeting {meeting_id} tidak punya berkas audio")

        await meeting_repo.update_status(meeting_id, ProcessingStatus.TRANSCRIBING)

    tmp_path: Path | None = None

    try:
        # Whisper membaca dari disk, jadi audio diunduh ke berkas sementara.
        audio_bytes = await storage_service.download_file(meeting.storage_path)
        suffix = Path(meeting.storage_path).suffix or ".mp3"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = Path(tmp.name)

        result = await get_transcriber().transcribe(
            tmp_path, language=language or meeting.language or None
        )
    except TranscriptionError as exc:
        async with async_session_maker() as session:
            await MeetingRepository(session).update_status(
                meeting_id, ProcessingStatus.FAILED
            )
        raise PipelineError(str(exc)) from exc
    except Exception as exc:
        async with async_session_maker() as session:
            await MeetingRepository(session).update_status(
                meeting_id, ProcessingStatus.FAILED
            )
        logger.error(f"Transkripsi meeting {meeting_id} gagal: {exc}")
        raise PipelineError(f"Transkripsi gagal: {exc}") from exc
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    async with async_session_maker() as session:
        transcription_repo = TranscriptionRepository(session)
        values = {
            "full_text": result.full_text,
            "segments": result.segments,
            "language": result.language,
        }

        existing = await transcription_repo.get_by_meeting_id(meeting_id)
        if existing is None:
            row = await transcription_repo.create(meeting_id=meeting_id, **values)
        else:
            row = await transcription_repo.update(existing.id, **values)

        await MeetingRepository(session).update_status(
            meeting_id, ProcessingStatus.UPLOADED
        )

    return {
        "transcription_id": row.id,
        "language": result.language,
        "duration": result.duration_label,
        "segments": len(result.segments),
        "length": len(result.full_text),
        "preview": result.full_text[:300],
    }


async def regenerate_pdf_from_summary(
    meeting_id: int,
    template_type: str = "simple",
) -> Path:
    """Cetak ulang PDF dari ringkasan yang sudah tersimpan, tanpa memanggil LLM."""
    from src.prompts.prompt_handler import build_prompt

    async with async_session_maker() as session:
        meeting = await MeetingRepository(session).get_by_id(meeting_id)
        if meeting is None:
            raise PipelineError(f"Meeting {meeting_id} tidak ditemukan")

        summary = await SummaryRepository(session).get_by_meeting_id(meeting_id)
        if summary is None:
            raise PipelineError(
                f"Meeting {meeting_id} belum punya ringkasan. Jalankan summarize dulu."
            )

    spec = build_prompt(template_type, "placeholder")

    language_label = {"id": "Indonesia", "en": "English"}.get(
        meeting.language or "id", meeting.language or "-"
    )
    audio_filename = (
        meeting.description or Path(meeting.storage_path or "").name or "-"
    )

    context = {
        "title": meeting.title or "Ringkasan Rapat",
        "audio_filename": audio_filename,
        "generated_date": datetime.now().strftime("%d %B %Y"),
        "language": language_label,
        "duration": "-",
    }

    if spec.pdf_template == "business":
        context.update(
            {
                "executive_summary": summary.summary or "",
                "key_discussion_points": summary.key_points or [],
                "decisions": summary.decisions or [],
                "next_steps": [],
                "action_assignment": summary.action_items or [],
            }
        )
    else:
        context.update(
            {
                "summary": summary.summary or "",
                "key_points": summary.key_points or [],
                "keywords": [],
                "action_items": summary.action_items or [],
            }
        )

    pdf_path = await asyncio.to_thread(
        PDFGeneratorService().generate_pdf,
        spec.pdf_template,
        context,
        f"meeting-{meeting_id}-{spec.template_type}.pdf",
    )
    return Path(pdf_path)
