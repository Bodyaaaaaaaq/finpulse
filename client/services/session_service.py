"""Керування сесією: відновлення при запуску, оновлення профілю, вихід (FE-2)."""
from services.api_client import ApiClient, ApiError, api as default_api
from state.auth_state import auth_state
from state.session_store import SessionStore


async def restore_session(store: SessionStore, client: ApiClient = default_api) -> bool:
    """Підставляє збережений токен і перевіряє його запитом GET /auth/me.

    Повертає True, якщо користувач залогінений. Недійсний токен видаляється.
    """
    token = await store.load_token()
    if not token:
        return False
    auth_state.set_session(token)
    try:
        user = await client.get("/auth/me")
    except ApiError as e:
        auth_state.clear()
        if e.status == 401:  # токен прострочений або недійсний
            await store.clear()
        return False
    auth_state.set_user(user)
    return True


async def refresh_user(client: ApiClient = default_api) -> None:
    """Оновити auth_state.user (наприклад, баланс балів) із сервера. Помилки мережі ігноруються."""
    if not auth_state.is_authenticated:
        return
    try:
        auth_state.set_user(await client.get("/auth/me"))
    except ApiError:
        pass


async def sign_out(store: SessionStore, client: ApiClient = default_api) -> None:
    """Вихід: POST /auth/logout (помилка не заважає), очищення стану й збереженого токена."""
    try:
        await client.post("/auth/logout")
    except ApiError:
        pass
    auth_state.clear()
    await store.clear()
