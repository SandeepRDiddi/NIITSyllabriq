from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DesignDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    requirement_id: int = Field(index=True)
    title: str
    created_by: str = Field(index=True)
    status: str = Field(default="DRAFT_GENERATED", index=True)
    template_version: str = Field(default="NIIT-v1")
    reused_content: bool = Field(default=False)
    similarity_score: float = Field(default=0.0)
    draft_content: str
    final_content: Optional[str] = None
    draft_path: Optional[str] = None
    final_path: Optional[str] = None
    traceability_map: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RetrievedReference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    design_document_id: int = Field(index=True)
    source_requirement_id: int = Field(index=True)
    source_design_id: Optional[int] = Field(default=None, index=True)
    source_training_document_id: Optional[int] = Field(default=None, index=True)
    source_type: str = Field(default="requirement", index=True)
    source_title: str
    similarity_score: float
    reused_sections: str


class ScoreCard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    design_document_id: int = Field(index=True, unique=True)
    requirement_coverage_score: float
    template_completeness_score: float
    technical_consistency_score: float
    reuse_relevance_score: float
    risk_quality_score: float
    review_readiness_score: float
    llm_evaluation_score: float
    overall_score: float
    missing_requirements: str
    contradictions: str
    notes: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
