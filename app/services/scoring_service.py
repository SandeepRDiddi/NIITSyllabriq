from __future__ import annotations

import json

from app.services.ollama_client import OllamaClient
from app.services.text_utils import cosine_similarity, dedupe_keep_order, split_sentences


class ScoringService:
    """
    Scores a generated NIIT StackRoute program design document across
    7 quality dimensions.  All computation runs locally — Ollama is used
    for the LLM evaluation dimension only, with a heuristic fallback.
    """

    # Mandatory sections that must appear in every StackRoute design document.
    # Checked via case-insensitive substring match against "## <section>" lines.
    REQUIRED_SECTIONS = [
        "Program Introduction",
        "Indicative Design and Content Coverage",
        "Pre-requisites",
        "Key Outcomes",
        "Detailed Design:",
        "Learning Pedagogy",
        "About StackRoute",
    ]

    # Action verbs expected at the start of Key Outcome bullets
    OUTCOME_VERBS = {
        "apply", "implement", "design", "build", "configure", "analyze",
        "deploy", "evaluate", "create", "demonstrate", "develop", "architect",
        "optimize", "debug", "integrate", "assess", "construct", "produce",
    }

    def __init__(self) -> None:
        self.ollama = OllamaClient()

    def score(
        self,
        normalized_requirement: dict[str, object],
        design_content: str,
        reused_content: bool,
    ) -> dict[str, object]:
        # 1. Requirement coverage — how many functional items appear in the draft
        functional_reqs = [str(item) for item in normalized_requirement.get("functional_requirements", [])]
        covered = [req for req in functional_reqs if req.lower() in design_content.lower()]
        missing = [req for req in functional_reqs if req not in covered]
        requirement_coverage = 100.0 if not functional_reqs else round((len(covered) / len(functional_reqs)) * 100, 2)

        # 2. Template completeness — all 7 StackRoute sections present
        lower_content = design_content.lower()
        section_hits = [
            section for section in self.REQUIRED_SECTIONS
            if f"## {section}".lower() in lower_content or f"## {section.lower()}" in lower_content
        ]
        template_completeness = round((len(section_hits) / len(self.REQUIRED_SECTIONS)) * 100, 2)

        # 3. Technical / content consistency
        consistency = self._consistency_score(normalized_requirement, design_content)

        # 4. Reuse relevance
        reuse_relevance = 90.0 if reused_content else 70.0

        # 5. Design quality — key outcomes with action verbs + detailed design table
        design_quality = self._design_quality_score(design_content)

        # 6. Review readiness — sufficient length, no placeholder overload
        review_readiness = self._review_readiness_score(design_content, missing)

        # 7. LLM evaluation (Ollama — local only, heuristic fallback)
        llm_score = self._llm_evaluate(normalized_requirement, design_content)

        overall = round(
            0.4 * ((requirement_coverage + template_completeness + consistency) / 3.0)
            + 0.2 * reuse_relevance
            + 0.15 * design_quality
            + 0.1 * review_readiness
            + 0.15 * llm_score,
            2,
        )

        contradictions = self._contradictions(normalized_requirement, design_content)
        notes = (
            "LLM-assisted scoring used (Ollama local model)."
            if llm_score != 70.0
            else "Heuristic scoring only — Ollama unavailable or response was unparseable."
        )

        return {
            "requirement_coverage_score": requirement_coverage,
            "template_completeness_score": template_completeness,
            "technical_consistency_score": consistency,
            "reuse_relevance_score": reuse_relevance,
            "risk_quality_score": design_quality,      # field name kept for DB compat
            "review_readiness_score": review_readiness,
            "llm_evaluation_score": llm_score,
            "overall_score": overall,
            "missing_requirements": missing,
            "contradictions": contradictions,
            "notes": notes,
        }

    # ------------------------------------------------------------------
    # Dimension scorers
    # ------------------------------------------------------------------

    def _consistency_score(self, normalized_requirement: dict[str, object], design_content: str) -> float:
        """Check that topics mentioned in the requirement appear in the design."""
        items = (
            [str(item) for item in normalized_requirement.get("functional_requirements", [])]
            + [str(item) for item in normalized_requirement.get("constraints", [])]
        )
        if not items:
            return 85.0
        matched = sum(
            1 for item in items
            if cosine_similarity(item, design_content) > 0.15 or item.lower() in design_content.lower()
        )
        return round((matched / len(items)) * 100, 2)

    def _design_quality_score(self, design_content: str) -> float:
        """
        Score quality of the StackRoute-specific sections:
          - Key Outcomes bullets should start with action verbs
          - Detailed Design should contain a table
          - Pre-requisites should be present and non-trivial
        """
        score = 55.0

        # Check for a Detailed Design table (markdown table indicator)
        if "| Module" in design_content or "| module" in design_content.lower():
            score += 10.0
        elif "Detailed Design:" in design_content:
            score += 5.0

        # Check Key Outcomes exist and use action verbs
        if "Key Outcomes" in design_content:
            score += 5.0
            # Extract bullet lines after "Key Outcomes"
            ko_match = design_content.lower().find("## key outcomes")
            if ko_match != -1:
                ko_block = design_content[ko_match:ko_match + 1000]
                bullets = [
                    line.lstrip("- ").strip().lower()
                    for line in ko_block.splitlines()
                    if line.strip().startswith("- ")
                ]
                verb_hits = sum(
                    1 for b in bullets
                    if any(b.startswith(v) for v in self.OUTCOME_VERBS)
                )
                if bullets:
                    verb_ratio = verb_hits / len(bullets)
                    score += round(verb_ratio * 15.0, 2)

        # Pre-requisites present
        if "Pre-requisites" in design_content or "## pre-requisites" in design_content.lower():
            score += 5.0

        # "After completing this program" intro line present
        if "after completing this program" in design_content.lower():
            score += 5.0

        # Fixed boilerplate sections present
        if "Learning Pedagogy" in design_content:
            score += 2.5
        if "About StackRoute" in design_content:
            score += 2.5

        return min(round(score, 2), 100.0)

    def _review_readiness_score(self, design_content: str, missing: list[str]) -> float:
        sentences = split_sentences(design_content)
        if not sentences:
            return 0.0
        # Count [TBD] placeholders — too many means not ready
        tbd_count = design_content.count("[TBD]")
        base = 90.0 if len(sentences) >= 15 else 70.0
        penalty = min(len(missing) * 3.0 + tbd_count * 5.0, 40.0)
        return max(round(base - penalty, 2), 0.0)

    def _contradictions(self, normalized_requirement: dict[str, object], design_content: str) -> list[str]:
        contradictions: list[str] = []
        text = design_content.lower()
        if "manual" in text and "fully automated" in text:
            contradictions.append("Document mentions both manual handling and full automation.")
        for constraint in normalized_requirement.get("constraints", []):
            constraint_str = str(constraint)
            if "must" in constraint_str.lower() and cosine_similarity(constraint_str, design_content) < 0.1:
                contradictions.append(f"Constraint may be insufficiently addressed: {constraint_str}")
        return dedupe_keep_order(contradictions)

    def _llm_evaluate(self, normalized_requirement: dict[str, object], design_content: str) -> float:
        """
        Ask the local Ollama model to evaluate the design quality.
        Returns a score 0-100.  Falls back to 70.0 on any error.
        """
        prompt = (
            "You are evaluating a NIIT StackRoute program design document.\n"
            "Return ONLY a JSON object with a single key 'score' (0-100 integer).\n"
            "Score based on: completeness of sections, quality of Key Outcomes (action verbs), "
            "presence of a Detailed Design table, clarity of Pre-requisites, "
            "and overall professional quality.\n\n"
            f"Requirement context (JSON):\n{json.dumps(normalized_requirement, ensure_ascii=True)[:2000]}\n\n"
            f"Design document (first 3000 chars):\n{design_content[:3000]}\n\n"
            "Return only: {{\"score\": <number>}}"
        )
        result = self.ollama.generate(prompt)
        if not result:
            return 70.0
        try:
            # Find JSON object in response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start == -1:
                return 70.0
            parsed = json.loads(result[start:end])
            s = float(parsed["score"])
            return max(min(s, 100.0), 0.0)
        except Exception:
            return 70.0
