"""Перевірка входу для приватних адрес (ТЗ 5.1: без входу - 401).

Використання в роутері:

    @router.get("/something")
    def something(user: CurrentUser):
        ...
"""
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException

from app.dependencies import DbSession
from app.models.user import User
from app.services.security import read_token

TOKEN_COOKIE = "token"  # ТЗ 5.1: httpOnly cookie token


def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Cookie()] = None,
) -> User:
    user_id = read_token(token) if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Потрібно увійти в акаунт")
    return user


# Скорочення: параметр типу CurrentUser - це залогінений користувач, інакше 401
CurrentUser = Annotated[User, Depends(get_current_user)]
