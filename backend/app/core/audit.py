from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


def record_audit(
    db: Session,
    *,
    tenant_id: str,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    summary: str,
) -> None:
    """Adds an audit log row to the session without committing — callers
    record audit entries as part of the same transaction as the change
    itself, so the two can never disagree about whether the change happened."""
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
        )
    )
