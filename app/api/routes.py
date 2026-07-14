from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import get_session
from app.models.design import DesignDocument, RetrievedReference, ScoreCard
from app.models.requirement import Requirement
from app.models.review import ReviewTask
from app.models.training import TrainingChunk, TrainingDocument, WorkflowEvent
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead
from app.schemas.common import HealthResponse, MessageResponse
from app.schemas.design import DesignRead, DesignSummaryRead, GenerateDesignRequest, ReferenceRead, ScoreCardRead
from app.schemas.llm_config import LLMProviderConfigRead, LLMProviderConfigUpdate
from app.schemas.requirement import (
    DISCOVERY_QUESTION_LABELS,
    DiscoveryAnswers,
    RequirementCreateResponse,
    RequirementRead,
    RequirementTextCreate,
)
from app.schemas.review import ReviewSubmitRequest, ReviewTaskRead
from app.schemas.training import LLMUsageSummaryRead, LeadershipSummaryRead, ReportingSummaryRead, TrainingDocumentRead, WorkflowEventRead
from app.services.audit_service import audit_service
from app.services.auth_service import auth_service, get_current_user, require_roles
from app.services.design_service import DesignService, NotQualifiedForDesignError
from app.services.document_parser import DocumentParser
from app.services.export_service import ExportService
from app.services.llm_config_service import llm_config_service
from app.services.ollama_client import OllamaClient
from app.services.reporting_service import ReportingService
from app.services.storage_service import StorageService
from app.services.training_service import TrainingService


router = APIRouter()

document_parser = DocumentParser()
storage_service = StorageService()
design_service = DesignService()
ollama_client = OllamaClient()
export_service = ExportService()
training_service = TrainingService()
reporting_service = ReportingService()


@router.get("/health", response_model=HealthResponse)
def healthcheck(session: Session = Depends(get_session)) -> HealthResponse:
    active_llm = llm_config_service.get_active_config(session)
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        llm_provider=active_llm.provider,
        generation_model=active_llm.model,
        embedding_model=settings.ollama_embed_model,
        ollama_reachable=ollama_client.is_reachable(),
    )


def _llm_config_response(config) -> LLMProviderConfigRead:
    return LLMProviderConfigRead(
        id=config.id or 0,
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        is_active=config.is_active,
        has_api_key=bool(config.api_key),
        updated_by=config.updated_by,
        updated_at=config.updated_at,
    )


@router.get("/admin/llm-config", response_model=LLMProviderConfigRead)
def get_llm_config(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin"])),
) -> LLMProviderConfigRead:
    return _llm_config_response(llm_config_service.get_active_config(session))


@router.put("/admin/llm-config", response_model=LLMProviderConfigRead)
def update_llm_config(
    payload: LLMProviderConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin"])),
) -> LLMProviderConfigRead:
    provider = payload.provider.strip().lower()
    retained_api_key = payload.api_key
    if provider != "ollama" and not payload.api_key:
        current = llm_config_service.get_active_config(session)
        if current.provider != provider or not current.api_key:
            raise HTTPException(status_code=400, detail=f"{provider} requires an API key")
        retained_api_key = current.api_key
    if provider == "openai_compatible" and not payload.base_url.strip():
        raise HTTPException(status_code=400, detail="OpenAI-compatible providers require a base URL")
    config = llm_config_service.save_active_config(
        session=session,
        provider=provider,
        model=payload.model,
        base_url=payload.base_url,
        api_key=retained_api_key,
        updated_by=current_user.email,
    )
    return _llm_config_response(config)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    token = auth_service.authenticate(session, payload.email, payload.password)
    user = session.exec(select(User).where(User.email == payload.email)).first()
    return TokenResponse(access_token=token, role=user.role if user else "unknown")


