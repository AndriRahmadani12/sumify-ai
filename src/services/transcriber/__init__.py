"""Transkripsi audio memakai faster-whisper (jalan lokal, tanpa API).

Dipilih faster-whisper, bukan openai-whisper, karena tidak butuh ffmpeg
terpasang terpisah dan jauh lebih ringan di CPU.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.config.setting import settings
from src.core.logging.logger import get_logger

logger = get_logger(__name__)


class TranscriptionError(Exception):
    """Transkripsi gagal."""


@dataclass
class TranscriptionResult:
    full_text: str
    language: str
    duration: float
    segments: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_label(self) -> str:
        """Durasi dalam bentuk '42 menit 10 detik'."""
        total = int(self.duration)
        minutes, seconds = divmod(total, 60)
        if minutes:
            return f"{minutes} menit {seconds} detik"
        return f"{seconds} detik"


class WhisperTranscriber:
    """Pembungkus faster-whisper. Model dimuat sekali lalu dipakai ulang."""

    _model = None  # dibagi antar instance, memuat model itu mahal

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        self.model_size = model_size or settings.WHISPER_MODEL
        self.device = device or settings.WHISPER_DEVICE
        self.compute_type = compute_type or settings.WHISPER_COMPUTE_TYPE

    def _load_model(self):
        if WhisperTranscriber._model is not None:
            return WhisperTranscriber._model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError(
                "Paket 'faster-whisper' belum terpasang. "
                "Jalankan: pip install faster-whisper"
            ) from exc

        logger.info(
            f"Memuat model Whisper '{self.model_size}' "
            f"(device={self.device}, compute_type={self.compute_type}). "
            "Pemanggilan pertama akan mengunduh model, mohon tunggu."
        )

        WhisperTranscriber._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        return WhisperTranscriber._model

    def _transcribe_sync(self, audio_path: str, language: str | None) -> TranscriptionResult:
        model = self._load_model()

        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=1,          # lebih cepat, cukup untuk notulen
            vad_filter=True,      # buang bagian hening
        )

        collected: list[dict[str, Any]] = []
        parts: list[str] = []

        for segment in segments:  # generator, baru jalan saat diiterasi
            text = segment.text.strip()
            if not text:
                continue
            parts.append(text)
            collected.append(
                {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": text,
                }
            )

        full_text = " ".join(parts).strip()

        if not full_text:
            raise TranscriptionError(
                "Tidak ada ucapan yang terdeteksi pada audio ini."
            )

        return TranscriptionResult(
            full_text=full_text,
            language=info.language,
            duration=info.duration,
            segments=collected,
        )

    async def transcribe(
        self,
        audio_path: str | Path,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transkrip satu berkas audio.

        Args:
            audio_path: lokasi berkas audio di disk.
            language: kode bahasa ('id', 'en'). None berarti deteksi otomatis.
        """
        path = Path(audio_path)
        if not path.exists():
            raise TranscriptionError(f"Berkas audio tidak ditemukan: {path}")

        logger.info(f"Mulai transkripsi: {path.name}")

        try:
            result = await asyncio.to_thread(
                self._transcribe_sync, str(path), language
            )
        except TranscriptionError:
            raise
        except Exception as exc:
            logger.error(f"Transkripsi gagal untuk {path.name}: {exc}")
            raise TranscriptionError(f"Transkripsi gagal: {exc}") from exc

        logger.info(
            f"Transkripsi selesai: {len(result.full_text)} karakter, "
            f"{len(result.segments)} segmen, bahasa={result.language}"
        )
        return result


_transcriber: WhisperTranscriber | None = None


def get_transcriber() -> WhisperTranscriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = WhisperTranscriber()
    return _transcriber