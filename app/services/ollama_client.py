from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.generation_model = settings.ollama_generation_model
        self.embedding_model = settings.ollama_embed_model

    def is_reachable(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            response.raise_for_status()
            return True
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str | None = None) -> str | None:
        payload: dict[str, Any] = {
            "model": self.generation_model,
            "prompt": prompt,
            "stream": False,
            # Model options — critical for getting complete, high-quality output:
            # num_ctx: larger context so the full prompt + detailed 10-module table fits
            # num_predict: allow enough tokens for a rich 10-module detailed design table
            # temperature: lower = more consistent, structured JSON output
            "options": {
                "num_ctx": 8192,
                "num_predict": 6000,
                "temperature": 0.3,
                "repeat_penalty": 1.1,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        try:
            # 5-minute timeout — a 10-module detailed design table takes 2-4 min on CPU
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300.0,
            )
            response.raise_for_status()
            return response.json().get("response")
        except Exception:
            return None

    def embed(self, text: str) -> list[float] | None:
        payload = {
            "model": self.embedding_model,
            "input": text,
        }
        try:
            response = httpx.post(f"{self.base_url}/api/embed", json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings") or []
            if embeddings:
                return embeddings[0]
        except Exception:
            return None
        return None

