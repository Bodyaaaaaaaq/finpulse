from datetime import datetime, timedelta, timezone

import pytest

from services import news_service as ns
from services.api_client import ApiError
from tests.helpers import run

ROW = {"id": "11111111-1111-1111-1111-111111111111", "title": "НБУ залишив облікову ставку без змін",
       "summary": "Короткий опис", "category": "CURRENCY", "sourceName": "Мінфін",
       "sourceUrl": "https://example.com/a", "imageUrl": "https://example.com/a.jpg",
       "publishedAt": "2026-11-16T09:40:00Z"}


class FakeApi:
    def __init__(self, data=None, error=None):
        self.data, self.error, self.calls = data, error, []

    async def get(self, path, **kw):
        self.calls.append((path, kw.get("params")))
        if self.error:
            raise self.error
        return self.data


def test_fetch_parses_items_and_total():
    api = FakeApi({"items": [ROW], "total": 41})
    page = run(ns.fetch_news(client=api))
    assert page.total == 41 and len(page.items) == 1
    item = page.items[0]
    assert (item.title, item.source_name, item.source_url, item.image_url) == (
        ROW["title"], "Мінфін", "https://example.com/a", "https://example.com/a.jpg")
    assert item.category_label == "Валюти"
    assert item.published_at == datetime(2026, 11, 16, 9, 40, tzinfo=timezone.utc)
    assert api.calls == [("/news", {"limit": 20, "offset": 0})]


def test_fetch_sends_filters_and_offset():
    api = FakeApi({"items": [], "total": 0})
    run(ns.fetch_news("CRYPTO", "  біткоїн ", offset=20, limit=10, client=api))
    assert api.calls[0][1] == {"limit": 10, "offset": 20, "category": "CRYPTO", "search": "біткоїн"}


def test_blank_search_is_not_sent():
    api = FakeApi({"items": [], "total": 0})
    run(ns.fetch_news(None, "   ", client=api))
    assert "search" not in api.calls[0][1] and "category" not in api.calls[0][1]


def test_missing_optional_fields():
    row = {**ROW, "imageUrl": None, "summary": None, "publishedAt": None, "category": "UNKNOWN"}
    item = run(ns.fetch_news(client=FakeApi({"items": [row], "total": 1}))).items[0]
    assert item.image_url is None and item.summary == "" and item.published_at is None
    assert item.category_label == ""


def test_api_error_propagates():
    with pytest.raises(ApiError):
        run(ns.fetch_news(client=FakeApi(error=ApiError("Не вдалося звʼязатися із сервером"))))


NOW = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("delta,expected", [
    (timedelta(seconds=20), "щойно"),
    (timedelta(seconds=-30), "щойно"),
    (timedelta(minutes=5), "5 хв тому"),
    (timedelta(hours=2, minutes=10), "2 год тому"),
    (timedelta(hours=30), "вчора"),
    (timedelta(days=3), "3 дн тому"),
])
def test_format_age(delta, expected):
    assert ns.format_age(NOW - delta, NOW) == expected


def test_format_age_old_news_shows_date_and_none_is_empty():
    old = NOW - timedelta(days=30)
    assert ns.format_age(old, NOW) == old.astimezone().strftime("%d.%m.%Y")
    assert ns.format_age(None, NOW) == ""
