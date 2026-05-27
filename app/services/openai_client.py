from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.groq_client import LLMUsage


class OpenAIClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        provider: str = "openai",
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.provider = provider
        self.last_usage: LLMUsage | None = None

    def is_reachable(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str | None = None) -> str | None:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 6000,
        }
        try:
            response = httpx.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage") or {}
            self.last_usage = LLMUsage(
                provider=self.provider,
                model=self.model,
                prompt_tokens=int(usage.get("prompt_tokens") or 0),
                completion_tokens=int(usage.get("completion_tokens") or 0),
                total_tokens=int(usage.get("total_tokens") or 0),
            )
            return data["choices"][0]["message"]["content"]
        except Exception:
            return None
