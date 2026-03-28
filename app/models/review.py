from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ReviewTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    design_document_id: int = Field(index=True)
    reviewer_name: str = Field(index=True)
    review_type: str = Field(index=True)
    assigned_by: Optional[str] = None
    status: str = Field(default="PENDING", index=True)
    comments: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
