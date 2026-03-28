from __future__ import annotations

import json
from typing import Any, Dict

from sqlmodel import Session

from app.models.training import WorkflowEvent


class AuditService:
    def log_event(
        self,
        session: Session,
        event_type: str,
        entity_type: str,
        entity_id: int,
        actor_email: str,
        status: str,
        details: Dict[str, Any],
    ) -> WorkflowEvent:
        event = WorkflowEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_email=actor_email,
            status=status,
            details_json=json.dumps(details, ensure_ascii=True),
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


audit_service = AuditService()
