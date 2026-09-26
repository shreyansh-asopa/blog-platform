# Import every model here so Alembic autogenerate can see all tables
from app.models.user import User, UserRole

__all__ = ["User", "UserRole"]
