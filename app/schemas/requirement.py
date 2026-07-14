from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# Question key -> human label, used to report exactly which questions are
# unanswered when a requirement fails the design-qualification check.
DISCOVERY_QUESTION_LABELS: Dict[str, str] = {
    "domain_focus": "Q1 domain focus",
    "target_audience_roles": "Q2 target audience",
    "experience_level": "Q3 experience level",
    "learner_count": "Q4 learner count",
    "trigger": "Q5 trigger",
    "delivery_model": "Q6 delivery model",
    "timeline": "Q7 timeline",
    "constraints": "Q8 constraints",
    "strategic_objective": "Q9 strategic objective",
    "prior_vendor_experience": "Q10 prior vendor experience",
    "expected_business_outcomes": "Q11 expected business outcomes",
}


class DiscoveryAnswers(BaseModel):
    """
    Structured answers to the 11-question Discovery Questionnaire.
    Every question must be answered — see missing_questions() — before a
    requirement qualifies for design generation.
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

    def missing_questions(self) -> List[str]:
        """Return labels of unanswered questions; empty list means the questionnaire qualifies for design."""
        missing: List[str] = []
        for field, label in DISCOVERY_QUESTION_LABELS.items():
            value = getattr(self, field)
            if field == "learner_count":
                if value is None or value <= 0:
                    missing.append(label)
            elif isinstance(value, list):
                if not value:
                    missing.append(label)
            elif not value or not str(value).strip():
                missing.append(label)
        return missing

    def is_complete(self) -> bool:
        return not self.missing_questions()


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
    # Optional at the wire-format level so a missing/incomplete questionnaire
    # fails with the route's own "not qualified for design" message instead of
    # a generic pydantic validation error — see missing_questions() below.
    discovery: Optional[DiscoveryAnswers] = None
