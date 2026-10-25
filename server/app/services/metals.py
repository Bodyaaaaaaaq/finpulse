import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.metal_rate import MetalRate, MetalType

logger = logging.getLogger(__name__)

METALS_API_URL = os.getenv("METALS_API_URL", "https://api.gold-api.com")
GRAMS_PER_TROY_OUNCE = Decimal("31.1035")

SYMBOLS = {
    "XAU": MetalType.GOLD,
    "XAG": MetalType.SILVER,
    "XPT": MetalType.PLATINUM,
    "XPD": MetalType.PALLADIUM,
}


def fetch_price_per_ounce(symbol: str) -> Decimal:
    last_error = None
    for attempt in (1, 2):
        try:
            response = httpx.get(f"{METALS_API_URL}/price/{symbol}", timeout=15)
            response.raise_for_status()
            return Decimal(str(response.json()["price"]))
        except (httpx.HTTPError, ValueError, KeyError, ArithmeticError) as exc:
            last_error = exc
            logger.warning("Metals request %s failed (attempt %s): %s", symbol, attempt, exc)
    raise RuntimeError(f"Metals API unavailable for {symbol}") from last_error


def update_metal_rates(db: Session | None = None) -> int:
    own_session = db is None
    db = db or SessionLocal()
    updated = 0
    try:
        now = datetime.now(timezone.utc)
        existing = {row.metal: row for row in db.scalars(select(MetalRate))}

        for symbol, metal in SYMBOLS.items():
            try:
                per_ounce = fetch_price_per_ounce(symbol)
            except RuntimeError:
                logger.error("%s not updated, keeping previous value", metal.value)
                continue

            per_gram = (per_ounce / GRAMS_PER_TROY_OUNCE).quantize(Decimal("0.000001"))
            row = existing.get(metal)
            if row is None:
                db.add(MetalRate(metal=metal, price_per_gram_usd=per_gram, updated_at=now))
            else:
                if row.price_per_gram_usd != per_gram:
                    row.previous_price_per_gram_usd = row.price_per_gram_usd
                    row.price_per_gram_usd = per_gram
                row.updated_at = now
            updated += 1

        db.commit()
        return updated
    except Exception:
        db.rollback()
        raise
    finally:
        if own_session:
            db.close()
