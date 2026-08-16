from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, ClassVar

from src.core.config.setting import settings


class WhisperModelManager:

    _instance: ClassVar[WhisperModelManager | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> WhisperModelManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
    ) -> None:
        if getattr(self, "_initialized", False):
            return
        self._model_size = model_size or settings.WHISPER_MODEL_SIZE or "base"
        self._device = device or settings.WHISPER_DEVICE
        self._model: Any | None = None
        self._initialized = True

    @classmethod
    def get_instance(
        cls,
        model_size: str | None = None,
        device: str | None = None,
    ) -> WhisperModelManager:
        if cls._instance is None:
            cls(model_size, device)
        return cls._instance

    def _load_model(self) -> None:
        if self._model is not None:
            return
        import whisper

        self._model = whisper.load_model(self._model_size, device=self._device)

    def transcribe(self, audio_path: str | Path, **options: Any) -> dict[str, Any]:
        self._load_model()
        return self._model.transcribe(str(audio_path), **options)
