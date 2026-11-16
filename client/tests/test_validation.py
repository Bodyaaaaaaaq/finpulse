import pytest

from services.validation import (validate_address, validate_email, validate_login, validate_name,
                                 validate_new_password, validate_register)


@pytest.mark.parametrize("value", ["a@b.ua", "name@example.com", " user.name+tag@mail.example.org "])
def test_valid_emails(value):
    assert validate_email(value) is None


@pytest.mark.parametrize("value,expected", [
    ("", "Введіть email"), ("   ", "Введіть email"), (None, "Введіть email"),
    ("plain", "Некоректний email"), ("a@b", "Некоректний email"), ("a b@c.com", "Некоректний email"),
    ("@c.com", "Некоректний email"), ("a@@c.com", "Некоректний email"),
])
def test_invalid_emails(value, expected):
    assert validate_email(value) == expected


def test_name_rules():
    assert validate_name("Іван") is None
    assert validate_name("  ") == "Введіть імʼя"
    assert "довге" in validate_name("a" * 101)


def test_address_rules():
    assert validate_address("Львів, Стрийська 1") is None
    assert validate_address(" ") == "Введіть адресу"


def test_password_rules():
    assert validate_new_password("12345678") is None
    assert validate_new_password("") == "Введіть пароль"
    assert "8" in validate_new_password("1234567")
    assert validate_new_password("п" * 37) == "Пароль занадто довгий"   # 37 літер кирилиці = 74 байти
    assert validate_new_password("п" * 36) is None                      # рівно 72 байти


def test_login_only_requires_filled_fields():
    assert validate_login("a@b.ua", "x") is None
    assert validate_login("bad", "x") == "Некоректний email"
    assert validate_login("a@b.ua", "") == "Введіть пароль"


def test_register_reports_first_error_in_field_order():
    assert validate_register("", "bad", "1", "2", "") == "Введіть імʼя"
    assert validate_register("Іван", "bad", "1", "2", "") == "Некоректний email"
    assert validate_register("Іван", "a@b.ua", "1", "2", "") == "Введіть адресу"
    assert "8" in validate_register("Іван", "a@b.ua", "1", "2", "Львів")
    assert validate_register("Іван", "a@b.ua", "12345678", "87654321", "Львів") == "Паролі не збігаються"
    assert validate_register("Іван", "a@b.ua", "12345678", "12345678", "Львів") is None


def test_register_without_address_field():
    assert validate_register("Іван", "a@b.ua", "12345678", "12345678", None) is None


def test_validate_password_change():
    from services.validation import validate_password_change as v
    assert v("", "newpass12") == "Введіть поточний пароль"
    assert v("old", "") == "Введіть пароль"
    assert v("old", "short").startswith("Пароль має містити")
    assert v("samepass1", "samepass1") == "Новий пароль має відрізнятися від поточного"
    assert v("oldpass1", "newpass12") is None


def test_validate_delete_password():
    from services.validation import validate_delete_password as v
    assert v("") == "Введіть пароль для підтвердження"
    assert v("x") is None
