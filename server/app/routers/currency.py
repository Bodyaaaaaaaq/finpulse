"""GET /api/currency - офіційні курси валют НБУ до гривні (ТЗ 5.2, задача BE-4). Публічна адреса."""
from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import DbSession
from app.models.currency_rate import CurrencyRate
from app.schemas.rates import CurrencyOut, change_percent

router = APIRouter(prefix="/currency", tags=["rates"])

# Ці валюти показуємо першими, решту - за абеткою
POPULAR = ["USD", "EUR", "PLN", "GBP"]


def _sort_key(row: CurrencyRate) -> tuple[int, str]:
    position = POPULAR.index(row.code) if row.code in POPULAR else len(POPULAR)
    return position, row.code


@router.get("", response_model=list[CurrencyOut])
def list_currency_rates(db: DbSession):
    rows = sorted(db.scalars(select(CurrencyRate)), key=_sort_key)
    return [
        CurrencyOut(
            code=row.code,
            name=row.name,
            rate=row.rate,
            previous_rate=row.previous_rate,
            change_percent=change_percent(row.rate, row.previous_rate),
            updated_at=row.updated_at,
        )
        for row in rows
    ]
