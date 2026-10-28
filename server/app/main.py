"""Точка входу сервера FinPulse.

Запуск з Visual Studio: run.py -> Set as Startup Item -> F5
Запуск з терміналу (з папки server): uvicorn app.main:app --reload
Swagger-документація: http://127.0.0.1:8000/api/docs
"""
from fastapi import APIRouter, FastAPI
from sqlalchemy import text

from app.dependencies import DbSession
from app.middleware.errors import register_error_handlers
from app.routers import auth

app = FastAPI(
    title="FinPulse API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
register_error_handlers(app)

# Усі адреси починаються з /api (розділ 5.1 ТЗ)
api = APIRouter(prefix="/api")


@api.get("/health", tags=["service"])
def health(db: DbSession):
    """Перевірка, що сервер працює і бачить базу даних."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


# Роутери. Далі тут з'являться profile (BE-3), currency... (BE-4)
api.include_router(auth.router)

app.include_router(api)
