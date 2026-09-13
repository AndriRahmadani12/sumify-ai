"""Klien LLM untuk DeepSeek (kompatibel OpenAI).

Menggantikan Apilogy. Perbedaannya dengan `src/core/llm/apilogy.py`:
- autentikasi pakai header Authorization: Bearer, bukan x-api-key
- payload wajib menyertakan "model"
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from src.core.config.setting import settings
from src.core.logging.logger import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Gagal memanggil atau memahami jawaban LLM."""


class DeepSeekService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or getattr(settings, "LLM_MODEL", "deepseek-chat")

    @property
    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "stream": False,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(self._endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"LLM HTTP {exc.response.status_code}: {exc.response.text[:300]}")
            raise LLMError(f"LLM menolak permintaan (HTTP {exc.response.status_code})") from exc
        except httpx.HTTPError as exc:
            logger.error(f"LLM tidak dapat dihubungi: {exc}")
            raise LLMError("LLM tidak dapat dihubungi") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            logger.error(f"Bentuk jawaban LLM tidak dikenali: {str(data)[:300]}")
            raise LLMError("Bentuk jawaban LLM tidak dikenali") from exc

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        raw = await self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return parse_json_response(raw)


def parse_json_response(raw: str) -> dict[str, Any]:
    """Bersihkan pagar markdown lalu parse JSON."""
    cleaned = (raw or "").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(f"Jawaban LLM bukan JSON valid: {cleaned[:300]}")
        raise LLMError("Jawaban LLM bukan JSON valid") from exc

    if not isinstance(parsed, dict):
        raise LLMError("Jawaban LLM bukan objek JSON")

    return parsed


_service: DeepSeekService | None = None


def get_llm_service() -> DeepSeekService:
    global _service
    if _service is None:
        _service = DeepSeekService()
    return _service