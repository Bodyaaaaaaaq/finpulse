"""Pydantic-схеми для /profile (ТЗ 5.2, задача BE-3).

Назви полів у JSON - як у ТЗ: oldPassword, newPassword.
"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.auth import _check_password_bytes, _normalize_email


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("Ім'я не може бути порожнім")
    return value


class ProfileUpdate(BaseModel):
    """PATCH /profile: можна передати name, email або обидва."""

    name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None

    _name = field_validator("name")(_clean_name)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str | None) -> str | None:
        return _normalize_email(value) if value is not None else None

    @model_validator(mode="after")
    def _something_to_change(self):
        if self.name is None and self.email is None:
            raise ValueError("Немає даних для зміни: передайте name або email")
        return self


class PasswordChange(BaseModel):
    """PATCH /profile/password."""

    model_config = ConfigDict(populate_by_name=True)

    old_password: str = Field(alias="oldPassword")
    new_password: str = Field(alias="newPassword", min_length=8)

    _new_password = field_validator("new_password")(_check_password_bytes)


class AccountDelete(BaseModel):
    """DELETE /profile: пароль для підтвердження (ТЗ 7.9)."""

    password: str
