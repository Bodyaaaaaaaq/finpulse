"""Запити входу та реєстрації (FE-3). Сервер видає cookie `token`, яку підхоплює ApiClient."""
from typing import Optional

from services.api_client import ApiClient, ApiError, api as default_api
from services.validation import validate_login, validate_register


def _email(value: str) -> str:
    return value.strip().lower()  # ТЗ: email в нижньому регістрі


async def login(email: str, password: str, client: ApiClient = default_api) -> dict:
    return await client.post("/auth/login", json={"email": _email(email), "password": password})


async def register(name: str, email: str, password: str, address: Optional[str] = None,
                   client: ApiClient = default_api) -> dict:
    payload = {"email": _email(email), "name": name.strip(), "password": password}
    if address:
        payload["address"] = address.strip()  # сервер поки ігнорує (потрібна колонка users.address)
    return await client.post("/auth/register", json=payload)


async def submit_login(ctx, email: str, password: str, client: ApiClient = default_api) -> Optional[str]:
    """Валідація -> запит -> перехід на головну. Повертає текст помилки (для показу над кнопкою) або None."""
    error = validate_login(email, password)
    if error:
        return error
    try:
        user = await login(email, password, client)
    except ApiError as e:
        return e.message
    await ctx.login(user)
    return None


async def submit_register(ctx, name: str, email: str, password: str, confirm: str,
                          address: Optional[str] = None, client: ApiClient = default_api) -> Optional[str]:
    error = validate_register(name, email, password, confirm, address)
    if error:
        return error
    try:
        user = await register(name, email, password, address, client)
    except ApiError as e:
        return e.message
    await ctx.login(user)  # сервер вже поставив cookie — користувач одразу залогінений
    return None
