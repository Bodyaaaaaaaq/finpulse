"""Налаштування тестів. Виконується pytest-ом раніше за самі тести.

Тести працюють з окремою базою (розділ 8 ТЗ), щоб не зіпсувати вашу робочу.
За замовчуванням це файл test.db (SQLite). У CI можна задати TEST_DATABASE_URL з PostgreSQL.
"""
import os

os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")
