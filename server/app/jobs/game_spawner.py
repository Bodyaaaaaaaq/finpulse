"""Крон генерації нових предметів гри (GD-3).

Раз на годину створює N предметів зі статусом ACTIVE у випадкових точках
у межах заданої зони (bounding box). Адмін може додати предмет вручну: create_item().
Запуск вручну (з папки server): python -m app.jobs.game_spawner
"""
import logging
import os
import random
from decimal import Decimal

from app.database import SessionLocal
from app.models.game_item import GameItem, GameItemStatus

logger = logging.getLogger(__name__)

# Зона за замовчуванням: центр Львова. Змінюється через .env.
MIN_LAT = float(os.getenv("SPAWN_MIN_LAT", "49.8200"))
MAX_LAT = float(os.getenv("SPAWN_MAX_LAT", "49.8600"))
MIN_LNG = float(os.getenv("SPAWN_MIN_LNG", "23.9700"))
MAX_LNG = float(os.getenv("SPAWN_MAX_LNG", "24.0700"))
ITEMS_PER_RUN = int(os.getenv("SPAWN_ITEMS_PER_RUN", "10"))
MIN_POINTS = int(os.getenv("SPAWN_MIN_POINTS", "5"))
MAX_POINTS = int(os.getenv("SPAWN_MAX_POINTS", "20"))


def _coord(value: float) -> Decimal:
    """Numeric(9, 6) у БД: рівно 6 знаків після коми."""
    return Decimal(f"{value:.6f}")


def create_item(latitude: float, longitude: float, points: int, db=None) -> GameItem:
    """Створює один ACTIVE-предмет. Використовується кроном і адмінкою (GD-6)."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Некоректні координати")
    if points < 0:
        raise ValueError("points не може бути від'ємним")

    own_session = db is None
    session = db or SessionLocal()
    try:
        item = GameItem(
            latitude=_coord(latitude),
            longitude=_coord(longitude),
            points=points,
            status=GameItemStatus.ACTIVE,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    finally:
        if own_session:
            session.close()


def spawn_items(count: int = ITEMS_PER_RUN) -> int:
    """Створює count предметів у випадкових точках зони. Повертає кількість."""
    db = SessionLocal()
    try:
        items = [
            GameItem(
                latitude=_coord(random.uniform(MIN_LAT, MAX_LAT)),
                longitude=_coord(random.uniform(MIN_LNG, MAX_LNG)),
                points=random.randint(MIN_POINTS, MAX_POINTS),
                status=GameItemStatus.ACTIVE,
            )
            for _ in range(count)
        ]
        db.add_all(items)
        db.commit()
        return len(items)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def spawn_job() -> None:
    """Точка входу для планувальника: ловить помилки, щоб крон не падав."""
    try:
        logger.info("game items spawned: %s", spawn_items())
    except Exception:
        logger.exception("game items spawn failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    spawn_job()
