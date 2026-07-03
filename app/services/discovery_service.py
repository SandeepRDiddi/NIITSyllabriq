from __future__ import annotations

# ---------------------------------------------------------------------------
# Translates structured Discovery Questionnaire answers (see
# app.schemas.requirement.DiscoveryAnswers) into:
#   1. A labeled-facts block injected into the LLM user prompt.
#   2. A question -> design-section traceability mapping.
# Kept isolated from design_service.py so _render_draft()/_build_traceability()
# stay focused on rendering rather than questionnaire-specific formatting.
# ---------------------------------------------------------------------------

FIELD_LABELS: dict[str, str] = {
    "domain_focus": "Domain Focus",
    "target_audience_roles": "Target Audience",
    "experience_level": "Experience Level",
    "learner_count": "Expected Learner Count",
    "trigger": "Requirement Trigger",
    "delivery_model": "Delivery Model",
    "timeline": "Expected Timeline",
    "constraints": "Known Constraints",
    "strategic_objective": "Linked Strategic Objective",
    "prior_vendor_experience": "Prior Vendor/Training Partner Experience",
    "expected_business_outcomes": "Expected Business Outcomes",
}

# Each field maps to the design section(s) it most directly influences.
FIELD_TO_DESIGN_SECTIONS: dict[str, list[str]] = {
    "domain_focus": ["program_introduction", "indicative_design"],
    "target_audience_roles": ["prerequisites", "key_outcomes"],
    "experience_level": ["prerequisites", "detailed_design"],
    "learner_count": ["indicative_design"],
    "trigger": ["program_introduction"],
    "delivery_model": ["indicative_design"],
    "timeline": ["program_introduction"],
    "constraints": ["prerequisites", "detailed_design"],
    "strategic_objective": ["program_introduction", "key_outcomes"],
    "prior_vendor_experience": ["key_outcomes"],
    "expected_business_outcomes": ["key_outcomes"],
}


def _format_value(value: object) -> str | None:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(items) if items else None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def build_discovery_facts_block(discovery: dict[str, object] | None) -> str:
    """
    Render answered Discovery Questionnaire fields as a labeled-facts block,
    e.g. "Target Audience: QA Engineers, 1-3 years experience". Skips any
    field that wasn't answered. Returns "" if no fields were answered.
    """
    if not discovery:
        return ""

    lines: list[str] = []
    for field, label in FIELD_LABELS.items():
        formatted = _format_value(discovery.get(field))
        if formatted:
            lines.append(f"- {label}: {formatted}")

    if not lines:
        return ""

    return (
        "=== STRUCTURED DISCOVERY FACTS (authoritative — ground every design decision in these) ===\n"
        + "\n".join(lines)
        + "\n=== END STRUCTURED DISCOVERY FACTS ==="
    )


def build_intro_clause(discovery: dict[str, object] | None) -> str:
    """
    One sentence summarizing domain focus / trigger / strategic objective, for
    the deterministic fallback's program_introduction — used when the LLM is
    unreachable, so discovery answers still influence the generated document.
    """
    if not discovery:
        return ""
    clauses: list[str] = []
    domain_focus = _format_value(discovery.get("domain_focus"))
    trigger = _format_value(discovery.get("trigger"))
    strategic_objective = _format_value(discovery.get("strategic_objective"))
    if domain_focus:
        clauses.append(f"with a particular focus on {domain_focus}")
    if trigger:
        clauses.append(f"initiated in response to {trigger.lower()}")
    if strategic_objective:
        clauses.append(f"aligned with the organization's {strategic_objective} objectives")
    if not clauses:
        return ""
    return "This engagement is " + "; ".join(clauses) + "."


def build_delivery_clause(discovery: dict[str, object] | None) -> str:
    """One sentence noting delivery model / learner count, for the indicative_design framing paragraph."""
    if not discovery:
        return ""
    clauses: list[str] = []
    delivery_model = _format_value(discovery.get("delivery_model"))
    learner_count = _format_value(discovery.get("learner_count"))
    if delivery_model:
        clauses.append(f"This program will be delivered via {delivery_model}.")
    if learner_count:
        clauses.append(f"It is designed for a cohort of approximately {learner_count} learners.")
    return " ".join(clauses)


def build_prerequisite_items(discovery: dict[str, object] | None) -> list[str]:
    """Prerequisite bullets derived from target audience / experience level."""
    if not discovery:
        return []
    items: list[str] = []
    audience = _format_value(discovery.get("target_audience_roles"))
    experience = _format_value(discovery.get("experience_level"))
    if audience:
        items.append(f"Participants are expected to be {audience} or in an equivalent role.")
    if experience:
        items.append(f"Prior experience level: {experience}.")
    return items


def build_outcome_items(discovery: dict[str, object] | None) -> list[str]:
    """Key-outcome bullets derived from expected business outcomes."""
    if not discovery:
        return []
    outcomes = discovery.get("expected_business_outcomes")
    if not isinstance(outcomes, list):
        return []
    verbs = ["Achieve", "Demonstrate", "Drive", "Support", "Deliver"]
    return [
        f"{verbs[i % len(verbs)]} measurable progress toward: {str(item).strip()}"
        for i, item in enumerate(outcomes)
        if str(item).strip()
    ]


def build_discovery_traceability(discovery: dict[str, object] | None) -> list[dict[str, object]]:
    """
    Build a question -> design-section traceability entry for every
    answered Discovery Questionnaire field.
    """
    if not discovery:
        return []

    entries: list[dict[str, object]] = []
    for field, label in FIELD_LABELS.items():
        formatted = _format_value(discovery.get(field))
        if not formatted:
            continue
        entries.append(
            {
                "field": field,
                "question": label,
                "answer": formatted,
                "influenced_sections": FIELD_TO_DESIGN_SECTIONS.get(field, []),
            }
        )
    return entries
