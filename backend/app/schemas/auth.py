import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    email: str = Field(..., description="Valid institutional or personal email address")
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Analyst handle (alphanumeric and underscores)",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Secure password (minimum 8 characters with mixed case and numbers)",
    )
    full_name: str | None = Field(default=None, max_length=128, description="Analyst full name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        email = v.strip().lower()
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            raise ValueError("Invalid email format. Please provide a valid email address.")
        return email

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        username = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
            raise ValueError(
                "Username must be 3-30 characters long and contain "
                "only letters, numbers, or underscores."
            )
        return username

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() or not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one number or special character.")
        return v


class UserLogin(BaseModel):
    identifier: str = Field(
        ...,
        min_length=3,
        description="Email address or username",
    )
    password: str = Field(..., min_length=1, description="Account password")


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionStatusResponse(BaseModel):
    authenticated: bool
    user: UserResponse | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=128)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)
