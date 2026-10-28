"""GET /api/crypto - топ криптовалют за ринковою капіталізацією (ТЗ 5.2, задача BE-4). Публічна адреса."""
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.dependencies import DbSession
from app.models.crypto_rate import CryptoRate
from app.schemas.rates import CryptoOut

router = APIRouter(prefix="/crypto", tags=["rates"])


@router.get("", response_model=list[CryptoOut])
def list_crypto_rates(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100, description="Скільки монет повернути")] = 20,
    search: Annotated[str | None, Query(max_length=50, description="Пошук за символом або назвою")] = None,
):
    query = select(CryptoRate)
    if search and search.strip():
        text = search.strip()
        query = query.where(
            or_(CryptoRate.symbol.icontains(text, autoescape=True), CryptoRate.name.icontains(text, autoescape=True))
        )
    # Спочатку найбільші за капіталізацією; монети без рейтингу - в кінці
    query = query.order_by(CryptoRate.rank.is_(None), CryptoRate.rank, CryptoRate.symbol).limit(limit)

    return [
        CryptoOut(
            symbol=row.symbol,
            name=row.name,
            rank=row.rank,
            price_usd=row.price_usd,
            change_24h=row.change_24h,
            updated_at=row.updated_at,
        )
        for row in db.scalars(query)
    ]
