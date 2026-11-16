"""Клієнтська валідація форм входу та реєстрації (FE-3). Повертає текст помилки або None."""
import re
from typing import Optional

# Той самий принцип, що в браузерах: щось@щось.домен, без пробілів.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
MIN_PASSWORD = 8        # ТЗ 5.2: password (≥8)
MAX_PASSWORD_BYTES = 72  # обмеження bcrypt на сервері; кирилиця = 2 байти на літеру


def validate_email(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return "Введіть email"
    if not _EMAIL_RE.match(value):
        return "Некоректний email"
    return None


def validate_name(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return "Введіть імʼя"
    if len(value) > 100:
        return "Імʼя занадто довге (до 100 символів)"
    return None


def validate_address(value: str) -> Optional[str]:
    if not (value or "").strip():
        return "Введіть адресу"
    return None


def validate_new_password(value: str) -> Optional[str]:
    if not value:
        return "Введіть пароль"
    if len(value) < MIN_PASSWORD:
        return f"Пароль має містити щонайменше {MIN_PASSWORD} символів"
    if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        return "Пароль занадто довгий"
    return None


def validate_login(email: str, password: str) -> Optional[str]:
    """Для входу достатньо, щоб поля були заповнені: правила пароля перевіряє сервер."""
    return validate_email(email) or ("Введіть пароль" if not password else None)


def validate_register(name: str, email: str, password: str, confirm: str,
                      address: Optional[str] = None) -> Optional[str]:
    """Перша знайдена помилка в порядку полів форми. address=None — поле вимкнене (REGISTER_ADDRESS=false)."""
    error = validate_name(name) or validate_email(email)
    if error is None and address is not None:
        error = validate_address(address)
    error = error or validate_new_password(password)
    if error is None and password != confirm:
        error = "Паролі не збігаються"
    return error


def validate_password_change(old: str, new: str) -> Optional[str]:
    """Форма «Змінити пароль» (FE-4): поточний пароль заповнений, новий відповідає правилам і відрізняється."""
    if not old:
        return "Введіть поточний пароль"
    error = validate_new_password(new)
    if error is None and new == old:
        return "Новий пароль має відрізнятися від поточного"
    return error


def validate_delete_password(password: str) -> Optional[str]:
    if not password:
        return "Введіть пароль для підтвердження"
    return None