@router.get("/auth/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead(
        id=current_user.id or 0,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.get("/users", response_model=List[UserRead])
def list_users(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin"])),
) -> List[UserRead]:
    users = session.exec(select(User).order_by(User.created_at.asc())).all()
    return [
        UserRead(
            id=u.id or 0,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("/users", response_model=UserRead)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin"])),
) -> UserRead:
    try:
        user = auth_service.create_user(session, payload.email, payload.full_name, payload.role, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserRead(
        id=user.id or 0,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/requirements/upload", response_model=RequirementCreateResponse)
async def upload_requirement(
    customer_name: str = Query(...),
    title: str = Query(...),
    discovery: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "designer"])),
) -> RequirementCreateResponse:
    try:
        discovery_answers = DiscoveryAnswers.model_validate_json(discovery)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid Discovery Questionnaire payload") from exc
    missing = discovery_answers.missing_questions()
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"This requirement is not qualified for design — the Discovery Questionnaire is incomplete. Missing: {', '.join(missing)}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    saved_path = storage_service.save_requirement(file.filename, content)
    try:
        raw_text = document_parser.extract_text(saved_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    normalized_requirement = document_parser.normalize_requirement(raw_text)
    normalized_requirement["discovery"] = discovery_answers.model_dump()

    requirement = Requirement(
        customer_name=customer_name,
        title=title,
        source_filename=file.filename,
        source_path=str(saved_path),
        raw_text=raw_text,
        normalized_json=json.dumps(normalized_requirement, indent=2, ensure_ascii=True),
        created_by=current_user.email,
    )
    session.add(requirement)
    session.commit()
    session.refresh(requirement)
    audit_service.log_event(
        session=session,
        event_type="requirement_uploaded",
        entity_type="requirement",
        entity_id=requirement.id or 0,
        actor_email=current_user.email,
        status="RECEIVED",
        details={
            "customer_name": customer_name,
            "title": title,
            "source_filename": file.filename,
        },
    )

    return RequirementCreateResponse(
        id=requirement.id or 0,
        customer_name=requirement.customer_name,
        title=requirement.title,
        created_at=requirement.created_at,
        normalized_requirement=json.loads(requirement.normalized_json),
    )


@router.post("/requirements/text", response_model=RequirementCreateResponse)
def create_requirement_from_text(
    payload: RequirementTextCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "designer"])),
) -> RequirementCreateResponse:
    """
    Create a requirement by typing or pasting text — no file needed.
    Use this when the requirement comes via email, call notes, chat, etc.

    If total_duration_hours is provided, it is prepended to the raw_text
    so the LLM and heuristics can pick it up during design generation.
    """
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Requirement text cannot be empty")

    missing = payload.discovery.missing_questions() if payload.discovery else list(DISCOVERY_QUESTION_LABELS.values())
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"This requirement is not qualified for design — the Discovery Questionnaire is incomplete. Missing: {', '.join(missing)}",
        )

    # Prepend the duration hint so the design generator can reliably extract it
    enriched_text = payload.raw_text.strip()
    if payload.total_duration_hours:
        enriched_text = (
            f"Total Duration: {payload.total_duration_hours} hours\n\n"
            + enriched_text
        )

    # Save as a plain-text file so the storage layer stays consistent
    from datetime import datetime as _dt
    timestamp = _dt.utcnow().strftime("%Y%m%d_%H%M%S")
    source_label = payload.source.replace(" ", "_").lower()
    source_filename = f"{source_label}_{timestamp}.txt"
    saved_path = storage_service.save_requirement(source_filename, enriched_text.encode("utf-8"))

    # Merge structured Discovery Questionnaire answers into the same
    # normalized requirement context the narrative text produces — the
    # designer's free text and the questionnaire are treated as one
    # combined source of truth for prompt construction and traceability.
    normalized_requirement = document_parser.normalize_requirement(enriched_text)
    discovery_answers = payload.discovery.model_dump()
    normalized_requirement["discovery"] = discovery_answers

    requirement = Requirement(
        customer_name=payload.customer_name,
        title=payload.title,
        source_filename=source_filename,
        source_path=str(saved_path),
        raw_text=enriched_text,
        normalized_json=json.dumps(normalized_requirement, indent=2, ensure_ascii=True),
        created_by=current_user.email,
    )
    session.add(requirement)
    session.commit()
    session.refresh(requirement)

    audit_service.log_event(
        session=session,
        event_type="requirement_created",
        entity_type="requirement",
        entity_id=requirement.id or 0,
        actor_email=current_user.email,
        status="RECEIVED",
        details={
            "customer_name": payload.customer_name,
            "title": payload.title,
            "source": payload.source,
            "total_duration_hours": payload.total_duration_hours,
            "char_count": len(enriched_text),
            "discovery_fields_answered": list(discovery_answers.keys()),
        },
    )
    return RequirementCreateResponse(
        id=requirement.id or 0,
        customer_name=requirement.customer_name,
        title=requirement.title,
        created_at=requirement.created_at,
        normalized_requirement=__import__("json").loads(requirement.normalized_json),
    )


@router.get("/requirements", response_model=List[RequirementRead])
def list_requirements(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin", "designer", "primary_reviewer", "final_reviewer"])),
) -> List[RequirementRead]:
    requirements = session.exec(select(Requirement).order_by(Requirement.created_at.desc())).all()
    return [
        RequirementRead(
            id=item.id or 0,
            customer_name=item.customer_name,
            title=item.title,
            source_filename=item.source_filename,
            created_by=item.created_by,
            created_at=item.created_at,
        )
        for item in requirements
    ]


