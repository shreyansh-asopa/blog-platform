import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models import AuditAction, AuditLog, User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.pagination import PageParams


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.audit = AuditLogRepository(session)

    async def change_role(self, admin: User, user_id: uuid.UUID, role: UserRole) -> User:
        # Also guarantees at least one admin is always left: the one making changes
        if user_id == admin.id:
            raise PermissionDeniedError("You can't change your own role")
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if user.role is role:
            return user  # nothing changed, nothing to record

        self.audit.record(
            admin,
            AuditAction.ROLE_CHANGED,
            "user",
            user.id,
            {"username": user.username, "from": user.role, "to": role},
        )
        user.role = role
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_audit_logs(
        self, params: PageParams, action: AuditAction | None, actor_id: uuid.UUID | None
    ) -> tuple[list[AuditLog], int]:
        return await self.audit.list(params, action, actor_id)
