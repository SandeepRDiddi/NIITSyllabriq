from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings


@dataclass
class LLMUsage:
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class GroqClient:
    """
    Drop-in replacement for OllamaClient using the Groq API.
    Groq runs llama-3.3-70b at ~500 tokens/sec — a 10-module design
    completes in under 30 seconds vs 3-5 minutes on a local CPU.

    Set LLM_PROVIDER=groq and GROQ_API_KEY in your .env file to activate.
    """

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self) -> None:
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
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
            response = httpx.post(self.BASE_URL, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage") or {}
            self.last_usage = LLMUsage(
                provider="groq",
                model=self.model,
                prompt_tokens=int(usage.get("prompt_tokens") or 0),
                completion_tokens=int(usage.get("completion_tokens") or 0),
                total_tokens=int(usage.get("total_tokens") or 0),
            )
            return data["choices"][0]["message"]["content"]
        except Exception:
            return None
