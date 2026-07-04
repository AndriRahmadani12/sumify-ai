from __future__ import annotations

import enum as _py_enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    Integer,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.postgree import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")
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
