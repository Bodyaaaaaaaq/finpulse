import pytest

from app.database import Base, SessionLocal, engine
from app.jobs import game_spawner
from app.models.game_item import GameItem, GameItemStatus


@pytest.fixture(autouse=True)
def _tables():
    """Створює таблиці, якщо їх ще немає (SQLite test.db). У CI вони вже є з міграцій."""
    Base.metadata.create_all(engine)


def _count() -> int:
    db = SessionLocal()
    try:
        return db.query(GameItem).count()
    finally:
        db.close()


def test_spawn_items_creates_active_items_in_bounds():
    before = _count()

    created = game_spawner.spawn_items(3)

    assert created == 3
    assert _count() == before + 3

    db = SessionLocal()
    try:
        for item in db.query(GameItem).all():
            assert item.status == GameItemStatus.ACTIVE
            assert game_spawner.MIN_LAT <= float(item.latitude) <= game_spawner.MAX_LAT
            assert game_spawner.MIN_LNG <= float(item.longitude) <= game_spawner.MAX_LNG
            assert item.points >= 0
    finally:
        db.close()


def test_create_item_manually():
    item = game_spawner.create_item(49.84, 24.03, 15)

    assert item.status == GameItemStatus.ACTIVE
    assert item.points == 15


def test_create_item_rejects_bad_coordinates():
    with pytest.raises(ValueError):
        game_spawner.create_item(120.0, 24.03, 15)
