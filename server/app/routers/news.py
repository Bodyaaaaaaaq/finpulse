"""GET /api/news - стрічка фінансових новин з фільтрами (ТЗ 5.2, 5.4, задача BE-4). Публічна адреса."""
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.dependencies import DbSession
from app.models.news import News, NewsCategory
from app.schemas.news import NewsItemOut, NewsPage

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=NewsPage)
def list_news(
    db: DbSession,
    category: Annotated[NewsCategory | None, Query(description="CURRENCY / CRYPTO / ECONOMY")] = None,
    search: Annotated[str | None, Query(max_length=100, description="Пошук у заголовку")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    filters = []
    if category is not None:
        filters.append(News.category == category)
    if search and search.strip():
        # На PostgreSQL пошук не залежить від регістру для будь-яких літер;
        # на SQLite (локально) - лише для латиниці
        filters.append(News.title.icontains(search.strip(), autoescape=True))

    total = db.scalar(select(func.count()).select_from(News).where(*filters))
    rows = db.scalars(
        select(News).where(*filters).order_by(News.published_at.desc(), News.id).limit(limit).offset(offset)
    )

    items = [
        NewsItemOut(
            id=row.id,
            title=row.title,
            summary=row.summary,
            category=row.category.value,
            source_name=row.source_name,
            source_url=row.source_url,
            image_url=row.image_url,
            published_at=row.published_at,
        )
        for row in rows
    ]
    return NewsPage(items=items, total=total)
