"""Новини: стрічка, фільтр за категорією, пошук, «Показати ще», відкриття статті, помилки."""
from datetime import datetime, timedelta, timezone

import flet as ft

from pages import news
from services.api_client import ApiError
from services.news_service import NewsItem, NewsPage
from tests.helpers import Ctx, find, run, texts

NOW = datetime.now(timezone.utc)


def make(n, category="CURRENCY", title=None, hours=2, image="https://example.com/i.jpg"):
    return NewsItem(f"id{n}", title or f"Новина {n}", "опис", category, "Мінфін", f"https://example.com/{n}",
                    image, NOW - timedelta(hours=hours))


ALL = [make(1, "CURRENCY", "НБУ залишив облікову ставку без змін", 2),
       make(2, "CRYPTO", "Біткоїн торгується вище 81 тис. доларів", 3),
       make(3, "ECONOMY", "Інфляція в Україні сповільнилася", 5, image=None)]


def patch_fetch(monkeypatch, behaviour):
    calls = []

    async def fake(category=None, search=None, offset=0, limit=20, client=None):
        calls.append((category, search, offset))
        return behaviour(category, search, offset)

    monkeypatch.setattr(news, "fetch_news", fake)
    monkeypatch.setattr(news, "SEARCH_DELAY", 0)
    return calls


def by_filter(category, search, offset):
    rows = [n for n in ALL if (category is None or n.category == category)
            and (not search or search.lower() in n.title.lower())]
    return NewsPage(rows, len(rows))


def open_page(monkeypatch, behaviour=by_filter):
    calls = patch_fetch(monkeypatch, behaviour)
    ctx = Ctx()
    page = news.build(ctx)
    ctx.page.run_pending()
    return ctx, page, calls


def chip(page, label):
    return next(c for c in find(page, ft.Container) if isinstance(c.content, ft.Text) and c.content.value == label)


def test_lists_cards_with_category_and_age(monkeypatch):
    _, page, calls = open_page(monkeypatch)
    shown = texts(page)
    for expected in ("Новини", "НБУ залишив облікову ставку без змін", "Валюти · 2 год тому",
                     "Крипта · 3 год тому", "Економіка · 5 год тому"):
        assert expected in shown
    assert calls == [(None, None, 0)]
    assert [f.hint_text for f in find(page, ft.TextField)] == ["Пошук у новинах"]


def test_filter_chips_in_order_with_active_first(monkeypatch):
    _, page, _ = open_page(monkeypatch)
    labels = [c.content.value for c in find(page, ft.Container)
              if isinstance(c.content, ft.Text) and c.content.value in ("Усі", "Валюти", "Крипта", "Економіка")]
    assert labels == ["Усі", "Валюти", "Крипта", "Економіка"]
    assert chip(page, "Усі").bgcolor == "#0088FF" and chip(page, "Валюти").bgcolor == "#F7F7F7"


def test_image_is_shown_only_when_news_has_one(monkeypatch):
    _, page, _ = open_page(monkeypatch)
    sources = [i.src for i in find(page, ft.Image)]
    assert sources == ["https://example.com/i.jpg"] * 2  # третя новина без зображення — сірий квадрат


def test_news_without_image_gets_category_tile(monkeypatch):
    _, page, _ = open_page(monkeypatch)
    icons = [i.icon for i in find(page, ft.Icon)]
    assert icons == [ft.Icons.TRENDING_UP]  # лише третя новина (Економіка) без фото
    tile = next(c for c in find(page, ft.Container) if isinstance(c.content, ft.Icon))
    assert tile.bgcolor == "#26A17B"


def test_failed_image_falls_back_to_tile(monkeypatch):
    _, page, _ = open_page(monkeypatch)
    image = find(page, ft.Image)[0]  # перша новина — Валюти
    assert isinstance(image.error_content.content, ft.Icon)
    assert image.error_content.content.icon == ft.Icons.CURRENCY_EXCHANGE
    assert image.error_content.bgcolor == "#2F4A9A"


def test_tile_per_category_and_unknown_category():
    from components.news_card import tile
    for category, icon in (("CURRENCY", ft.Icons.CURRENCY_EXCHANGE), ("CRYPTO", ft.Icons.CURRENCY_BITCOIN),
                           ("ECONOMY", ft.Icons.TRENDING_UP), ("OTHER", ft.Icons.NEWSPAPER)):
        assert tile(make(1, category, image=None)).content.icon == icon


