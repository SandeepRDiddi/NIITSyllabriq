from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class RequirementCreateResponse(BaseModel):
    id: int
    customer_name: str
    title: str
    created_at: datetime
    normalized_requirement: Dict[str, Any]


class RequirementRead(BaseModel):
    id: int
    customer_name: str
    title: str
    source_filename: str
    created_by: str
    created_at: datetime


class RequirementTextCreate(BaseModel):
    """
    Used when a requirement comes in via email, call, or any other
    non-file channel. The designer types or pastes the text directly.
    """
    customer_name: str
    title: str
    raw_text: str
    source: str = "email"           # email | call_notes | teams | chat | other
    total_duration_hours: Optional[int] = None   # e.g. 40 — StackRoute programs always have a fixed duration
