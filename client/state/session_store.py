"""Збереження токена між запусками програми (Flet SharedPreferences)."""
from typing import Optional

TOKEN_KEY = "finpulse.token"


class SessionStore:
    """Тонка обгортка: prefs — це ft.SharedPreferences (або будь-який об'єкт з async get/set/remove)."""

    def __init__(self, prefs) -> None:
        self._prefs = prefs

    async def load_token(self) -> Optional[str]:
        try:
            value = await self._prefs.get(TOKEN_KEY)
        except Exception:  # сховище недоступне — працюємо без збереження
            return None
        return value if isinstance(value, str) and value else None

    async def save_token(self, token: str) -> None:
        try:
            await self._prefs.set(TOKEN_KEY, token)
        except Exception:
            pass

    async def clear(self) -> None:
        try:
            await self._prefs.remove(TOKEN_KEY)
        except Exception:
            pass