def test_category_filter_requests_and_highlights(monkeypatch):
    ctx, page, calls = open_page(monkeypatch)
    chip(page, "Крипта").on_click(None)
    ctx.page.run_pending()
    assert calls[-1] == ("CRYPTO", None, 0)
    shown = texts(page)
    assert "Біткоїн торгується вище 81 тис. доларів" in shown and "НБУ залишив облікову ставку без змін" not in shown
    assert chip(page, "Крипта").bgcolor == "#0088FF" and chip(page, "Усі").bgcolor == "#F7F7F7"


def test_selecting_active_category_does_not_reload(monkeypatch):
    ctx, page, calls = open_page(monkeypatch)
    chip(page, "Усі").on_click(None)
    ctx.page.run_pending()
    assert len(calls) == 1


def test_search_combines_with_category(monkeypatch):
    ctx, page, calls = open_page(monkeypatch)
    chip(page, "Валюти").on_click(None)
    ctx.page.run_pending()
    field = find(page, ft.TextField)[0]
    field.value = "нбу"
    run(field.on_change(None))
    assert calls[-1] == ("CURRENCY", "нбу", 0)
    assert "НБУ залишив облікову ставку без змін" in texts(page)


def test_empty_result(monkeypatch):
    _, page, _ = open_page(monkeypatch, lambda c, s, o: NewsPage([], 0))
    assert "Новин не знайдено" in texts(page)


def test_show_more_appends_next_page(monkeypatch):
    first, second = [make(i) for i in range(1, 4)], [make(i) for i in range(4, 6)]

    def behaviour(category, search, offset):
        return NewsPage(first if offset == 0 else second, 5)

    ctx, page, calls = open_page(monkeypatch, behaviour)
    more = next(b for b in find(page, ft.TextButton) if b.content.value == "Показати ще")
    run(more.on_click(None))
    assert calls[-1] == (None, None, 3)
    shown = texts(page)
    assert all(f"Новина {i}" in shown for i in range(1, 6))
    assert not [b for b in find(page, ft.TextButton) if b.content.value == "Показати ще"]


def test_no_show_more_when_everything_loaded(monkeypatch):
    _, page, _ = open_page(monkeypatch)
    assert not [b for b in find(page, ft.TextButton) if b.content.value == "Показати ще"]


def test_click_opens_source_url(monkeypatch):
    opened = []

    async def fake_open(url):
        opened.append(url)

    monkeypatch.setattr(news, "open_url", fake_open)
    ctx, page, _ = open_page(monkeypatch)
    card = next(c for c in find(page, ft.Container) if c.on_click and "Біткоїн" in str(texts(c)))
    card.on_click(None)
    ctx.page.run_pending()
    assert opened == ["https://example.com/2"]


def test_failed_open_shows_message(monkeypatch):
    async def broken(url):
        raise RuntimeError("no browser")

    monkeypatch.setattr(news, "open_url", broken)
    ctx, page, _ = open_page(monkeypatch)
    card = next(c for c in find(page, ft.Container) if c.on_click and "Біткоїн" in str(texts(c)))
    card.on_click(None)
    ctx.page.run_pending()
    assert "Не вдалося відкрити посилання" in texts(page)


def test_error_shows_message_and_retry(monkeypatch):
    state = {"fail": True}

    def behaviour(category, search, offset):
        if state["fail"]:
            raise ApiError("Не вдалося звʼязатися із сервером")
        return by_filter(category, search, offset)

    _, page, _ = open_page(monkeypatch, behaviour)
    shown = texts(page)
    assert "Не вдалося звʼязатися із сервером" in shown and "Новин не знайдено" not in shown
    state["fail"] = False
    retry = next(b for b in find(page, ft.TextButton) if b.content.value == "Повторити")
    run(retry.on_click(None))
    assert "НБУ залишив облікову ставку без змін" in texts(page)


def test_stale_response_is_dropped(monkeypatch):
    """Відповідь на старий пошук не перезаписує результат нового."""
    import asyncio
    ctx = Ctx()

    async def scenario():
        gate = asyncio.Event()

        async def fake(category=None, search=None, offset=0, limit=20, client=None):
            if search == "slow":
                await gate.wait()
                return NewsPage([ALL[0]], 1)
            return NewsPage([ALL[1]], 1)

        monkeypatch.setattr(news, "fetch_news", fake)
        monkeypatch.setattr(news, "SEARCH_DELAY", 0)
        page = news.build(ctx)
        field = find(page, ft.TextField)[0]
        field.value = "slow"
        first = asyncio.create_task(field.on_change(None))
        await asyncio.sleep(0.01)
        field.value = "fast"
        await field.on_change(None)
        gate.set()
        await first
        return page

    shown = texts(run(scenario()))
    assert "Біткоїн торгується вище 81 тис. доларів" in shown and "НБУ залишив облікову ставку без змін" not in shown
