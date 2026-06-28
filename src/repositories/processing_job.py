"""Repository untuk entitas ProcessingJob."""
from __future__ import annotations

from typing import Sequence

from src.models import ProcessingJob
from src.repositories.base import BaseRepository
from src.schemas.common import JobStatus


class ProcessingJobRepository(BaseRepository[ProcessingJob]):
    model = ProcessingJob

    async def get_by_meeting_id(self, meeting_id: int) -> Sequence[ProcessingJob]:
        """Semua job milik sebuah meeting (transcription/summarization/pdf)."""
        return await self.get_all(meeting_id=meeting_id, order_by="created_at")

    async def get_by_celery_task_id(self, task_id: str) -> ProcessingJob | None:
        """Cari job berdasarkan id task Celery (untuk tracking status async)."""
        return await self.get_by(celery_task_id=task_id)

    async def update_status(
        self, job_id: int, status: JobStatus, error: str | None = None
    ) -> ProcessingJob | None:
        """Ubah status job; isi `error` bila gagal."""
        values: dict = {"status": status}
        if error is not None:
            values["error"] = error
        return await self.update(job_id, **values)
