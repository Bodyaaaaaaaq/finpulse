"""Що показувати на головній (кнопка «Редагувати», FE-5). Зберігається між запусками в SharedPreferences."""
import json
from typing import Optional

HOME_KEY = "finpulse.home"
# Як у макеті «Головна»: USD, EUR, BTC, ETH, Gold
DEFAULT_SELECTED = ["currency:USD", "currency:EUR", "crypto:BTC", "crypto:ETH", "metal:gold"]


class HomeStore:
    """prefs — ft.SharedPreferences (або будь-який об'єкт з async get/set)."""

    def __init__(self, prefs) -> None:
        self._prefs = prefs

    async def load(self) -> Optional[list[str]]:
        try:
            raw = await self._prefs.get(HOME_KEY)
            data = json.loads(raw) if isinstance(raw, str) else None
        except Exception:  # сховище недоступне або значення зіпсоване — беремо типовий набір
            return None
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return data
        return None

    async def save(self, keys: list[str]) -> None:
        try:
            await self._prefs.set(HOME_KEY, json.dumps(keys))
        except Exception:
            pass


class HomeState:
    def __init__(self) -> None:
        self.selected: list[str] = list(DEFAULT_SELECTED)
        self.store: Optional[HomeStore] = None

    async def load(self, store: HomeStore) -> None:
        self.store = store
        saved = await store.load()
        if saved is not None:
            self.selected = saved

    def is_selected(self, key: str) -> bool:
        return key in self.selected

    def toggle(self, key: str) -> bool:
        """Додає або прибирає ключ; повертає новий стан (True — тепер показується)."""
        if key in self.selected:
            self.selected.remove(key)
            return False
        self.selected.append(key)
        return True

    async def save(self) -> None:
        if self.store is not None:
            await self.store.save(self.selected)

    def reset(self) -> None:
        self.selected = list(DEFAULT_SELECTED)
        self.store = None


home_state = HomeState()
