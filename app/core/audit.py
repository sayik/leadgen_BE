from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.models import AuditLog, User


def record_audit(
    db: AsyncSession,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: UUID,
    details: dict | None = None,
) -> None:
    db.add(AuditLog(
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    ))
