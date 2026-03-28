from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TrainingDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source_filename: str
    source_path: str
    content_type: str
    raw_text: str
    normalized_json: str
    summary: str
    uploaded_by: str = Field(index=True)
    status: str = Field(default="ACTIVE", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class WorkflowEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)
    entity_type: str = Field(index=True)
    entity_id: int = Field(index=True)
    actor_email: str = Field(index=True)
    status: str = Field(index=True)
    details_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
