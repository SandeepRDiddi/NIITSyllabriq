from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.groq_client import LLMUsage


class AnthropicClient:
    BASE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self.last_usage: LLMUsage | None = None

    def is_reachable(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str | None = None) -> str | None:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 6000,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
        try:
            response = httpx.post(self.BASE_URL, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage") or {}
            input_tokens = int(usage.get("input_tokens") or 0)
            output_tokens = int(usage.get("output_tokens") or 0)
            self.last_usage = LLMUsage(
                provider="anthropic",
                model=self.model,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )
            blocks = data.get("content") or []
            return "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        except Exception:
            return None
