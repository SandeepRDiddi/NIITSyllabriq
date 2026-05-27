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
    chunk_count: int = 0
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


class LeadershipSummaryRead(BaseModel):
    total_users: int
    active_users_count: int
    active_tool_users_count: int
    requirements_count: int
    designs_generated_count: int
    final_approved_count: int
    rejected_or_rework_count: int
    pending_review_count: int
    pdf_exports_count: int
    success_rate: float
    average_design_score: float
    recent_events: List[WorkflowEventRead]


class LLMUsageEventRead(BaseModel):
    id: int
    provider: str
    model: str
    user_email: str
    entity_type: str
    entity_id: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    created_at: datetime


class LLMUsageByUserRead(BaseModel):
    user_email: str
    calls_count: int
    total_tokens: int
    estimated_cost: float


class LLMUsageSummaryRead(BaseModel):
    total_calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    by_user: List[LLMUsageByUserRead]
    recent_events: List[LLMUsageEventRead]
