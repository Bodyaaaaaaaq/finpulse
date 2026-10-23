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
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        return JSONResponse(status_code=400, content={"message": f"Неправильні дані: {field}"})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.exception("Неочікувана помилка")
        return JSONResponse(status_code=500, content={"message": "Внутрішня помилка сервера"})
