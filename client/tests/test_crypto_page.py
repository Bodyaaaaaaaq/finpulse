"""Криптовалюти: список, зміна за 24 год, пошук із затримкою, порожній результат, помилка."""
import flet as ft

from pages import crypto
from services.api_client import ApiError
from services.rates_service import RateItem
from tests.helpers import Ctx, find, run, texts

ALL = [RateItem("crypto", "BTC", "BTC", "Bitcoin", 81277.08, "$", 1.8),
       RateItem("crypto", "ETH", "ETH", "Ethereum", 2636.52, "$", -0.6),
       RateItem("crypto", "USDT", "USDT", "Tether", 1.0, "$", 0.0)]


def patch_fetch(monkeypatch, behaviour):
    calls = []

    async def fake(search=None, limit=30, client=None):
        calls.append(search)
        return behaviour(search)

    monkeypatch.setattr(crypto, "fetch_crypto", fake)
    monkeypatch.setattr(crypto, "SEARCH_DELAY", 0)
    return calls


def open_page(monkeypatch, behaviour=lambda s: ALL):
    calls = patch_fetch(monkeypatch, behaviour)
    ctx = Ctx()
    page = crypto.build(ctx)
    ctx.page.run_pending()
    return ctx, page, calls


def test_lists_coins_with_price_and_change(monkeypatch):
    _, page, calls = open_page(monkeypatch)
    shown = texts(page)
    for expected in ("Криптовалюти", "BTC", "Bitcoin", "81 277,08$", "▲ 1,8%", "ETH", "▼ 0,6%",
                     "USDT", "Tether", "1,00$", "▲ 0,0%"):
        assert expected in shown
    assert calls == [None]
    assert [f.hint_text for f in find(page, ft.TextField)] == ["Пошук монети"]


def test_change_color_is_red_for_fall_and_green_for_growth(monkeypatch):
    _, page, _ = open_page(monkeypatch)
    colors = {t.value: t.color for t in find(page, ft.Text) if t.visible}
    assert colors["▲ 1,8%"] == "#219A47" and colors["▼ 0,6%"] == "#D62E2E"


def test_update_time_caption(monkeypatch):
    from datetime import datetime, timezone
    moment = datetime(2026, 11, 16, 9, 40, tzinfo=timezone.utc)
    items = [RateItem("crypto", "BTC", "BTC", "Bitcoin", 1.0, "$", 1.0, moment)]
    _, page, _ = open_page(monkeypatch, lambda s: items)
    assert f"Дані станом на {moment.astimezone().strftime('%H:%M')}" in texts(page)


def test_search_sends_query_and_shows_result(monkeypatch):
    ctx, page, calls = open_page(
        monkeypatch, lambda s: [c for c in ALL if s is None or s.lower() in c.name.lower()])
    field = find(page, ft.TextField)[0]
    field.value = "teth"
    run(field.on_change(None))
    assert calls == [None, "teth"]
    shown = texts(page)
    assert "Tether" in shown and "Bitcoin" not in shown


def test_search_with_no_matches(monkeypatch):
    _, page, _ = open_page(monkeypatch, lambda s: [] if s else ALL)
    field = find(page, ft.TextField)[0]
    field.value = "zzz"
    run(field.on_change(None))
    assert "Нічого не знайдено" in texts(page)


def test_clearing_search_reloads_full_list(monkeypatch):
    _, page, calls = open_page(
        monkeypatch, lambda s: [c for c in ALL if s is None or s.lower() in c.name.lower()])
    field = find(page, ft.TextField)[0]
    field.value = "teth"
    run(field.on_change(None))
    field.value = ""
    run(field.on_change(None))
    assert calls == [None, "teth", None] and "Bitcoin" in texts(page)


def test_stale_search_response_is_dropped(monkeypatch):
    """Якщо поки йшов запит, користувач ввів інше — стара відповідь не перезаписує нову."""
    import asyncio
    ctx = Ctx()
    release_first = asyncio.Event

    async def scenario():
        gate = release_first()

        async def fake(search=None, limit=30, client=None):
            if search == "slow":
                await gate.wait()
                return [ALL[0]]
            return [ALL[2]]

        monkeypatch.setattr(crypto, "fetch_crypto", fake)
        monkeypatch.setattr(crypto, "SEARCH_DELAY", 0)
        page = crypto.build(ctx)
        field = find(page, ft.TextField)[0]
        field.value = "slow"
        first = asyncio.create_task(field.on_change(None))
        await asyncio.sleep(0.01)
        field.value = "fast"
        await field.on_change(None)
        gate.set()
        await first
        return page

    page = run(scenario())
    shown = texts(page)
    assert "Tether" in shown and "Bitcoin" not in shown


def test_error_shows_message_and_retry(monkeypatch):
    state = {"fail": True}

    def behaviour(search):
        if state["fail"]:
            raise ApiError("Не вдалося звʼязатися із сервером")
        return ALL

    _, page, _ = open_page(monkeypatch, behaviour)
    assert "Не вдалося звʼязатися із сервером" in texts(page)
    state["fail"] = False
    retry = next(b for b in find(page, ft.TextButton) if b.content.value == "Повторити")
    run(retry.on_click(None))
    assert "Bitcoin" in texts(page)
