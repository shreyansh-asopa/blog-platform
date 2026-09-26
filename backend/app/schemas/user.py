import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        # Ada@Example.com and ada@example.com are the same inbox
        return value.lower()


class UserRead(BaseModel):
    """What the API returns about a user. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime


class ProfileRead(BaseModel):
    """What anyone can see about an author. No email: that stays private."""

    id: uuid.UUID
    username: str
    created_at: datetime
    post_count: int = Field(description="Published posts only")
