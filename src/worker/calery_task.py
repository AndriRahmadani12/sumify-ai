"""Task Celery untuk pekerjaan berat: transkripsi, ringkasan, dan cetak PDF.

Setiap task hanya membungkus fungsi async yang sudah dipakai dan diuji lewat
endpoint HTTP, jadi logikanya tidak digandakan.

Menjalankan worker (butuh Redis hidup):

    celery -A src.worker.calery_app.calery_app worker --loglevel=info \\
        --pool=solo -Q default,transcription,summarization,pdf_generation

Dua opsi itu wajib:
- --pool=solo karena pool prefork bawaan Celery tidak jalan di Windows
- -Q ... karena tanpa itu worker hanya mendengarkan queue "default",
  sedangkan task-task di bawah dikirim ke queue transcription,
  summarization, dan pdf_generation

Mengirim task dari Python:

    from src.worker.calery_task import generate_summary_task
    result = generate_summary_task.delay(meeting_id=3, template_type="business")
    print(result.get(timeout=300))
"""
from __future__ import annotations

import asyncio

from celery import Task

from src.core.logging.logger import get_logger
from src.worker.calery_app import calery_app

logger = get_logger(__name__)


def _run(coro):
    """Jalankan coroutine di dalam worker Celery yang sinkron."""
    return asyncio.run(coro)


@calery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    queue="transcription",
)
def transcribe_audio_task(self: Task, meeting_id: int) -> dict:
    """Transkripsikan audio milik satu meeting memakai Whisper."""
    logger.info(f"Task transkripsi dimulai untuk meeting {meeting_id}")

    from src.services.pipeline.main_pipeline import transcribe_meeting_audio

    try:
        result = _run(transcribe_meeting_audio(meeting_id))
    except Exception as exc:
        logger.error(f"Task transkripsi gagal untuk meeting {meeting_id}: {exc}")
        raise self.retry(exc=exc)

    return {
        "meeting_id": meeting_id,
        "transcription_id": result["transcription_id"],
        "language": result["language"],
        "length": result["length"],
    }


@calery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="summarization",
)
def generate_summary_task(self: Task, meeting_id: int, template_type: str = "simple") -> dict:
    """Ringkas transkrip lalu cetak PDF."""
    logger.info(f"Task ringkasan dimulai untuk meeting {meeting_id}")

    from src.services.pipeline.main_pipeline import summarize_and_generate_pdf

    try:
        result = _run(summarize_and_generate_pdf(meeting_id, template_type))
    except Exception as exc:
        logger.error(f"Task ringkasan gagal untuk meeting {meeting_id}: {exc}")
        raise self.retry(exc=exc)

    return {
        "meeting_id": result.meeting_id,
        "template_type": result.template_type,
        "summary_id": result.summary_id,
        "pdf_path": result.pdf_path,
        "pdf_url": result.pdf_url,
    }


@calery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="pdf_generation",
)
def generate_pdf_task(self: Task, meeting_id: int, template_type: str = "simple") -> dict:
    """Cetak PDF dari ringkasan yang sudah tersimpan, tanpa memanggil LLM lagi."""
    logger.info(f"Task cetak PDF dimulai untuk meeting {meeting_id}")

    from src.services.pipeline.main_pipeline import regenerate_pdf_from_summary

    try:
        pdf_path = _run(regenerate_pdf_from_summary(meeting_id, template_type))
    except Exception as exc:
        logger.error(f"Task cetak PDF gagal untuk meeting {meeting_id}: {exc}")
        raise self.retry(exc=exc)

    return {"meeting_id": meeting_id, "pdf_path": str(pdf_path)}


@calery_app.task(queue="transcription")
def full_pipeline_task(meeting_id: int, template_type: str = "simple") -> dict:
    """Rangkaian penuh: transkripsi lalu ringkasan dan PDF, berurutan."""
    logger.info(f"Pipeline penuh dimulai untuk meeting {meeting_id}")
    transcribe_audio_task.run(meeting_id)
    return generate_summary_task.run(meeting_id, template_type)