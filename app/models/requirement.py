from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Requirement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str
    title: str
    source_filename: str
    source_path: str
    raw_text: str
    normalized_json: str
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
