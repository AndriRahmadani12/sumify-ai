from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, PKType, TimestampMixin, _enum_col
from src.schemas.common import JobStatus, JobType

if TYPE_CHECKING:
    from src.models.meeting import Meeting


class ProcessingJob(Base, TimestampMixin):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(
        PKType, ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[JobType] = mapped_column(_enum_col(JobType, "job_type"))
    status: Mapped[JobStatus] = mapped_column(
        _enum_col(JobStatus, "job_status"), default=JobStatus.PENDING
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    error: Mapped[str | None] = mapped_column(Text)

    meeting: Mapped["Meeting"] = relationship(back_populates="jobs")
