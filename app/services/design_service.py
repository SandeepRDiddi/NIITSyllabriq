from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from jinja2 import Template
from sqlmodel import Session, select

from app.core.config import settings
from app.models.design import DesignDocument, RetrievedReference, ScoreCard
from app.models.requirement import Requirement
from app.models.review import ReviewTask
from app.services.audit_service import audit_service
from app.services.groq_client import GroqClient
from app.services.ollama_client import OllamaClient
from app.services.scoring_service import ScoringService
from app.services.similarity_service import SimilarityService
from app.services.storage_service import StorageService
from app.services.text_utils import as_pretty_json, dedupe_keep_order

# ---------------------------------------------------------------------------
# System prompt injected into every Ollama call — encodes the full StackRoute
# template rules so the local LLM never needs external API access.
# ---------------------------------------------------------------------------
_STACKROUTE_SYSTEM_PROMPT = """
You are the NIIT StackRoute Design Document Generator.
Your sole job is to produce program design documents for corporate training programs.
You MUST return ONLY valid JSON — no markdown fences, no extra text, no commentary.

Return a JSON object with EXACTLY these keys:

{
  "program_name": "<full program/course name>",
  "total_duration_hours": <integer>,
  "program_introduction": "<2-3 rich paragraphs about the program, separated by \\n\\n>",
  "indicative_design": "<paragraph + 3-column module summary table — see format below>",
  "prerequisites": "<bullet list, each line starting with '- '>",
  "key_outcomes": "<bullet list starting with action verbs, each line starting with '- '>",
  "detailed_design": "<ONE single 5-column markdown table — see format and example below>",
  "case_study": "<case study description if applicable, else empty string>",
  "capstone": "<capstone description if applicable, else empty string>"
}

====== INDICATIVE_DESIGN FORMAT ======
One short paragraph followed by a 3-column table: # | Module | Duration (Hours)
All durations must sum to total_duration_hours.

====== DETAILED_DESIGN FORMAT AND EXAMPLE ======
This is ONE single markdown table. Every module is ONE ROW. No headings. No sub-tables.

Columns: Module Name | Sub-topics / Detailed Technical Coverage | Duration (Hours) | Hands-on | Tools Needed

QUALITY STANDARD FOR Sub-topics column:
Write 4-6 sentences covering the specific topics, domain concepts, frameworks, and techniques taught.
Name the actual subject matter — do not write generic phrases like "introduction to the topic".
Use semicolons to separate topic groups within the cell.

Study this example carefully — your output must match this level of detail:

| Module Name | Sub-topics / Detailed Technical Coverage | Duration (Hours) | Hands-on | Tools Needed |
|---|---|---|---|---|
| 1. AI Foundations and Business Context | Enterprise AI landscape overview; difference between automation, analytics, generative AI, and agentic AI; core AI terminology including LLMs, RAG, embeddings, agents, and orchestration; where AI creates measurable value across business functions including operations, finance, HR, and customer engagement; human-in-the-loop operating models and governance framing. | 3 | Participants map their own business functions and identify where generative AI versus rule-based automation is the appropriate approach, and why. | Slides, workshop canvas, use-case classification cards |
| 2. Generative AI Use Cases and Design Patterns | Use cases across knowledge retrieval, document intelligence, meeting summarisation, contract analysis, report generation, customer query handling, and HR assistance; copilots versus workflow agents; retrieval-augmented generation architecture; prompt engineering fundamentals; context windows and hallucination risk; designing prompts that produce consistent, auditable outputs. | 4 | Teams prioritise a set of enterprise use cases using a structured value, feasibility, data-readiness, and risk scoring matrix, then sketch a prompt and retrieval design for their top-ranked use case. | Use-case canvas, prioritisation matrix, sample enterprise documents |
| 3. Agentic AI: Concepts, Architecture, and Design | What makes a system agentic versus generative; agent roles, tasks, memory types, tools, and orchestration patterns; deterministic steps versus AI-driven reasoning; planner, analyst, reviewer, and approver agent patterns; event-driven workflows; human approval checkpoints; exception-based operations; reliability and fallback design for enterprise deployment. | 3 | Participants decompose a business scenario into agent roles, tool calls, decision checkpoints, and human handoffs using a structured agent design canvas. | Agent design template, workflow cards, orchestration whiteboard |

(generate ALL modules in this same table, continuing rows until duration sums to total_duration_hours)

====== RULES ======
1. detailed_design is ONE table only — no headings, no sub-tables, no text outside the table.
2. Sum of Duration column in detailed_design MUST equal total_duration_hours exactly.
3. Sum of Duration column in indicative_design table MUST also equal total_duration_hours.
4. Sub-topics must name real concepts, tools, frameworks — never generic filler phrases.
5. Hands-on must describe the specific activity the participant actually does, not just "a lab".
6. Key Outcomes bullets MUST start with action verbs: Design, Build, Implement, Analyze, Apply,
   Create, Evaluate, Demonstrate, Configure, Deploy, Architect, Develop, Assess, etc.
7. program_introduction: factual, professional, third-person — no marketing slogans.
8. Do NOT include Learning Pedagogy or About StackRoute — they are added separately.
9. Return ONLY valid JSON. No ```json fences. No extra text before or after the JSON object.
""".strip()


