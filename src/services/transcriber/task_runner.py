from __future__ import annotations

from typing import Any

from celery import Task
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.postgree import async_session_maker
from src.core.logging.logger import get_logger
from src.models import ProcessingJob
from src.repositories.meeting import MeetingRepository
from src.repositories.processing_job import ProcessingJobRepository
from src.schemas.common import JobStatus, JobType, ProcessingStatus
from src.services.transcriber.transcriber_service import TranscriberService

logger = get_logger(__name__)


class TranscriptionTaskRunner:

    def __init__(
        self,
        task: Task,
        transcriber_service: TranscriberService | None = None,
    ) -> None:
        self.task = task
        self.transcriber_service = transcriber_service or TranscriberService()

    async def run(self, meeting_id: int) -> dict[str, Any]:
        async with async_session_maker() as session:
            return await self._execute(session, meeting_id)

    async def _execute(
        self,
        session: AsyncSession,
        meeting_id: int,
    ) -> dict[str, Any]:
        job_repo = ProcessingJobRepository(session)
        meeting_repo = MeetingRepository(session)

        job = await self._get_or_create_job(job_repo, meeting_id)

        try:
            await meeting_repo.update_status(meeting_id, ProcessingStatus.TRANSCRIBING)
            transcription = await self.transcriber_service.transcribe_meeting(
                meeting_id, session
            )
            await job_repo.update_status(job.id, JobStatus.SUCCESS)
            await meeting_repo.update_status(meeting_id, ProcessingStatus.SUMMARIZING)

            return {
                "job_id": job.id,
                "transcription_id": transcription.id,
                "status": JobStatus.SUCCESS.value,
            }

        except Exception as exc:
            error_msg = str(exc)
            logger.error(
                "Transcription failed",
                meeting_id=meeting_id,
                task_id=self.task.request.id,
                error=error_msg,
            )
            await job_repo.update_status(job.id, JobStatus.FAILURE, error=error_msg)

            try:
                raise self.task.retry(exc=exc) from exc
            except MaxRetriesExceededError:
                await meeting_repo.update_status(meeting_id, ProcessingStatus.FAILED)
                raise

    async def _get_or_create_job(
        self,
        job_repo: ProcessingJobRepository,
        meeting_id: int,
    ) -> ProcessingJob:
        """Reuse job dari retry sebelumnya atau buat job baru."""
        task_id = self.task.request.id

        if task_id:
            existing = await job_repo.get_by_celery_task_id(task_id)
            if existing:
                status = (
                    JobStatus.RETRY
                    if self.task.request.retries > 0
                    else JobStatus.STARTED
                )
                updated = await job_repo.update_status(existing.id, status)
                return updated or existing

        return await job_repo.create(
            meeting_id=meeting_id,
            job_type=JobType.TRANSCRIPTION,
            status=JobStatus.STARTED,
            celery_task_id=task_id,
        )
