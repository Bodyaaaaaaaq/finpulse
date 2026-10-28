"""Залежності FastAPI, спільні для всіх ендпоінтів.

get_db дає сесію бази даних у кожен запит і гарантовано закриває її після.
Використання в роутері:

    @router.get("/something")
    def something(db: DbSession):
        ...
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Скорочення: параметр типу DbSession автоматично отримує сесію БД
DbSession = Annotated[Session, Depends(get_db)]