@router.post("/training/upload", response_model=TrainingDocumentRead)
async def upload_training_document(
    title: str = Query(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "designer"])),
) -> TrainingDocumentRead:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded training file is empty")

    saved_path = storage_service.save_requirement(file.filename, content)
    try:
        raw_text = document_parser.extract_text(saved_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    training_document = training_service.create_training_document(
        session=session,
        title=title,
        source_filename=file.filename,
        source_path=str(saved_path),
        content_type=file.content_type or "application/octet-stream",
        raw_text=raw_text,
        uploaded_by=current_user.email,
    )
    audit_service.log_event(
        session=session,
        event_type="training_document_uploaded",
        entity_type="training_document",
        entity_id=training_document.id or 0,
        actor_email=current_user.email,
        status="ACTIVE",
        details={
            "title": title,
            "source_filename": file.filename,
            "content_type": file.content_type or "application/octet-stream",
        },
    )
    return TrainingDocumentRead(
        id=training_document.id or 0,
        title=training_document.title,
        source_filename=training_document.source_filename,
        uploaded_by=training_document.uploaded_by,
        status=training_document.status,
        summary=training_document.summary,
        chunk_count=len(
            session.exec(
                select(TrainingChunk).where(TrainingChunk.training_document_id == training_document.id)
            ).all()
        ),
        created_at=training_document.created_at,
        normalized_document=json.loads(training_document.normalized_json),
    )


@router.get("/training", response_model=List[TrainingDocumentRead])
def list_training_documents(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin", "designer", "primary_reviewer", "final_reviewer"])),
) -> List[TrainingDocumentRead]:
    documents = training_service.list_training_documents(session)
    chunks = session.exec(select(TrainingChunk)).all()
    chunk_counts: dict[int, int] = {}
    for chunk in chunks:
        chunk_counts[chunk.training_document_id] = chunk_counts.get(chunk.training_document_id, 0) + 1
    return [
        TrainingDocumentRead(
            id=item.id or 0,
            title=item.title,
            source_filename=item.source_filename,
            uploaded_by=item.uploaded_by,
            status=item.status,
            summary=item.summary,
            chunk_count=chunk_counts.get(item.id or 0, 0),
            created_at=item.created_at,
            normalized_document=json.loads(item.normalized_json),
        )
        for item in documents
    ]


@router.post("/designs/generate/{requirement_id}", response_model=DesignRead)
def generate_design(
    requirement_id: int,
    payload: GenerateDesignRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "designer"])),
) -> DesignRead:
    try:
        design = design_service.generate_design(
            session,
            requirement_id,
            payload.requested_by or current_user.email,
            primary_reviewers=payload.primary_reviewer_emails or None,
        )
    except NotQualifiedForDesignError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _build_design_response(session, design)


@router.get("/designs", response_model=List[DesignSummaryRead])
def list_designs(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "designer", "primary_reviewer", "final_reviewer"])),
) -> List[DesignSummaryRead]:
    designs = session.exec(select(DesignDocument).order_by(DesignDocument.created_at.desc())).all()
    if current_user.role == "designer":
        designs = [item for item in designs if item.created_by == current_user.email]
    return [
        DesignSummaryRead(
            id=item.id or 0,
            requirement_id=item.requirement_id,
            title=item.title,
            created_by=item.created_by,
            status=item.status,
            similarity_score=item.similarity_score,
            created_at=item.created_at,
        )
        for item in designs
    ]


@router.get("/designs/{design_id}", response_model=DesignRead)
def get_design(
    design_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin", "designer", "primary_reviewer", "final_reviewer"])),
) -> DesignRead:
    design = session.get(DesignDocument, design_id)
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")
    return _build_design_response(session, design)


@router.get("/reviews", response_model=List[ReviewTaskRead])
def list_reviews(
    reviewer_name: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "primary_reviewer", "final_reviewer"])),
) -> List[ReviewTaskRead]:
    statement = select(ReviewTask)
    if reviewer_name:
        statement = statement.where(ReviewTask.reviewer_name == reviewer_name)
    tasks = session.exec(statement.order_by(ReviewTask.created_at.desc())).all()
    if current_user.role != "admin":
        tasks = [item for item in tasks if item.reviewer_name == current_user.email]
    return [
        ReviewTaskRead(
            id=item.id or 0,
            design_document_id=item.design_document_id,
            reviewer_name=item.reviewer_name,
            review_type=item.review_type,
            assigned_by=item.assigned_by,
            status=item.status,
            comments=item.comments,
            reviewed_at=item.reviewed_at,
            created_at=item.created_at,
        )
        for item in tasks
    ]


