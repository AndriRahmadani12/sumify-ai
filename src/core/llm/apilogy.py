import os
import json
import asyncio
from functools import partial
import httpx
from typing import Any

from src.core.config.setting import settings
from src.core.logging.logger import get_logger

logger = get_logger(__name__)


class ApilogyService:
    def __init__(self, api_key: str | None = None, url: str | None = None):
        self.api_key = api_key or settings.LLM_API_KEY
        self.url = url or settings.LLM_BASE_URL

    async def generate_response(
        self,
        user_prompt: str,
        system_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str | None:

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            payload = {
                "messages": messages,
                "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
                "temperature": temperature or settings.LLM_TEMPERATURE,
                "stream": False,
            }

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None

    async def generate_json_response(
        self,
        user_prompt: str,
        system_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None
    ) -> dict[str, Any] | None:
        response = await self.generate_response(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        if not response:
            return None

        try:
            # Handle markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            # Fix double braces that LLM sometimes returns (from f-string escaping)
            if cleaned.startswith("{{") and cleaned.endswith("}}"):
                cleaned = cleaned[1:-1]

            # Also handle cases where LLM returns escaped braces
            cleaned = cleaned.replace("{{", "{").replace("}}", "}")

            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}", response_preview=response[:500])
            return None

    async def batch_generate(
        self,
        prompts: list[tuple[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None
    ) -> list[str | None]:

        tasks = [
            self.generate_response(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            for user_prompt, system_prompt in prompts
        ]

        return await asyncio.gather(*tasks)


# Global singleton instance
_apilogy_llm_service: ApilogyService | None = None


def get_apilogy_llm_service() -> ApilogyService:
    global _apilogy_llm_service
    if _apilogy_llm_service is None:
        _apilogy_llm_service = ApilogyService()
    return _apilogy_llm_service

async def main():
    llm_service = get_apilogy_llm_service()
    response = await llm_service.generate_response(
        user_prompt="Hello, how are you?",
        system_prompt="You are a helpful assistant.",
        max_tokens=100,
        temperature=0.5
    )
    logger.info(f"Response: {response}")
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
