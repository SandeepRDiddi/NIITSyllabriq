from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DiscoveryAnswers(BaseModel):
    """
    Structured answers to the 11-question Discovery Questionnaire.
    Additive companion to raw_text — every field is optional so the
    questionnaire can be partially filled without blocking submission.
    """
    domain_focus: List[str] = []                       # Q1 — why are we discussing this requirement (domain focus)
    target_audience_roles: List[str] = []               # Q2 — target audience roles
    experience_level: Optional[str] = None               # Q3 — learner experience level
    learner_count: Optional[int] = None                  # Q4 — expected number of learners
    trigger: Optional[str] = None                        # Q5 — what triggered this requirement
    delivery_model: Optional[str] = None                 # Q6 — preferred delivery model
    timeline: Optional[str] = None                       # Q7 — expected programme timeline
    constraints: Optional[str] = None                    # Q8 — known constraints
    strategic_objective: List[str] = []                  # Q9 — linked business/strategic objective
    prior_vendor_experience: Optional[str] = None         # Q10 — prior vendor/training partner experience
    expected_business_outcomes: List[str] = []           # Q11 — expected business outcomes


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
    discovery: Optional[DiscoveryAnswers] = None  # structured Discovery Questionnaire answers (optional companion)
