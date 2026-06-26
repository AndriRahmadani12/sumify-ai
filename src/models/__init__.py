"""Model ORM (SQLAlchemy 2.0, async-ready) untuk Sumify AI.

Catatan desain:
- Primary key memakai INTEGER auto-increment, menyesuaikan kode tim yang sudah ada
  (worker & storage memakai meeting_id: int, user_id: int).
- Enum status diambil dari src/schemas/common.py (sumber tunggal), bukan didefinisikan
  ulang, supaya konsisten dengan layer lain.
- Kolom JSON otomatis menjadi JSONB di PostgreSQL, JSON biasa di database lain.
"""
from __future__ import annotations

import enum as _py_enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Integer,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.postgree import Base
from src.schemas.common import JobStatus, JobType, ProcessingStatus

# JSON yang jadi JSONB di Postgres, tetap JSON di SQLite (memudahkan testing)
JSONType = JSON().with_variant(JSONB(), "postgresql")
# BIGINT di Postgres, INTEGER di SQLite (agar auto-increment jalan saat testing)
PKType = BigInteger().with_variant(Integer(), "sqlite")


def _enum_col(enum_cls: type[_py_enum.Enum], name: str):
    """Kolom enum yang menyimpan VALUE (lowercase), bukan NAME."""
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda e: [m.value for m in e],
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))

    meetings: Mapped[list["Meeting"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Meeting(Base, TimestampMixin):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        PKType, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="id")
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    storage_bucket: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ProcessingStatus] = mapped_column(
        _enum_col(ProcessingStatus, "processing_status"),
        default=ProcessingStatus.UPLOADED,
        index=True,
    )
    pdf_url: Mapped[str | None] = mapped_column(String(1024))

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

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(
        PKType, ForeignKey("meetings.id", ondelete="CASCADE"), unique=True
    )
    full_text: Mapped[str | None] = mapped_column(Text)
    segments: Mapped[list | None] = mapped_column(JSONType)
    language: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="transcription")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(
        PKType, ForeignKey("meetings.id", ondelete="CASCADE"), unique=True
    )
    template_id: Mapped[int | None] = mapped_column(
        PKType, ForeignKey("pdf_templates.id", ondelete="SET NULL")
    )
    summary: Mapped[str | None] = mapped_column(Text)
    key_points: Mapped[list | None] = mapped_column(JSONType)
    action_items: Mapped[list | None] = mapped_column(JSONType)
    decisions: Mapped[list | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meeting: Mapped["Meeting"] = relationship(back_populates="summary")
    template: Mapped["PDFTemplate | None"] = relationship(back_populates="summaries")


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


class PDFTemplate(Base):
    __tablename__ = "pdf_templates"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    html_content: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    summaries: Mapped[list["Summary"]] = relationship(back_populates="template")


__all__ = [
    "Base",
    "User",
    "Meeting",
    "Transcription",
    "Summary",
    "ProcessingJob",
    "PDFTemplate",
]
