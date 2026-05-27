from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    from app.models.design import DesignDocument, RetrievedReference, ScoreCard
    from app.models.llm_config import LLMProviderConfig
    from app.models.requirement import Requirement
    from app.models.review import ReviewTask
    from app.models.training import LLMUsageEvent, TrainingChunk, TrainingDocument, WorkflowEvent
    from app.models.user import User
    from app.services.auth_service import auth_service

    Path(settings.export_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.requirement_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.template_dir).mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        auth_service.ensure_seed_users(session)


def get_session():
    with Session(engine) as session:
        yield session
