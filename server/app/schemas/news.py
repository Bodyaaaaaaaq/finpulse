"""Схеми відповідей для новин (ТЗ 5.2, 5.4, задача BE-4)."""
import uuid
from datetime import datetime

from app.schemas.rates import CamelModel


class NewsItemOut(CamelModel):
    id: uuid.UUID
    title: str
    summary: str
    category: str
    source_name: str
    source_url: str
    image_url: str | None
    published_at: datetime


class NewsPage(CamelModel):
    items: list[NewsItemOut]
    total: int  # скільки новин підходить під фільтр загалом (для пагінації)
