from datetime import datetime

from celery import Task
from celery.exceptions import MaxRetriesExceededError
from src.core.logging.logger import get_logger
from src.core.config.setting import settings
from src.worker.calery_app import calery_app
import asyncio

logger = get_logger(__name__)
settings = Settings()

@celery_app.task(
    bind=True, 
    max_retries=3, 
    default_retry_delay=10, 
    queue="transcription"
)
def transcribe_audio_task(self: Task, meeting_id: int) -> dict:
    logger.info(f"Transcribing audio for meeting {meeting_id}")

    # TODO: Implement transcribe audio task
    # return asyncio.run(transcribe_audio(meeting_id))

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="pdf_generation",
)
def generate_pdf_task(self: Task, meeting_id: int) -> dict:
    logger.info("PDF generation task started", meeting_id=meeting_id, task_id=self.request.id)

    # return asyncio.run(_generate_pdf_async(self, meeting_id))

