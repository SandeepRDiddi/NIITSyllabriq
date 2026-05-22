from __future__ import annotations

import httpx

from app.core.config import settings


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
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return None
