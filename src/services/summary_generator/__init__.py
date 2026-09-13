"""Service pembuat ringkasan dari transkrip menggunakan LLM."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.core.logging.logger import get_logger
from src.prompts.prompt_handler import build_prompt
from src.utils.llm import DeepSeekService, LLMError, get_llm_service

logger = get_logger(__name__)

# Field yang wajib ada per jenis template, dipakai untuk mengisi kekosongan
# kalau LLM lupa mengeluarkan salah satunya.
_REQUIRED_FIELDS: dict[str, dict[str, Any]] = {
    "simple": {
        "title": "",
        "summary": "",
        "key_points": [],
        "keywords": [],
        "action_items": [],
    },
    "business": {
        "title": "",
        "executive_summary": "",
        "key_discussion_points": [],
        "decisions": [],
        "next_steps": [],
        "action_assignment": [],
    },
}


@dataclass
class SummaryResult:
    """Hasil ringkasan siap dipakai PDF generator maupun disimpan ke DB."""

    template_type: str
    pdf_template: str
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def summary_text(self) -> str:
        """Teks ringkasan utama, apa pun jenis templatenya."""
        return self.context.get("summary") or self.context.get("executive_summary") or ""

    @property
    def key_points(self) -> list:
        return (
            self.context.get("key_points")
            or self.context.get("key_discussion_points")
            or []
        )

    @property
    def action_items(self) -> list:
        return (
            self.context.get("action_items")
            or self.context.get("action_assignment")
            or []
        )

    @property
    def decisions(self) -> list:
        return self.context.get("decisions") or []


class SummaryGeneratorService:
    def __init__(self, llm: DeepSeekService | None = None) -> None:
        self.llm = llm or get_llm_service()

    async def generate(
        self,
        transcript: str,
        template_type: str = "simple",
        audio_filename: str | None = None,
        language: str = "id",
        duration: str | None = None,
    ) -> SummaryResult:
        """Ubah transkrip jadi ringkasan terstruktur.

        Raises:
            ValueError: template_type tidak dikenal atau transkrip kosong.
            LLMError: LLM gagal dihubungi atau jawabannya tidak bisa dipakai.
        """
        spec = build_prompt(template_type, transcript)

        logger.info(
            f"Membuat ringkasan: template={spec.template_type}, "
            f"panjang transkrip={len(transcript)} karakter"
        )

        data = await self.llm.generate_json(
            system_prompt=spec.system_prompt,
            user_prompt=spec.user_prompt,
        )

        context = self._normalize(data, spec.pdf_template)
        context.update(
            self._metadata(
                audio_filename=audio_filename,
                language=language,
                duration=duration,
            )
        )

        return SummaryResult(
            template_type=spec.template_type,
            pdf_template=spec.pdf_template,
            context=context,
        )

    def _normalize(self, data: dict[str, Any], pdf_template: str) -> dict[str, Any]:
        """Pastikan semua field wajib ada, isi yang kosong dengan default."""
        required = _REQUIRED_FIELDS.get(pdf_template, _REQUIRED_FIELDS["simple"])
        context = dict(data)

        missing = []
        for key, default in required.items():
            value = context.get(key)
            if value in (None, ""):
                context[key] = default
                missing.append(key)

        if missing:
            logger.warning(f"LLM tidak mengeluarkan field: {', '.join(missing)}")

        if not context.get("title"):
            context["title"] = "Ringkasan Rapat"

        return context

    def _metadata(
        self,
        audio_filename: str | None,
        language: str,
        duration: str | None,
    ) -> dict[str, str]:
        language_label = {"id": "Indonesia", "en": "English"}.get(language, language)

        return {
            "audio_filename": audio_filename or "-",
            "generated_date": datetime.now().strftime("%d %B %Y"),
            "language": language_label,
            "duration": duration or "-",
        }


_service: SummaryGeneratorService | None = None


def get_summary_service() -> SummaryGeneratorService:
    global _service
    if _service is None:
        _service = SummaryGeneratorService()
    return _service