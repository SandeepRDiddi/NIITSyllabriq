from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


LLMProvider = Literal["ollama", "groq", "anthropic", "openai", "openai_compatible"]


class LLMProviderConfigRead(BaseModel):
    id: int
    provider: str
    model: str
    base_url: str
    is_active: bool
    has_api_key: bool
    updated_by: str
    updated_at: datetime


class LLMProviderConfigUpdate(BaseModel):
    provider: LLMProvider
    model: str
    base_url: str = ""
    api_key: str | None = None
