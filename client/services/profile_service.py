"""Запити профілю: зміна пароля й видалення акаунта (FE-4, сервер — BE-3)."""
from typing import Optional

from services.api_client import ApiClient, ApiError, api as default_api
from services.validation import validate_delete_password, validate_password_change


async def change_password(old_password: str, new_password: str, client: ApiClient = default_api) -> dict:
    # Назви полів у JSON — як у ТЗ: oldPassword, newPassword
    return await client.patch("/profile/password",
                              json={"oldPassword": old_password, "newPassword": new_password})


async def delete_account(password: str, client: ApiClient = default_api) -> dict:
    # DELETE із тілом: client.delete() у обгортці без json, тому викликаємо request()
    return await client.request("DELETE", "/profile", json={"password": password})


async def submit_change_password(old_password: str, new_password: str,
                                 client: ApiClient = default_api) -> Optional[str]:
    """Валідація -> запит. Повертає текст помилки або None, якщо пароль змінено."""
    error = validate_password_change(old_password, new_password)
    if error:
        return error
    try:
        await change_password(old_password, new_password, client)
    except ApiError as e:
        return e.message
    return None


async def submit_delete_account(ctx, password: str, client: ApiClient = default_api) -> Optional[str]:
    """Після успіху сервер уже прибрав cookie: чистимо сесію й ведемо на /login."""
    error = validate_delete_password(password)
    if error:
        return error
    try:
        await delete_account(password, client)
    except ApiError as e:
        return e.message
    await ctx.session_expired()  # очищає збережений токен і стан, відкриває /login
    return None
