import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, Pagination, require_permission
from app.models import AuditAction, User
from app.permissions import Permission
from app.schemas.admin import AuditLogRead, RoleUpdate
from app.schemas.pagination import Page
from app.schemas.user import UserRead
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])

UserManager = Annotated[User, Depends(require_permission(Permission.MANAGE_USERS))]
AuditViewer = Annotated[User, Depends(require_permission(Permission.VIEW_AUDIT_LOG))]


@router.patch("/users/{user_id}/role")
async def change_role(
    user_id: uuid.UUID, data: RoleUpdate, db: DbSession, admin: UserManager
) -> UserRead:
    """Make a user an admin, or back. You can't change your own role."""
    return UserRead.model_validate(await AdminService(db).change_role(admin, user_id, data.role))


@router.get("/audit-logs")
async def list_audit_logs(
    db: DbSession,
    _: AuditViewer,
    params: Pagination,
    action: AuditAction | None = None,
    actor_id: uuid.UUID | None = None,
) -> Page[AuditLogRead]:
    """Newest first. Filter by ?action=post.deleted or ?actor_id=<user id>."""
    logs, total = await AdminService(db).list_audit_logs(params, action, actor_id)
    return Page(
        items=[AuditLogRead.model_validate(entry) for entry in logs],
        total=total,
        page=params.page,
        size=params.size,
    )
