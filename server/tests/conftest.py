"""Налаштування тестів. Виконується pytest-ом раніше за самі тести.

Тести працюють з окремою базою (розділ 8 ТЗ), щоб не зіпсувати вашу робочу.
За замовчуванням це файл test.db (SQLite). У CI можна задати TEST_DATABASE_URL з PostgreSQL.
"""
import os
from pathlib import Path

TEST_DB_FILE = Path(__file__).resolve().parent.parent / "test.db"

os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{TEST_DB_FILE.as_posix()}")
os.environ["JWT_SECRET"] = "test-secret"

import pytest  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import login_limiter  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Один раз на всі тести: чиста база з усіма таблицями."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_state():
    """Перед кожним тестом: жодних користувачів і обнулений лічильник спроб входу."""
    with SessionLocal() as db:
        db.execute(delete(User))
        db.commit()
    login_limiter.reset_all()
