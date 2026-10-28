"""Схеми відповідей для курсів валют, криптовалют і металів (ТЗ 5.2, 5.3, задача BE-4).

Поля в Python - snake_case, у JSON - camelCase (rate_usd -> rateUsd), як у прикладах ТЗ.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


def change_percent(current: Decimal | None, previous: Decimal | None) -> float | None:
    """На скільки відсотків змінився курс відносно попереднього значення (None, якщо попереднього немає)."""
    if current is None or not previous:
        return None
    return round(float((current - previous) / previous * 100), 2)


class CurrencyOut(CamelModel):
    code: str
    name: str
    rate: float  # скільки гривень коштує 1 одиниця валюти (офіційний курс НБУ)
    previous_rate: float | None
    change_percent: float | None
    updated_at: datetime


class CryptoOut(CamelModel):
    symbol: str
    name: str
    rank: int | None
    price_usd: float
    # Явна назва: автоматично вийшло б change24H, а в ТЗ 5.3 - change24h
    change_24h: float | None = Field(alias="change24h")
    updated_at: datetime


class MetalOut(CamelModel):
    metal: str
    name: str
    price_per_gram_usd: float
    previous_price_per_gram_usd: float | None
    change_percent: float | None
    updated_at: datetime
