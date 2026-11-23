"""Новини (FE-6, сервер — BE-4): стрічка з фільтром за категорією, пошуком і пагінацією. Адреса публічна."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from services.api_client import ApiClient, api as default_api
from services.rates_service import parse_time

PAGE_SIZE = 20

# (значення category для сервера, підпис у фільтрі). None — «Усі».
CATEGORIES: list[tuple[Optional[str], str]] = [
    (None, "Усі"),
    ("CURRENCY", "Валюти"),
    ("CRYPTO", "Крипта"),
    ("ECONOMY", "Економіка"),
]
CATEGORY_LABELS = {code: label for code, label in CATEGORIES if code}


@dataclass(frozen=True)
class NewsItem:
    id: str
    title: str
    summary: str
    category: str                   # CURRENCY | CRYPTO | ECONOMY
    source_name: str
    source_url: str
    image_url: Optional[str]
    published_at: Optional[datetime]

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS.get(self.category, "")


@dataclass(frozen=True)
class NewsPage:
    items: list[NewsItem]
    total: int


def _item(row: dict) -> NewsItem:
    return NewsItem(
        id=str(row["id"]), title=row["title"], summary=row.get("summary") or "",
        category=row.get("category") or "", source_name=row.get("sourceName") or "",
        source_url=row["sourceUrl"], image_url=row.get("imageUrl") or None,
        published_at=parse_time(row.get("publishedAt")),
    )


async def fetch_news(category: Optional[str] = None, search: Optional[str] = None,
                     offset: int = 0, limit: int = PAGE_SIZE,
                     client: ApiClient = default_api) -> NewsPage:
    params: dict = {"limit": limit, "offset": offset}
    if category:
        params["category"] = category
    if search and search.strip():
        params["search"] = search.strip()
    data = await client.get("/news", params=params)
    return NewsPage([_item(r) for r in data["items"]], int(data["total"]))


def format_age(moment: Optional[datetime], now: Optional[datetime] = None) -> str:
    """'щойно', '5 хв тому', '2 год тому', 'вчора', '3 дн тому', далі — дата '12.11.2026'."""
    if moment is None:
        return ""
    now = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    seconds = (now - moment).total_seconds()
    if seconds < 60:
        return "щойно"  # зокрема, якщо годинник сервера трохи випереджає клієнт
    if seconds < 3600:
        return f"{int(seconds // 60)} хв тому"
    if seconds < 86400:
        return f"{int(seconds // 3600)} год тому"
    days = int(seconds // 86400)
    if days == 1:
        return "вчора"
    if days < 7:
        return f"{days} дн тому"
    return moment.astimezone().strftime("%d.%m.%Y")
