"""Role-based permissions: what each role may do beyond its own content.

Ownership ("you may edit your own post") is checked in the services. This map only
lists the extra powers a role has over other people's content.
"""

import enum

from app.models import User, UserRole


class Permission(enum.StrEnum):
    MANAGE_ANY_POST = "manage_any_post"
    DELETE_ANY_COMMENT = "delete_any_comment"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOG = "view_audit_log"


ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.USER: frozenset(),
    UserRole.ADMIN: frozenset(Permission),
}


def has_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[user.role]
