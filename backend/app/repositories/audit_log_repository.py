import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog, User
from app.repositories.pagination import paginate
from app.schemas.pagination import PageParams


class AuditLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def record(
        self,
        actor: User,
        action: AuditAction,
        entity_type: str,
        entity_id: object,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add an entry to the current transaction. It is saved by the caller's commit,
        together with the change it describes: both are saved, or neither is."""
        self.session.add(
            AuditLog(
                actor_id=actor.id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id),
                details=details or {},
            )
        )

    async def list(
        self,
        params: PageParams,
        action: AuditAction | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog)
        if action is not None:
            query = query.where(AuditLog.action == action)
        if actor_id is not None:
            query = query.where(AuditLog.actor_id == actor_id)
        # Entries written in one transaction share a timestamp; the id keeps them in order
        return await paginate(
            self.session, query, params, AuditLog.created_at.desc(), AuditLog.id.desc()
        )
