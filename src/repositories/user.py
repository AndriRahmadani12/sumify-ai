"""Repository untuk entitas User."""
from __future__ import annotations

from src.models import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Cari user berdasarkan email (dipakai saat login/registrasi)."""
        return await self.get_by(email=email)

    async def email_exists(self, email: str) -> bool:
        """Cek apakah email sudah terpakai."""
        return await self.exists(email=email)