@router.post("/reviews/{task_id}/submit", response_model=ReviewTaskRead)
def submit_review(
    task_id: int,
    payload: ReviewSubmitRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "primary_reviewer", "final_reviewer"])),
) -> ReviewTaskRead:
    is_admin = current_user.role == "admin"
    reviewer_name = current_user.email
    try:
        task = design_service.submit_review(session, task_id, reviewer_name, payload.decision, payload.comments, is_admin=is_admin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReviewTaskRead(
        id=task.id or 0,
        design_document_id=task.design_document_id,
        reviewer_name=task.reviewer_name,
        review_type=task.review_type,
        assigned_by=task.assigned_by,
        status=task.status,
        comments=task.comments,
        reviewed_at=task.reviewed_at,
        created_at=task.created_at,
    )


@router.get("/designs/{design_id}/export")
def export_design(
    design_id: int,
    version: str = Query(default="draft"),
    file_format: str = Query(default="md"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(["admin", "designer", "primary_reviewer", "final_reviewer"])),
):
    design = session.get(DesignDocument, design_id)
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")
    if version not in {"draft", "final"}:
        raise HTTPException(status_code=400, detail="version must be 'draft' or 'final'")
    if file_format not in {"md", "docx", "pdf"}:
        raise HTTPException(status_code=400, detail="file_format must be one of: md, docx, pdf")
    if version == "final" and design.status != "FINAL_APPROVED":
        raise HTTPException(status_code=409, detail="Final exports are available only after final approval")
    if file_format == "pdf" and design.status != "FINAL_APPROVED":
        raise HTTPException(status_code=409, detail="PDF export is available only after final approval")
    content = design.final_content if version == "final" and design.final_content else design.draft_content
    path = design.final_path if version == "final" else design.draft_path
    stem = storage_service.design_stem(design.title, f"{version}-{file_format}")

    if file_format == "docx":
        path = export_service.export_docx(design.title, content, stem)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_format == "pdf":
        path = export_service.export_pdf(design.title, content, stem)
        media_type = "application/pdf"
    else:
        if not path or not Path(path).exists():
            raise HTTPException(status_code=404, detail="Requested export file is not available")
        media_type = "text/markdown"
    audit_service.log_event(
        session=session,
        event_type="design_exported",
        entity_type="design_document",
        entity_id=design.id or 0,
        actor_email=current_user.email,
        status=f"{version}:{file_format}",
        details={
            "path": path,
            "version": version,
            "file_format": file_format,
        },
    )
    return FileResponse(path=path, filename=Path(path).name, media_type=media_type)


@router.post("/seed/sample", response_model=MessageResponse)
def seed_sample(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin"])),
) -> MessageResponse:
    sample_file = Path(settings.requirement_dir) / "sample_requirement.txt"
    if not sample_file.exists():
        sample_text = (
            "Total Duration: 40 hours\n\n"
            "Customer: Infosys\n\n"
            "We need a Cloud Native Development program for our application developers who are "
            "transitioning from on-premise Java/Spring Boot development to building microservices on AWS. "
            "The team of about 30 developers has strong Java skills but limited cloud exposure.\n\n"
            "Key topics to cover:\n"
            "- AWS core services: EC2, S3, RDS, IAM, VPC\n"
            "- Containerisation with Docker and orchestration with Kubernetes (EKS)\n"
            "- CI/CD pipelines using AWS CodePipeline and GitHub Actions\n"
            "- Twelve-Factor App principles and microservices design patterns\n"
            "- Monitoring and observability with CloudWatch and OpenTelemetry\n\n"
            "The program should be hands-on with real AWS accounts, include a capstone project where "
            "teams migrate a sample monolith to microservices, and conclude with a mini-assessment. "
            "Duration is 40 hours spread over 5 days (instructor-led) or 8 weeks (blended). "
            "Pre-requisites: participants must know Java and basic Linux."
        )
        sample_file.write_text(sample_text, encoding="utf-8")

    existing = session.exec(select(Requirement).where(Requirement.title == "Cloud Native Development on AWS — 40 Hours")).first()
    if existing:
        return MessageResponse(message="Sample data already exists", data={"requirement_id": existing.id})

    raw_text = sample_file.read_text(encoding="utf-8")
    requirement = Requirement(
        customer_name="Infosys",
        title="Cloud Native Development on AWS — 40 Hours",
        source_filename=sample_file.name,
        source_path=str(sample_file),
        raw_text=raw_text,
        normalized_json=document_parser.normalize_to_json(raw_text),
        created_by="system",
    )
    session.add(requirement)
    session.commit()
    session.refresh(requirement)
    return MessageResponse(message="Sample requirement created", data={"requirement_id": requirement.id})


@router.delete("/admin/reset-data", response_model=MessageResponse)
def reset_all_data(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin"])),
) -> MessageResponse:
    """Delete all requirements, designs, reviews and events. Users are preserved. Admin only."""
    from app.models.design import DesignDocument, RetrievedReference, ScoreCard
    from app.models.requirement import Requirement
    from app.models.review import ReviewTask
    from app.models.training import TrainingChunk, TrainingDocument, WorkflowEvent
    for model in [WorkflowEvent, ReviewTask, ScoreCard, RetrievedReference, DesignDocument, Requirement, TrainingChunk, TrainingDocument]:
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()
    return MessageResponse(message="All data cleared. Users preserved.", data={})


@router.get("/reports/summary", response_model=ReportingSummaryRead)
def reporting_summary(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin"])),
) -> ReportingSummaryRead:
    summary = reporting_service.summary(session)
    return ReportingSummaryRead(**summary)


@router.get("/reports/leadership", response_model=LeadershipSummaryRead)
def leadership_summary(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin", "leadership", "svp", "executive"])),
) -> LeadershipSummaryRead:
    summary = reporting_service.leadership_summary(session)
    return LeadershipSummaryRead(**summary)


@router.get("/reports/usage", response_model=LLMUsageSummaryRead)
def llm_usage_summary(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin", "leadership", "svp", "executive"])),
) -> LLMUsageSummaryRead:
    summary = reporting_service.llm_usage_summary(session)
    return LLMUsageSummaryRead(**summary)


@router.get("/reports/events", response_model=List[WorkflowEventRead])
def list_workflow_events(
    entity_type: Optional[str] = Query(default=None),
    actor_email: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(["admin"])),
) -> List[WorkflowEventRead]:
    statement = select(WorkflowEvent).order_by(WorkflowEvent.created_at.desc())
    if entity_type:
        statement = statement.where(WorkflowEvent.entity_type == entity_type)
    if actor_email:
        statement = statement.where(WorkflowEvent.actor_email == actor_email)
    events = session.exec(statement).all()
    return [
        WorkflowEventRead(
            id=item.id or 0,
            event_type=item.event_type,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            actor_email=item.actor_email,
            status=item.status,
            details=json.loads(item.details_json),
            created_at=item.created_at,
        )
        for item in events
    ]


