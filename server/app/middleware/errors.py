"""Обробник помилок: будь-яка помилка повертається у форматі { "message": "..." } (розділ 5.1 ТЗ)."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Саме starlette-версія ловить і наші помилки, і 404 на неіснуючі адреси
from starlette.exceptions import HTTPException

logger = logging.getLogger("finpulse")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        # Наші помилки: raise HTTPException(status_code=409, detail="Предмет уже зібрано")
        return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # FastAPI за замовчуванням повертає 422, а за ТЗ неправильні дані - це 400
        return JSONResponse(status_code=400, content={"message": _validation_message(exc.errors()[0])})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.exception("Неочікувана помилка")
        return JSONResponse(status_code=500, content={"message": "Внутрішня помилка сервера"})


def _validation_message(error: dict) -> str:
    """Перетворює помилку Pydantic на зрозумілий текст українською (його показує фронтенд)."""
    kind = error["type"]
    # loc виглядає як ("body", "email") або ("query", "limit"); перше слово користувачу не потрібне
    field = ".".join(str(p) for p in error["loc"] if p not in ("body", "query", "path"))
    ctx = error.get("ctx", {})

    if kind == "json_invalid":
        return "Неправильний формат JSON"
    if kind == "missing":
        return f"Не заповнено поле {field}"
    if field == "email":
        return "Неправильний email"
    if kind == "string_too_short":
        return f"Поле {field} закоротке: мінімум {ctx.get('min_length')} символів"
    if kind == "string_too_long":
        return f"Поле {field} задовге: максимум {ctx.get('max_length')} символів"
    if kind in ("greater_than_equal", "greater_than"):
        return f"Поле {field} замале: мінімум {ctx.get('ge', ctx.get('gt'))}"
    if kind in ("less_than_equal", "less_than"):
        return f"Поле {field} завелике: максимум {ctx.get('le', ctx.get('lt'))}"
    if kind == "int_parsing":
        return f"Поле {field} має бути цілим числом"
    if kind == "enum":
        return f"Неправильне значення {field}: можливі {ctx.get('expected')}"
    if kind == "value_error":
        # Наші власні перевірки в схемах пишуть текст українською: raise ValueError("...")
        return str(ctx.get("error", "")) or f"Неправильні дані: {field}"
    return f"Неправильні дані: {field}"
