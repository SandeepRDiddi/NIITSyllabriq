from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class GenerateDesignRequest(BaseModel):
    requested_by: str = "system"


class ReferenceRead(BaseModel):
    source_requirement_id: int
    source_design_id: Optional[int]
    source_training_document_id: Optional[int]
    source_type: str
    source_title: str
    similarity_score: float
    reused_sections: List[str]


class ScoreCardRead(BaseModel):
    requirement_coverage_score: float
    template_completeness_score: float
    technical_consistency_score: float
    reuse_relevance_score: float
    risk_quality_score: float
    review_readiness_score: float
    llm_evaluation_score: float
    overall_score: float
    missing_requirements: List[str]
    contradictions: List[str]
    notes: str


class DesignRead(BaseModel):
    id: int
    requirement_id: int
    title: str
    created_by: str
    status: str
    reused_content: bool
    similarity_score: float
    draft_content: str
    final_content: Optional[str]
    traceability_map: Dict[str, Any]
    references: List[ReferenceRead]
    scorecard: Optional[ScoreCardRead]
    created_at: datetime
    updated_at: datetime


class DesignSummaryRead(BaseModel):
    id: int
    requirement_id: int
    title: str
    created_by: str
    status: str
    similarity_score: float
    created_at: datetime