def _build_design_response(session: Session, design: DesignDocument) -> DesignRead:
    refs = session.exec(select(RetrievedReference).where(RetrievedReference.design_document_id == design.id)).all()
    scorecard = session.exec(select(ScoreCard).where(ScoreCard.design_document_id == design.id)).first()

    return DesignRead(
        id=design.id or 0,
        requirement_id=design.requirement_id,
        title=design.title,
        created_by=design.created_by,
        status=design.status,
        reused_content=design.reused_content,
        similarity_score=design.similarity_score,
        draft_content=design.draft_content,
        final_content=design.final_content,
        traceability_map=json.loads(design.traceability_map),
        references=[
            ReferenceRead(
                source_requirement_id=ref.source_requirement_id,
                source_design_id=ref.source_design_id,
                source_training_document_id=ref.source_training_document_id,
                source_type=ref.source_type,
                source_title=ref.source_title,
                similarity_score=ref.similarity_score,
                reused_sections=json.loads(ref.reused_sections),
            )
            for ref in refs
        ],
        scorecard=(
            ScoreCardRead(
                requirement_coverage_score=scorecard.requirement_coverage_score,
                template_completeness_score=scorecard.template_completeness_score,
                technical_consistency_score=scorecard.technical_consistency_score,
                reuse_relevance_score=scorecard.reuse_relevance_score,
                risk_quality_score=scorecard.risk_quality_score,
                review_readiness_score=scorecard.review_readiness_score,
                llm_evaluation_score=scorecard.llm_evaluation_score,
                overall_score=scorecard.overall_score,
                missing_requirements=json.loads(scorecard.missing_requirements),
                contradictions=json.loads(scorecard.contradictions),
                notes=scorecard.notes,
            )
            if scorecard
            else None
        ),
        created_at=design.created_at,
        updated_at=design.updated_at,
    )
