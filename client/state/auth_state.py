"""Стан сесії користувача (FE-2).

Сервер (BE-2) після входу ставить httpOnly-cookie `token`. Клієнт зберігає це значення
в `token` і додає його до кожного запиту (див. services/api_client.py), а між запусками
програми — у SharedPreferences (state/session_store.py).
"""
from typing import Optional


class AuthState:
    def __init__(self) -> None:
        self.token: Optional[str] = None
        self.user: Optional[dict] = None

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None

    @property
    def name(self) -> str:
        return (self.user or {}).get("name") or ""

    @property
    def email(self) -> str:
        return (self.user or {}).get("email") or ""

    @property
    def points(self) -> int:
        return int((self.user or {}).get("points") or 0)

    def set_session(self, token: str, user: Optional[dict] = None) -> None:
        self.token = token
        self.user = user

    def set_user(self, user: Optional[dict]) -> None:
        """Оновити дані користувача (після /auth/me, збору предмета, обміну балів тощо)."""
        self.user = user

    def clear(self) -> None:
        self.token = None
        self.user = None


auth_state = AuthState()
