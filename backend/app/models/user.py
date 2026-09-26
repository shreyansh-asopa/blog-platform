import enum
import uuid

from sqlalchemy import Enum, Index, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UserRole(enum.StrEnum):
    USER = "user"
    ADMIN = "admin"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # Stored as typed, so "Ada_Writes" keeps its capitals; unique ignoring case (index below)
    username: Mapped[str] = mapped_column(String(50))
    # Argon2 hash, never the plain password
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())


# "Ada" and "ada" can't both exist, so nobody can pass as someone else by changing case
Index("uq_users_username_lower", func.lower(User.username), unique=True)
