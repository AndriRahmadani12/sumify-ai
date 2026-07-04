from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, PKType, TimestampMixin, _enum_col
from src.schemas.common import ProcessingStatus

if TYPE_CHECKING:
    from src.models.processing_job import ProcessingJob
    from src.models.summary import Summary
    from src.models.transcription import Transcription
    from src.models.user import User


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
