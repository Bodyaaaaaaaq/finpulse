import logging
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import bcrypt
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.crypto_rate import CryptoRate
from app.models.currency_rate import CurrencyRate
from app.models.game_item import GameItem, GameItemStatus
from app.models.metal_rate import MetalRate, MetalType
from app.models.news import News, NewsCategory
from app.models.reward import Reward
from app.models.user import User
from app.services.coingecko import update_crypto_rates
from app.services.metals import update_metal_rates
from app.services.nbu import update_currency_rates
from app.services.news import update_news

logger = logging.getLogger(__name__)

DEMO_EMAIL = "demo@finquest.com"
DEMO_PASSWORD = "demo12345"

# Центр зони гри (Київ, як у прикладі з ТЗ); змініть за потреби
CENTER_LAT = 50.4501
CENTER_LNG = 30.5234


def is_empty(db, model) -> bool:
    return db.scalar(select(func.count()).select_from(model)) == 0


def seed_user(db) -> User:
    user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
        user = User(email=DEMO_EMAIL, name="Demo", password_hash=password_hash, points=150)
        db.add(user)
        db.commit()
        logger.info("Demo user created")
    return user


def run_integration(name, func_, db) -> None:
    try:
        logger.info("%s: %s records", name, func_(db))
    except Exception:
        db.rollback()
        logger.exception("%s integration failed, will use fallback data", name)


def seed_fallback_rates(db) -> None:
    now = datetime.now(timezone.utc)
    if is_empty(db, CurrencyRate):
        for code, name, rate in (
            ("USD", "Долар США", "41.50"),
            ("EUR", "Євро", "45.00"),
            ("PLN", "Злотий", "10.50"),
        ):
            db.add(CurrencyRate(code=code, name=name, rate=Decimal(rate), updated_at=now))
    if is_empty(db, CryptoRate):
        for coin_id, symbol, name, rank, price, change in (
            ("bitcoin", "BTC", "Bitcoin", 1, "64000", "1.8"),
            ("ethereum", "ETH", "Ethereum", 2, "3200", "-0.7"),
            ("tether", "USDT", "Tether", 3, "1.0", "0.0"),
        ):
            db.add(
                CryptoRate(
                    coin_id=coin_id, symbol=symbol, name=name, rank=rank,
                    price_usd=Decimal(price), change_24h=Decimal(change), updated_at=now,
                )
            )
    if is_empty(db, MetalRate):
        for metal, price in (
            (MetalType.GOLD, "128.50"),
            (MetalType.SILVER, "1.55"),
            (MetalType.PLATINUM, "31.20"),
            (MetalType.PALLADIUM, "30.10"),
        ):
            db.add(MetalRate(metal=metal, price_per_gram_usd=Decimal(price), updated_at=now))
    db.commit()


def seed_news_fallback(db) -> None:
    if not is_empty(db, News):
        return
    now = datetime.now(timezone.utc)
    samples = (
        ("Курс долара на міжбанку: підсумки тижня", NewsCategory.CURRENCY),
        ("НБУ зберіг облікову ставку без змін", NewsCategory.ECONOMY),
        ("Bitcoin тримається вище ключового рівня підтримки", NewsCategory.CRYPTO),
        ("Інфляція в Україні: що кажуть аналітики", NewsCategory.ECONOMY),
        ("Ethereum: огляд ринку за добу", NewsCategory.CRYPTO),
    )
    for i, (title, category) in enumerate(samples, start=1):
        db.add(
            News(
                title=title,
                summary="Демонстраційна новина для тестування стрічки.",
                category=category,
                source_url=f"https://example.com/demo-news-{i}",
                source_name="Demo",
                published_at=now - timedelta(hours=i),
            )
        )
    db.commit()


def seed_game_items(db, user: User) -> None:
    if not is_empty(db, GameItem):
        return
    now = datetime.now(timezone.utc)
    for index in range(10):
        lat = Decimal(str(round(CENTER_LAT + random.uniform(-0.01, 0.01), 6)))
        lng = Decimal(str(round(CENTER_LNG + random.uniform(-0.01, 0.01), 6)))
        collected = index >= 5
        db.add(
            GameItem(
                latitude=lat,
                longitude=lng,
                points=random.choice((5, 10, 20)),
                status=GameItemStatus.COLLECTED if collected else GameItemStatus.ACTIVE,
                collected_by_user_id=user.id if collected else None,
                collected_at=now - timedelta(hours=index) if collected else None,
            )
        )
    db.commit()


def seed_rewards(db) -> None:
    if not is_empty(db, Reward):
        return
    db.add_all(
        [
            Reward(title="Стікерпак FinPulse", description="Набір наклейок з логотипом проєкту.", cost_points=50, stock=20),
            Reward(title="Брендована кружка", description="Керамічна кружка FinPulse.", cost_points=150, stock=10),
            Reward(title="Футболка FinPulse", description="Футболка з принтом проєкту.", cost_points=300, stock=5),
        ]
    )
    db.commit()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        user = seed_user(db)
        run_integration("currency", update_currency_rates, db)
        run_integration("crypto", update_crypto_rates, db)
        run_integration("metals", update_metal_rates, db)
        run_integration("news", update_news, db)
        seed_fallback_rates(db)
        seed_news_fallback(db)
        seed_game_items(db, user)
        seed_rewards(db)
        logger.info("Seed finished")
    finally:
        db.close()


if __name__ == "__main__":
    main()