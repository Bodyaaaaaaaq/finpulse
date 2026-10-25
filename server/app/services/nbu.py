import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.currency_rate import CurrencyRate

logger = logging.getLogger(__name__)

NBU_API_URL = os.getenv(
    "NBU_API_URL",
    "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json",
)


def fetch_nbu_rates() -> list[dict]:
    last_error = None
    for attempt in (1, 2):
        try:
            response = httpx.get(NBU_API_URL, timeout=15)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            logger.warning("NBU request failed (attempt %s): %s", attempt, exc)
    raise RuntimeError("NBU API unavailable") from last_error


def update_currency_rates(db: Session | None = None) -> int:
    own_session = db is None
    db = db or SessionLocal()
    try:
        try:
            data = fetch_nbu_rates()
        except RuntimeError:
            logger.error("Currency rates not updated, keeping previous values")
            return 0

        now = datetime.now(timezone.utc)
        existing = {row.code: row for row in db.scalars(select(CurrencyRate))}

        for item in data:
            code = item["cc"]
            rate = Decimal(str(item["rate"]))
            row = existing.get(code)
            if row is None:
                db.add(CurrencyRate(code=code, name=item["txt"], rate=rate, updated_at=now))
            else:
                if row.rate != rate:
                    row.previous_rate = row.rate
                    row.rate = rate
                row.updated_at = now

        db.commit()
        return len(data)
    except Exception:
        db.rollback()
        raise
    finally:
        if own_session:
            db.close()