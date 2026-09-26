from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import UserRole
from app.schemas.post import AuthorRead


class RoleUpdate(BaseModel):
    role: UserRole


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # None once the user who acted has been deleted; the entry itself stays
    actor: AuthorRead | None
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any]
    created_at: datetime
