"""Паролі та JWT-токени (ТЗ 5.1, BE-2).

Паролі: бібліотека bcrypt напряму. passlib[bcrypt] з ТЗ не використовуємо:
passlib не оновлюється з 2020 року і падає з поточною версією bcrypt 5.x.
Хеш при цьому той самий - bcrypt, як вимагає таблиця users у ТЗ.
"""
import os
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("У файлі server/.env не задано JWT_SECRET")

JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(days=7)  # ТЗ 5.1: JWT на 7 днів


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id: uuid.UUID) -> str:
    expires = datetime.now(UTC) + TOKEN_LIFETIME
    return jwt.encode({"sub": str(user_id), "exp": expires}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def read_token(token: str) -> uuid.UUID | None:
    """Повертає id користувача з токена або None, якщо токен підроблений чи прострочений."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
