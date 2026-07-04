from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, JSONType, PKType

if TYPE_CHECKING:
    from src.models.meeting import Meeting
    from src.models.pdf_template import PDFTemplate


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
