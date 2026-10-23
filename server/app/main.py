"""Точка входу сервера FinPulse.

Запуск з Visual Studio: run.py -> Set as Startup Item -> F5
Запуск з терміналу (з папки server): uvicorn app.main:app --reload
Swagger-документація: http://127.0.0.1:8000/api/docs
"""
from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.middleware.errors import register_error_handlers

app = FastAPI(
    title="FinPulse API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
register_error_handlers(app)

# Усі адреси починаються з /api (розділ 5.1 ТЗ)
api = APIRouter(prefix="/api")


@api.get("/health", tags=["service"])
def health(db: Session = Depends(get_db)):
    """Перевірка, що сервер працює і бачить базу даних."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


# Тут підключатимуться роутери: auth (BE-2), profile (BE-3), currency... (BE-4)
# from app.routers import auth
# api.include_router(auth.router)

app.include_router(api)
