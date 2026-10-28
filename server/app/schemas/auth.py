"""Pydantic-схеми: що приймає і що повертає /auth (ТЗ 5.2, 5.3)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _normalize_email(value: str) -> str:
    # ТЗ, таблиця users: email унікальний, в нижньому регістрі
    return value.strip().lower()


def _check_password_bytes(value: str) -> str:
    # bcrypt приймає не більше 72 байтів; кирилиця займає 2 байти на літеру
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Пароль задовгий")
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)  # ТЗ 5.2: password (≥8)

    _email = field_validator("email")(_normalize_email)
    _password = field_validator("password")(_check_password_bytes)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    _email = field_validator("email")(_normalize_email)


class UserOut(BaseModel):
    """Формат user з ТЗ 5.3: id, email, name, points, createdAt."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    points: int
    created_at: datetime = Field(serialization_alias="createdAt")
