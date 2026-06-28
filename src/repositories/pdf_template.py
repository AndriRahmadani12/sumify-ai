"""Repository untuk entitas PDFTemplate."""
from __future__ import annotations

from typing import Sequence

from src.models import PDFTemplate
from src.repositories.base import BaseRepository


class PDFTemplateRepository(BaseRepository[PDFTemplate]):
    model = PDFTemplate

    async def get_active(self) -> Sequence[PDFTemplate]:
        """Hanya template yang aktif (untuk endpoint /list-template nanti)."""
        return await self.get_all(is_active=True)

    async def get_by_name(self, name: str) -> PDFTemplate | None:
        """Cari template berdasarkan nama."""
        return await self.get_by(name=name)
