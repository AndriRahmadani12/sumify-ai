import asyncio
from datetime import datetime

from celery import Task
from celery.exceptions import MaxRetriesExceededError

from src.core.logging.logger import get_logger
from src.services.transcriber.task_runner import TranscriptionTaskRunner
from src.worker.calery_app import calery_app

logger = get_logger(__name__)


@calery_app.task(
    bind=True,
    name="sumify_ai.tasks.transcribe_audio",
    max_retries=3,
    default_retry_delay=10,
    queue="transcription",
)
def transcribe_audio_task(self: Task, meeting_id: int) -> dict:
    """Task Celery untuk transkripsi audio meeting.

    - Tracking `ProcessingJob` di DB (STARTED -> RETRY/SUCCESS/FAILURE).
    - Update status meeting (TRANSCRIBING -> SUMMARIZING/FAILED).
    - Model Whisper di-load sekali per worker process via singleton.
    """
    logger.info(
        "Transcribing audio for meeting",
        meeting_id=meeting_id,
        task_id=self.request.id,
        retries=self.request.retries,
    )
    return asyncio.run(TranscriptionTaskRunner(self).run(meeting_id))


@calery_app.task(
    bind=True,
    name="sumify_ai.tasks.generate_summary",
    max_retries=3,
    default_retry_delay=60,
    queue="summarization",
)
def generate_summary_task(self: Task, meeting_id: int) -> dict:
    logger.info(
        "Summary generation task started",
        meeting_id=meeting_id,
        task_id=self.request.id,
    )
    # TODO: Implement summary generation task
    return {"status": "pending", "meeting_id": meeting_id}


@calery_app.task(
    bind=True,
    name="sumify_ai.tasks.generate_pdf",
    max_retries=3,
    default_retry_delay=60,
    queue="pdf_generation",
)
def generate_pdf_task(self: Task, meeting_id: int) -> dict:
    logger.info(
        "PDF generation task started",
        meeting_id=meeting_id,
        task_id=self.request.id,
    )
    # TODO: Implement PDF generation task
    return {"status": "pending", "meeting_id": meeting_id}
