from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str
    ollama_reachable: bool


class MessageResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
