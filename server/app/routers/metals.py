"""GET /api/metals - ціни дорогоцінних металів за грам у USD (ТЗ 5.2, задача BE-4). Публічна адреса."""
from fastapi import APIRouter
from sqlalchemy import select

from app.dependencies import DbSession
from app.models.metal_rate import MetalRate, MetalType
from app.schemas.rates import MetalOut, change_percent

router = APIRouter(prefix="/metals", tags=["rates"])

# Порядок і назви для відображення
METAL_NAMES = {
    MetalType.GOLD: "Золото",
    MetalType.SILVER: "Срібло",
    MetalType.PLATINUM: "Платина",
    MetalType.PALLADIUM: "Паладій",
}
ORDER = list(METAL_NAMES)


@router.get("", response_model=list[MetalOut])
def list_metal_rates(db: DbSession):
    rows = sorted(db.scalars(select(MetalRate)), key=lambda row: ORDER.index(row.metal))
    return [
        MetalOut(
            metal=row.metal.value,
            name=METAL_NAMES[row.metal],
            price_per_gram_usd=row.price_per_gram_usd,
            previous_price_per_gram_usd=row.previous_price_per_gram_usd,
            change_percent=change_percent(row.price_per_gram_usd, row.previous_price_per_gram_usd),
            updated_at=row.updated_at,
        )
        for row in rows
    ]