class DesignService:
    def __init__(self) -> None:
        self.llm = self._build_llm_client()
        self.similarity_service = SimilarityService()
        self.scoring_service = ScoringService()
        self.storage_service = StorageService()
        self.template_path = Path(settings.template_dir) / "niit_template.md"

    def _build_llm_client(self) -> OllamaClient | GroqClient:
        provider = settings.llm_provider.strip().lower()
        if provider == "ollama":
            return OllamaClient()
        if provider == "groq":
            groq = GroqClient()
            if not groq.is_reachable():
                raise ValueError("LLM_PROVIDER=groq requires GROQ_API_KEY to be set")
            return groq
        raise ValueError("LLM_PROVIDER must be either 'ollama' or 'groq'")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_design(self, session: Session, requirement_id: int, requested_by: str, primary_reviewers: list[str] | None = None) -> DesignDocument:
        requirement = session.get(Requirement, requirement_id)
        if not requirement:
            raise ValueError("Requirement not found")

        normalized_requirement = json.loads(requirement.normalized_json)
        matches = [
            match
            for match in self.similarity_service.find_matches(session, requirement.raw_text)
            if match.requirement_id != requirement.id
        ]
        best_match = matches[0] if matches else None
        reused_content = bool(best_match and best_match.similarity_score >= settings.similarity_threshold)

        draft = self._render_draft(requirement.title, requirement.raw_text, normalized_requirement, best_match)
        traceability_map = self._build_traceability(normalized_requirement, draft)
        draft_path = self.storage_service.save_design(requirement.title, draft, status="draft")

        design = DesignDocument(
            requirement_id=requirement.id or 0,
            title=requirement.title,
            created_by=requested_by,
            status="UNDER_PRIMARY_REVIEW",
            reused_content=reused_content,
            similarity_score=best_match.similarity_score if best_match else 0.0,
            draft_content=draft,
            draft_path=str(draft_path),
            traceability_map=as_pretty_json(traceability_map),
            updated_at=datetime.utcnow(),
        )
        session.add(design)
        session.commit()
        session.refresh(design)
        audit_service.log_event(
            session=session,
            event_type="design_generated",
            entity_type="design_document",
            entity_id=design.id or 0,
            actor_email=requested_by,
            status=design.status,
            details={
                "requirement_id": requirement.id,
                "reused_content": reused_content,
                "similarity_score": design.similarity_score,
                "best_match_title": best_match.title if best_match else None,
                "best_match_source_type": best_match.source_type if best_match else None,
            },
        )

        if best_match:
            reference = RetrievedReference(
                design_document_id=design.id or 0,
                source_requirement_id=best_match.requirement_id,
                source_design_id=best_match.design_id,
                source_training_document_id=best_match.training_document_id,
                source_type=best_match.source_type,
                source_title=best_match.title,
                similarity_score=best_match.similarity_score,
                reused_sections=as_pretty_json(best_match.reused_sections),
            )
            session.add(reference)

        score = self.scoring_service.score(normalized_requirement, draft, reused_content)
        session.add(
            ScoreCard(
                design_document_id=design.id or 0,
                requirement_coverage_score=score["requirement_coverage_score"],
                template_completeness_score=score["template_completeness_score"],
                technical_consistency_score=score["technical_consistency_score"],
                reuse_relevance_score=score["reuse_relevance_score"],
                risk_quality_score=score["risk_quality_score"],
                review_readiness_score=score["review_readiness_score"],
                llm_evaluation_score=score["llm_evaluation_score"],
                overall_score=score["overall_score"],
                missing_requirements=as_pretty_json(score["missing_requirements"]),
                contradictions=as_pretty_json(score["contradictions"]),
                notes=score["notes"],
            )
        )

        reviewer_list = primary_reviewers if primary_reviewers else settings.primary_reviewer_list
        for reviewer in reviewer_list:
            session.add(
                ReviewTask(
                    design_document_id=design.id or 0,
                    reviewer_name=reviewer,
                    review_type="primary",
                    assigned_by=requested_by,
                    status="PENDING",
                )
            )

        session.commit()
        return design

    def submit_review(self, session: Session, task_id: int, reviewer_name: str, decision: str, comments: str, is_admin: bool = False) -> ReviewTask:
        task = session.get(ReviewTask, task_id)
        if not task:
            raise ValueError("Review task not found")
        if not is_admin and task.reviewer_name != reviewer_name:
            raise ValueError("Reviewer does not match assigned task")
        if task.status == "APPROVED":
            return task

        task.status = "APPROVED" if decision.lower() == "approve" else "REJECTED"
        task.comments = comments
        task.reviewed_at = datetime.utcnow()
        session.add(task)

        design = session.get(DesignDocument, task.design_document_id)
        if not design:
            raise ValueError("Design not found")

        if task.review_type == "primary":
            if task.status == "REJECTED":
                design.status = "PRIMARY_REJECTED"
            else:
                design.status = "UNDER_FINAL_REVIEW"
                existing_final = session.exec(
                    select(ReviewTask).where(
                        ReviewTask.design_document_id == design.id,
                        ReviewTask.review_type == "final",
                    )
                ).all()
                if not existing_final:
                    for reviewer in settings.final_reviewer_list:
                        session.add(
                            ReviewTask(
                                design_document_id=design.id or 0,
                                reviewer_name=reviewer,
                                review_type="final",
                                assigned_by=reviewer_name,
                                status="PENDING",
                            )
                        )
        else:
            final_tasks = session.exec(
                select(ReviewTask).where(
                    ReviewTask.design_document_id == design.id,
                    ReviewTask.review_type == "final",
                )
            ).all()
            if any(item.status == "REJECTED" for item in final_tasks):
                design.status = "FINAL_REWORK_REQUIRED"
            elif final_tasks and all(item.status == "APPROVED" for item in final_tasks):
                design.status = "FINAL_APPROVED"
                design.final_content = design.draft_content
                final_path = self.storage_service.save_design(design.title, design.final_content, status="final")
                design.final_path = str(final_path)

        design.updated_at = datetime.utcnow()
        session.add(design)
        session.commit()
        session.refresh(task)
        audit_service.log_event(
            session=session,
            event_type="review_submitted",
            entity_type="review_task",
            entity_id=task.id or 0,
            actor_email=reviewer_name,
            status=task.status,
            details={
                "design_document_id": task.design_document_id,
                "review_type": task.review_type,
                "comments": comments,
                "design_status_after_review": design.status,
            },
        )
        return task

    # ------------------------------------------------------------------
    # Private: draft rendering
    # ------------------------------------------------------------------

    def _render_draft(
        self,
        title: str,
        raw_text: str,
        normalized_requirement: dict[str, object],
        best_match,
    ) -> str:
        """
        Render the Jinja2 NIIT StackRoute template.

        Strategy:
          1. Build a deterministic fallback context from normalized_requirement.
          2. Ask the local Ollama LLM (no external API) to produce richer content.
          3. Merge the LLM output over the fallback — any LLM key overwrites the fallback.
          4. Render the Jinja2 template.
        """
        template = Template(self.template_path.read_text(encoding="utf-8"))
        context = self._build_fallback_context(title, normalized_requirement, best_match)

        # Generate via Groq (if GROQ_API_KEY is set) or local Ollama
        llm_result = self.llm.generate(
            prompt=self._build_llm_user_prompt(title, raw_text, best_match),
            system_prompt=_STACKROUTE_SYSTEM_PROMPT,
        )
        if llm_result:
            parsed = self._parse_llm_json(llm_result)
            if parsed:
                # Only accept string or numeric values; skip anything unexpected
                for key, value in parsed.items():
                    if key in context and (isinstance(value, str) or isinstance(value, (int, float))):
                        context[key] = str(value) if isinstance(value, (int, float)) else value

        # Normalise table fields — LLMs (especially Groq) sometimes add leading spaces
        # before pipe characters or omit the leading pipe on rows entirely.
        context["detailed_design"] = self._normalise_md_table(context.get("detailed_design", ""))
        context["indicative_design"] = self._normalise_md_table(context.get("indicative_design", ""))

        return template.render(**context)

    def _build_llm_user_prompt(self, title: str, raw_text: str, best_match) -> str:
        """
        User-turn prompt sent to the local Ollama model.
        Provides all available context so the model can generate rich content
        without any external API call.
        """
        reused_note = ""
        if best_match:
            reused_note = (
                f"\n\nA similar prior design exists (similarity score: {best_match.similarity_score:.2f}): "
                f'"{best_match.title}". Relevant reused sections: {json.dumps(best_match.reused_sections, ensure_ascii=True)}. '
                "You may reuse and adapt content where appropriate."
            )

        return (
            f"Generate a complete NIIT StackRoute program design document for the requirement below.\n\n"
            f"Program Title: {title}\n\n"
            f"Requirement Text (read carefully — use ALL details to populate the design):\n"
            f"{raw_text[:8000]}\n"
            f"{reused_note}\n\n"
            "Your detailed_design field must be ONE markdown table where every module is a row.\n"
            "The Sub-topics column must contain 4-6 sentences naming the SPECIFIC topics, concepts,\n"
            "and techniques taught — use the domain language from the requirement text above.\n"
            "The Hands-on column must describe the exact activity the participant performs.\n"
            "All Duration values must sum exactly to total_duration_hours.\n\n"
            "Return ONLY valid JSON. No ```json fences. No text outside the JSON object."
        )

    def _parse_llm_json(self, llm_result: str) -> dict | None:
        """
        Parse JSON from LLM output — handles cases where the model adds
        markdown fences or surrounding text despite instructions.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", llm_result).strip().rstrip("`").strip()
        # Find the outermost JSON object
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        try:
            return json.loads(cleaned[start:end])
        except Exception:
            return None

    def _normalise_md_table(self, text: str) -> str:
        """
        Fix common LLM table formatting issues so the DOCX renderer always sees
        clean markdown tables:

        1. Leading whitespace before | — Groq often outputs " | col |" instead of "| col |"
        2. Missing leading | — some models output "col1 | col2" without the opening pipe
        3. Missing trailing | — trim then add it
        4. Missing separator row — insert one after the header if absent
        """
        if not text or "|" not in text:
            return text

        lines = text.splitlines()
        cleaned: list[str] = []
        header_index: int | None = None

        for raw_line in lines:
            line = raw_line.strip()

            # Skip empty lines (preserve them outside table blocks)
            if not line:
                cleaned.append("")
                continue

            # Detect table rows: contains | (either proper "|col|" or improper "col | col")
            if "|" in line:
                # Ensure starts and ends with |
                if not line.startswith("|"):
                    line = "| " + line
                if not line.endswith("|"):
                    line = line + " |"
                cleaned.append(line)

                # Track where header is (first table row)
                if header_index is None and not re.match(r"^\|[-| :]+\|$", line):
                    header_index = len(cleaned) - 1
            else:
                # Non-table line (paragraph text in indicative_design, etc.)
                cleaned.append(line)
                header_index = None  # reset — new table block may follow

        # If we found a header row but no separator immediately follows it, insert one
        if header_index is not None:
            sep_index = header_index + 1
            if sep_index >= len(cleaned) or not re.match(r"^\|[-| :]+\|$", cleaned[sep_index].strip()):
                # Count columns from header
                header = cleaned[header_index]
                n_cols = len(header.strip("|").split("|"))
                separator = "|" + "|".join(["---"] * n_cols) + "|"
                cleaned.insert(sep_index, separator)

        return "\n".join(cleaned)

    def _build_fallback_context(
        self,
        title: str,
        normalized_requirement: dict[str, object],
        best_match,
    ) -> dict[str, str]:
        """
        Deterministic heuristic context used when Ollama is unreachable
        or when the LLM output is unparseable.
        All keys must match the Jinja2 template variables exactly.
        """
        # Extract fields from normalized requirement (IT-requirement schema)
        business_goal = str(normalized_requirement.get("business_goal", ""))
        functional = [str(item) for item in normalized_requirement.get("functional_requirements", [])]
        scope_items = [str(item) for item in normalized_requirement.get("scope", [])]
        constraints = [str(item) for item in normalized_requirement.get("constraints", [])]
        source_summary = normalized_requirement.get("source_summary", [])

        # Derive program name — strip common suffixes / clean up title
        program_name = title.replace(" - Solution Design", "").replace(" Design", "").strip()

        # Try to extract total hours from the requirement text
        total_duration_hours = self._extract_duration(
            business_goal + " ".join(str(s) for s in source_summary)
        )

        # Program introduction: 2 paragraphs built from the business goal
        intro_p1 = (
            f"This program — {program_name} — is designed to equip participants with the practical skills "
            f"and theoretical knowledge required to address the following learning objective: {business_goal or '[TBD]'}. "
            "The curriculum is structured to deliver progressive skill development across all covered topics."
        )
        intro_p2 = (
            "Participants will engage with hands-on labs, guided exercises, and real-world scenarios throughout "
            "the program. Upon completion, learners will have a solid foundation to apply their skills in "
            "professional contexts and continue to advanced practice areas."
        )

        # Build topic list: prefer scope items, fall back to functional requirements
        topics = scope_items or functional[:8] or ["Core Concepts", "Hands-on Practice", "Assessment"]

        # Indicative design: paragraph + summary module table
        indicative = self._build_indicative_table(program_name, topics, total_duration_hours)

        # Prerequisites: from constraints or generic based on topics
        prereq_items = constraints or [
            "Basic understanding of the subject domain covered in this program",
            "Familiarity with a command-line interface (Linux/macOS/Windows terminal)",
            "Laptop with internet access and at least 8 GB RAM",
        ]
        prerequisites = "\n".join(f"- {item}" for item in prereq_items)

        # Key outcomes: transform functional requirements into learning outcome statements
        outcomes = self._to_learning_outcomes(functional) or [
            "Apply core concepts from the program in practical, real-world scenarios",
            "Demonstrate proficiency with the tools and technologies covered",
            "Design and implement solutions to domain-specific problems",
            "Evaluate architectural trade-offs and select appropriate approaches",
        ]
        key_outcomes = "\n".join(f"- {item}" for item in outcomes)

        # Detailed design: rich per-module breakdown
        detailed_design = self._build_fallback_detailed(topics, total_duration_hours)

        return {
            "program_name": program_name,
            "total_duration_hours": str(total_duration_hours),
            "program_introduction": f"{intro_p1}\n\n{intro_p2}",
            "indicative_design": indicative,
            "prerequisites": prerequisites,
            "key_outcomes": key_outcomes,
            "detailed_design": detailed_design,
            "case_study": "",
            "capstone": "",
        }

    def _extract_duration(self, text: str) -> int:
        """Extract total hours from text if mentioned, else return 40 as default."""
        match = re.search(r"(\d+)\s*(?:hours?|hrs?)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 40

    def _to_learning_outcomes(self, functional_requirements: list[str]) -> list[str]:
        """
        Convert functional requirement strings into learning outcome statements
        by prefixing with action verbs.
        """
        action_verbs = ["Apply", "Implement", "Design", "Build", "Configure", "Analyze", "Deploy", "Evaluate"]
        outcomes = []
        for i, req in enumerate(functional_requirements[:8]):
            verb = action_verbs[i % len(action_verbs)]
            # Clean up the requirement text a bit
            clean = req.strip().rstrip(".")
            if clean and not any(clean.lower().startswith(v.lower()) for v in action_verbs):
                outcomes.append(f"{verb} {clean[0].lower()}{clean[1:]}")
            else:
                outcomes.append(clean)
        return outcomes

    def _build_indicative_table(self, program_name: str, topics: list[str], total_hours: int) -> str:
        """
        Build the Indicative Design and Content Coverage section:
        a brief paragraph followed by a module-level summary table.
        """
        if not topics:
            topics = ["Core Module"]
        n = len(topics)
        hours_each = max(2, total_hours // n)

        lines: list[str] = [
            f"This program — {program_name} — is structured across {n} modules, "
            f"progressively building from foundational concepts through advanced hands-on practice.",
            "",
            "| # | Module | Duration (Hours) |",
            "|---|---|---|",
        ]
        for i, topic in enumerate(topics):
            h = total_hours - hours_each * (n - 1) if i == n - 1 else hours_each
            lines.append(f"| {i + 1} | {topic} | {h} |")
        return "\n".join(lines)

    def _build_fallback_detailed(self, topics: list[str], total_hours: int) -> str:
        """
        Generate the Detailed Design as a single flat markdown table matching the
        NIIT StackRoute template format:
        Module Name | Sub-topics / Detailed Technical Coverage | Duration (Hours) | Hands-on | Tools Needed
        Every module is one row. Hours across all rows sum to total_hours.
        """
        if not topics:
            topics = ["Core Module"]
        n = len(topics)
        hours_each = max(2, total_hours // n)

        rows = [
            "| Module Name | Sub-topics / Detailed Technical Coverage | Duration (Hours) | Hands-on | Tools Needed |",
            "|---|---|---|---|---|",
        ]
        for i, topic in enumerate(topics):
            mod_num = i + 1
            mod_hours = total_hours - hours_each * (n - 1) if i == n - 1 else hours_each
            rows.append(
                f"| {mod_num}. {topic} "
                f"| [Detailed sub-topics for {topic} — to be filled by the design team] "
                f"| {mod_hours} "
                f"| [Hands-on lab exercise for {topic} — TBD] "
                f"| [Tools required — TBD] |"
            )
        return "\n".join(rows)

    # ------------------------------------------------------------------
    # Private: traceability
    # ------------------------------------------------------------------

    def _build_traceability(self, normalized_requirement: dict[str, object], draft_content: str) -> dict[str, object]:
        requirements = dedupe_keep_order(
            [str(item) for item in normalized_requirement.get("functional_requirements", [])]
        )
        traceability = []
        lower_draft = draft_content.lower()
        for requirement in requirements:
            traceability.append(
                {
                    "requirement": requirement,
                    "covered": requirement.lower() in lower_draft,
                    "evidence_hint": (
                        "Direct textual match" if requirement.lower() in lower_draft else "Needs reviewer confirmation"
                    ),
                }
            )
        return {"requirements": traceability}
