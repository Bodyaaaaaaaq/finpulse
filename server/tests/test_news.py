"""Тести BE-4: GET /news з фільтрами category, search, limit, offset (ТЗ 5.2, 5.4)."""
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.news import News, NewsCategory

client = TestClient(app)  # без входу: новини - публічні дані (ТЗ 5.1)
NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)

SAMPLES = [
    ("НБУ зберіг облікову ставку", NewsCategory.ECONOMY),
    ("Курс долара на міжбанку", NewsCategory.CURRENCY),
    ("Bitcoin above 80k", NewsCategory.CRYPTO),
    ("Ethereum: огляд ринку", NewsCategory.CRYPTO),
    ("Інфляція сповільнилась", NewsCategory.ECONOMY),
]


@pytest.fixture
def news():
    with SessionLocal() as db:
        for i, (title, category) in enumerate(SAMPLES):
            db.add(News(
                title=title, summary=f"Опис {i}", category=category, source_url=f"https://example.com/{i}",
                source_name="Demo", image_url=None, published_at=NOW - timedelta(hours=i),
            ))
        db.commit()


def titles(response) -> list[str]:
    return [item["title"] for item in response.json()["items"]]


def test_news_is_public_and_empty_without_data():
    response = client.get("/api/news")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_news_newest_first_and_format(news):
    body = client.get("/api/news").json()

    assert body["total"] == 5
    assert titles(client.get("/api/news"))[0] == "НБУ зберіг облікову ставку"
    item = body["items"][0]
    assert set(item) == {"id", "title", "summary", "category", "sourceName", "sourceUrl", "imageUrl", "publishedAt"}
    assert item["category"] == "ECONOMY"
    assert item["sourceUrl"] == "https://example.com/0"


def test_news_filter_by_category(news):
    response = client.get("/api/news?category=CRYPTO")
    assert response.json()["total"] == 2
    assert titles(response) == ["Bitcoin above 80k", "Ethereum: огляд ринку"]


def test_news_unknown_category_returns_400():
    response = client.get("/api/news?category=METALS")
    assert response.status_code == 400
    assert response.json()["message"].startswith("Неправильне значення category")


def test_news_search_in_title(news):
    assert titles(client.get("/api/news?search=bitcoin")) == ["Bitcoin above 80k"]  # без урахування регістру
    assert titles(client.get("/api/news?search=долара")) == ["Курс долара на міжбанку"]


def test_news_search_treats_percent_literally(news):
    assert client.get("/api/news?search=%25").json()["total"] == 0  # %25 - це символ %


def test_news_pagination(news):
    first = client.get("/api/news?limit=2&offset=0")
    second = client.get("/api/news?limit=2&offset=2")

    assert first.json()["total"] == 5 and second.json()["total"] == 5
    assert titles(first) == ["НБУ зберіг облікову ставку", "Курс долара на міжбанку"]
    assert titles(second) == ["Bitcoin above 80k", "Ethereum: огляд ринку"]


def test_news_filters_combine(news):
    response = client.get("/api/news?category=CRYPTO&search=ethereum")
    assert response.json()["total"] == 1


def test_news_negative_offset_returns_400():
    response = client.get("/api/news?offset=-1")
    assert response.status_code == 400
    assert response.json() == {"message": "Поле offset замале: мінімум 0"}
