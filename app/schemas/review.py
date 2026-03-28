from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReviewSubmitRequest(BaseModel):
    reviewer_name: str
    decision: str
    comments: str = ""


class ReviewTaskRead(BaseModel):
    id: int
    design_document_id: int
    reviewer_name: str
    review_type: str
    assigned_by: Optional[str]
    status: str
    comments: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime
