"""Перевірка входу для приватних адрес (ТЗ 5.1: без входу - 401).

Використання в роутері:

    @router.get("/something")
    def something(user: User = Depends(get_current_user)):
        ...
"""
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.user import User
from app.services.security import read_token

TOKEN_COOKIE = "token"  # ТЗ 5.1: httpOnly cookie token


def get_current_user(
    token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    user_id = read_token(token) if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Потрібно увійти в акаунт")
    return user
