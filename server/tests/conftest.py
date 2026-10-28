"""Налаштування тестів. Виконується pytest-ом раніше за самі тести.

Тести працюють з окремою базою (розділ 8 ТЗ), щоб не зіпсувати вашу робочу:
- локально: файл test.db (SQLite), таблиці створюються з моделей;
- у CI: PostgreSQL з TEST_DATABASE_URL, таблиці вже створили міграції (alembic upgrade head).
"""
import importlib
import os
import pkgutil
from pathlib import Path

import pytest
from sqlalchemy import event

TEST_DB_FILE = Path(__file__).resolve().parent.parent / "test.db"

# Ці змінні треба задати ДО імпорту app.*, бо app.database читає їх під час імпорту
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{TEST_DB_FILE.as_posix()}")
os.environ.setdefault("JWT_SECRET", "test-secret")


def _load_all_models():
    """Імпортує всі файли з app/models, щоб Base знав про всі таблиці."""
    import app.models

    for module in pkgutil.iter_modules(app.models.__path__):
        importlib.import_module(f"app.models.{module.name}")


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """Один раз на всі тести: база з усіма таблицями."""
    from app.database import Base, engine

    _load_all_models()
    if engine.dialect.name == "sqlite":
        # SQLite за замовчуванням ігнорує зовнішні ключі (CASCADE, SET NULL).
        # Вмикаємо, щоб тести поводилися як PostgreSQL.
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        engine.dispose()  # нові з'єднання вже з увімкненими зовнішніми ключами
        # Локально: щоразу чиста база з моделей
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    else:
        # У CI таблиці вже створили міграції; create_all лише додасть відсутні
        Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_state():
    """Перед кожним тестом: порожні таблиці й обнулений лічильник спроб входу."""
    from app.database import Base, SessionLocal
    from app.services import login_limiter

    with SessionLocal() as db:
        # Від залежних таблиць до головних, щоб не порушити зовнішні ключі
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    login_limiter.reset_all()
