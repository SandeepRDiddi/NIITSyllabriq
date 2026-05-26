from __future__ import annotations

import json

from sqlmodel import Session, select

from app.models.design import DesignDocument, ScoreCard
from app.models.requirement import Requirement
from app.models.review import ReviewTask
from app.models.training import TrainingDocument, WorkflowEvent
from app.models.user import User


class ReportingService:
    def summary(self, session: Session) -> dict:
        requirements_count = len(session.exec(select(Requirement)).all())
        designs = session.exec(select(DesignDocument)).all()
        training_documents_count = len(session.exec(select(TrainingDocument)).all())
        reviews = session.exec(select(ReviewTask)).all()
        scorecards = session.exec(select(ScoreCard)).all()
        recent_events = session.exec(select(WorkflowEvent).order_by(WorkflowEvent.created_at.desc())).all()[:20]

        return {
            "requirements_count": requirements_count,
            "designs_count": len(designs),
            "training_documents_count": training_documents_count,
            "primary_pending_count": len([item for item in reviews if item.review_type == "primary" and item.status == "PENDING"]),
            "final_pending_count": len([item for item in reviews if item.review_type == "final" and item.status == "PENDING"]),
            "final_approved_count": len([item for item in designs if item.status == "FINAL_APPROVED"]),
            "average_design_score": round(sum(item.overall_score for item in scorecards) / len(scorecards), 2) if scorecards else 0.0,
            "recent_events": [
                {
                    "id": item.id or 0,
                    "event_type": item.event_type,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "actor_email": item.actor_email,
                    "status": item.status,
                    "details": json.loads(item.details_json),
                    "created_at": item.created_at,
                }
                for item in recent_events
            ],
        }

    def leadership_summary(self, session: Session) -> dict:
        users = session.exec(select(User)).all()
        requirements = session.exec(select(Requirement)).all()
        designs = session.exec(select(DesignDocument)).all()
        reviews = session.exec(select(ReviewTask)).all()
        scorecards = session.exec(select(ScoreCard)).all()
        events = session.exec(select(WorkflowEvent).order_by(WorkflowEvent.created_at.desc())).all()
        generated_events = [item for item in events if item.event_type == "design_generated"]
        export_events = [
            item for item in events
            if item.event_type == "design_exported" and item.status in {"final:docx", "final:pdf"}
        ]
        active_tool_users = {
            item.actor_email
            for item in events
            if item.actor_email and item.actor_email != "system"
        }
        approved_count = len([item for item in designs if item.status == "FINAL_APPROVED"])
        rejected_or_rework_count = len([
            item for item in designs
            if item.status in {"PRIMARY_REJECTED", "FINAL_REWORK_REQUIRED"}
        ])
        generated_count = len(generated_events) or len(designs)
        recent_events = events[:10]

        return {
            "total_users": len(users),
            "active_users_count": len([item for item in users if item.is_active]),
            "active_tool_users_count": len(active_tool_users),
            "requirements_count": len(requirements),
            "designs_generated_count": generated_count,
            "final_approved_count": approved_count,
            "rejected_or_rework_count": rejected_or_rework_count,
            "pending_review_count": len([item for item in reviews if item.status == "PENDING"]),
            "pdf_exports_count": len(export_events),
            "success_rate": round(approved_count / generated_count, 2) if generated_count else 0.0,
            "average_design_score": round(sum(item.overall_score for item in scorecards) / len(scorecards), 2) if scorecards else 0.0,
            "recent_events": [
                {
                    "id": item.id or 0,
                    "event_type": item.event_type,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "actor_email": item.actor_email,
                    "status": item.status,
                    "details": json.loads(item.details_json),
                    "created_at": item.created_at,
                }
                for item in recent_events
            ],
        }
