"""Model database untuk Meeting Summarizer.

Alur status meeting (dari sequence diagram):
UPLOADED -> TRANSCRIBING -> SUMMARIZING -> GENERATING_PDF -> COMPLETED
(FAILED ditambahkan untuk menangani error di tengah proses async.)
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------- Enum ----------

class MeetingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    TRANSCRIBING = "TRANSCRIBING"
    SUMMARIZING = "SUMMARIZING"
    GENERATING_PDF = "GENERATING_PDF"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, enum.Enum):
    TRANSCRIPTION = "TRANSCRIPTION"
    SUMMARIZATION = "SUMMARIZATION"
    PDF_GENERATION = "PDF_GENERATION"


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------- Helper kolom ----------

def _pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at():
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def _updated_at():
    return mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------- Tabel ----------

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    meetings: Mapped[list["Meeting"]] = relationship(back_populates="user")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="id")
    storage_path: Mapped[str | None] = mapped_column(String(1024))  # path audio di MinIO
    status: Mapped[MeetingStatus] = mapped_column(
        SAEnum(MeetingStatus, name="meeting_status"),
        default=MeetingStatus.UPLOADED,
        nullable=False,
        index=True,
    )
    pdf_url: Mapped[str | None] = mapped_column(String(1024))  # download_url PDF hasil
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    user: Mapped["User"] = relationship(back_populates="meetings")
    transcription: Mapped["Transcription | None"] = relationship(
        back_populates="meeting", uselist=False, cascade="all, delete-orphan"
    )
    summary: Mapped["Summary | None"] = relationship(
        back_populates="meeting", uselist=False, cascade="all, delete-orphan"
    )
    jobs: Mapped[list["ProcessingJob"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )


class Transcription(Base):
    __tablename__ = "transcriptions"

    id: Mapped[uuid.UUID] = _pk()
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        unique=True,  # 1 meeting = 1 transkrip
    )
    full_text: Mapped[str] = mapped_column(Text)
    segments: Mapped[dict | None] = mapped_column(JSONB)  # [{start, end, text}, ...]
    language: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = _created_at()

    meeting: Mapped["Meeting"] = relationship(back_populates="transcription")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = _pk()
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        unique=True,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pdf_templates.id", ondelete="SET NULL")
    )
    summary: Mapped[str] = mapped_column(Text)
    key_points: Mapped[dict | None] = mapped_column(JSONB)
    action_items: Mapped[dict | None] = mapped_column(JSONB)
    decisions: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created_at()

    meeting: Mapped["Meeting"] = relationship(back_populates="summary")
    template: Mapped["PDFTemplate | None"] = relationship(back_populates="summaries")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = _pk()
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[JobType] = mapped_column(SAEnum(JobType, name="job_type"))
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status"), default=JobStatus.QUEUED
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    meeting: Mapped["Meeting"] = relationship(back_populates="jobs")


class PDFTemplate(Base):
    __tablename__ = "pdf_templates"

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    html_content: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = _created_at()

    summaries: Mapped[list["Summary"]] = relationship(back_populates="template")
