"""Pemilih prompt berdasarkan jenis template ringkasan."""
from __future__ import annotations

from dataclasses import dataclass

from src.prompts import summary_template_a, summary_template_b, summary_template_c


@dataclass(frozen=True)
class PromptSpec:
    """Sepasang prompt siap kirim ke LLM, plus template PDF yang cocok."""

    template_type: str
    system_prompt: str
    user_prompt: str
    pdf_template: str


_MODULES = {
    "simple": (summary_template_a, "simple"),
    "business": (summary_template_b, "business"),
    "study": (summary_template_c, "simple"),
}

_ALIASES = {
    "simple_summary": "simple",
    "a": "simple",
    "business_summary": "business",
    "b": "business",
    "study_summary": "study",
    "c": "study",
}


def available_types() -> list[str]:
    return list(_MODULES.keys())


def build_prompt(template_type: str, transcript: str) -> PromptSpec:
    """Ambil prompt untuk satu jenis template.

    Raises:
        ValueError: kalau jenis template tidak dikenal.
    """
    if not transcript or not transcript.strip():
        raise ValueError("Transkrip kosong, tidak ada yang bisa diringkas.")

    key = template_type.strip().lower()
    key = _ALIASES.get(key, key)

    entry = _MODULES.get(key)
    if entry is None:
        raise ValueError(
            f"Jenis template '{template_type}' tidak dikenal. "
            f"Pilihan: {', '.join(_MODULES)}"
        )

    module, pdf_template = entry

    return PromptSpec(
        template_type=key,
        system_prompt=module.SYSTEM_PROMPT,
        user_prompt=module.build_user_prompt(transcript),
        pdf_template=pdf_template,
    )