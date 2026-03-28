from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class TrainingDocumentRead(BaseModel):
    id: int
    title: str
    source_filename: str
    uploaded_by: str
    status: str
    summary: str
    created_at: datetime
    normalized_document: Dict[str, Any]


class WorkflowEventRead(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: int
    actor_email: str
    status: str
    details: Dict[str, Any]
    created_at: datetime


class ReportingSummaryRead(BaseModel):
    requirements_count: int
    designs_count: int
    training_documents_count: int
    primary_pending_count: int
    final_pending_count: int
    final_approved_count: int
    average_design_score: float
    recent_events: List[WorkflowEventRead]
