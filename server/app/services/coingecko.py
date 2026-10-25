import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.crypto_rate import CryptoRate

logger = logging.getLogger(__name__)

COINGECKO_API_URL = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
TOP_N = 100


def fetch_top_coins() -> list[dict]:
    last_error = None
    for attempt in (1, 2):
        try:
            response = httpx.get(
                f"{COINGECKO_API_URL}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": TOP_N,
                    "page": 1,
                    "price_change_percentage": "24h",
                },
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            logger.warning("CoinGecko request failed (attempt %s): %s", attempt, exc)
    raise RuntimeError("CoinGecko API unavailable") from last_error


def update_crypto_rates(db: Session | None = None) -> int:
    own_session = db is None
    db = db or SessionLocal()
    try:
        try:
            data = fetch_top_coins()
        except RuntimeError:
            logger.error("Crypto rates not updated, keeping previous values")
            return 0

        now = datetime.now(timezone.utc)
        existing = {row.coin_id: row for row in db.scalars(select(CryptoRate))}

        for item in data:
            if item.get("current_price") is None:
                continue
            price = Decimal(str(item["current_price"]))
            change = item.get("price_change_percentage_24h")
            change = Decimal(str(change)) if change is not None else None

            row = existing.get(item["id"])
            if row is None:
                db.add(
                    CryptoRate(
                        coin_id=item["id"],
                        symbol=item["symbol"].upper(),
                        name=item["name"],
                        rank=item.get("market_cap_rank"),
                        price_usd=price,
                        change_24h=change,
                        updated_at=now,
                    )
                )
            else:
                row.symbol = item["symbol"].upper()
                row.name = item["name"]
                row.rank = item.get("market_cap_rank")
                row.price_usd = price
                row.change_24h = change
                row.updated_at = now

        db.commit()
        return len(data)
    except Exception:
        db.rollback()
        raise
    finally:
        if own_session:
            db.close()
