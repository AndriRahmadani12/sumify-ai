from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, JSONType, PKType

if TYPE_CHECKING:
    from src.models.meeting import Meeting


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
