"""Стан сесії користувача. У FE-1 — мінімальна версія в памʼяті;
повноцінне збереження токена і завантаження профілю робиться в FE-2."""
from typing import Optional


class AuthState:
    def __init__(self) -> None:
        self.token: Optional[str] = None
        self.user: Optional[dict] = None

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None

    def set_session(self, token: str, user: Optional[dict] = None) -> None:
        self.token = token
        self.user = user

    def clear(self) -> None:
        self.token = None
        self.user = None


auth_state = AuthState()
