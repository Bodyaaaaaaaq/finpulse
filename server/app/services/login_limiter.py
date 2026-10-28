"""Обмеження спроб входу: 5 невдалих спроб за 15 хвилин (ТЗ 5.2, код 429).

Лічильник зберігається в пам'яті сервера, тож скидається після перезапуску.
Для навчального проєкту з одним процесом сервера цього достатньо.
"""
from datetime import datetime, timedelta, timezone

MAX_ATTEMPTS = 5
WINDOW = timedelta(minutes=15)

_failed: dict[str, list[datetime]] = {}


def _recent(email: str) -> list[datetime]:
    border = datetime.now(timezone.utc) - WINDOW
    attempts = [t for t in _failed.get(email, []) if t > border]
    _failed[email] = attempts
    return attempts


def is_blocked(email: str) -> bool:
    return len(_recent(email)) >= MAX_ATTEMPTS


def minutes_left(email: str) -> int:
    oldest = min(_recent(email))
    seconds = (oldest + WINDOW - datetime.now(timezone.utc)).total_seconds()
    return max(1, int(seconds // 60) + 1)


def register_failure(email: str) -> None:
    _recent(email).append(datetime.now(timezone.utc))


def reset(email: str) -> None:
    _failed.pop(email, None)


def reset_all() -> None:
    """Для тестів."""
    _failed.clear()
