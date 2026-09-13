"""Klien Redis untuk keperluan di luar Celery (cache, penanda status).

Celery memakai koneksinya sendiri lewat `broker_url` dan `result_backend`,
jadi modul ini opsional dan hanya dipakai bila dibutuhkan.
"""
from __future__ import annotations

from src.core.config.setting import settings
from src.core.logging.logger import get_logger

logger = get_logger(__name__)

_client = None


def get_redis():
    """Ambil klien Redis async, dibuat sekali lalu dipakai ulang.

    Raises:
        RuntimeError: kalau paket `redis` belum terpasang.
    """
    global _client

    if _client is not None:
        return _client

    try:
        from redis import asyncio as aioredis
    except ImportError as exc:
        raise RuntimeError(
            "Paket 'redis' belum terpasang. Jalankan: pip install redis"
        ) from exc

    _client = aioredis.from_url(
        settings.result_backend,
        encoding="utf-8",
        decode_responses=True,
    )
    logger.info(f"Klien Redis dibuat: {settings.result_backend}")
    return _client


async def ping() -> bool:
    """Cek Redis hidup atau tidak. Mengembalikan False, bukan melempar error."""
    try:
        return bool(await get_redis().ping())
    except Exception as exc:
        logger.warning(f"Redis tidak dapat dihubungi: {exc}")
        return False


async def close() -> None:
    """Tutup koneksi saat aplikasi berhenti."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Koneksi Redis ditutup")
