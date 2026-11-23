"""Повні списки валют і металів (кнопка «Усі» на головній): рядки, підпис, помилка, порожній список, назад."""
import flet as ft

from pages import currencies, metals
from services.api_client import ApiError
from services.rates_service import RateItem
from tests.helpers import Ctx, find, run, texts

CUR = [RateItem("currency", "USD", "USD", "Долар США", 44.6648, "₴", 0.37),
       RateItem("currency", "PLN", "PLN", "Злотий", 12.3, "₴", -0.2)]
MET = [RateItem("metal", "gold", "Gold", "Золото", 4378.78, "$", 1.2)]


def open_page(module, monkeypatch, fetch_name, behaviour):
    async def fake():
        return behaviour()

    monkeypatch.setattr(module, fetch_name, fake)
    ctx = Ctx()
    page = module.build(ctx)
    ctx.page.run_pending()
    return ctx, page


def test_currency_list_shows_every_currency(monkeypatch):
    _, page = open_page(currencies, monkeypatch, "fetch_currency", lambda: CUR)
    shown = texts(page)
    for expected in ("Курси обміну", "USD", "Долар США", "44,6648₴", "PLN", "Злотий", "12,3000₴"):
        assert expected in shown


def test_metals_list_has_per_gram_caption(monkeypatch):
    _, page = open_page(metals, monkeypatch, "fetch_metals", lambda: MET)
    shown = texts(page)
    assert "Метали" in shown and "ціна за грам" in shown and "Золото" in shown and "4 378,78$" in shown


def test_back_button_returns_home(monkeypatch):
    ctx, page = open_page(currencies, monkeypatch, "fetch_currency", lambda: CUR)
    back = next(b for b in find(page, ft.TextButton) if b.content.value == "‹ Головна")
    run(back.on_click(None))
    assert ctx.went == ["/"]


def test_empty_list(monkeypatch):
    _, page = open_page(currencies, monkeypatch, "fetch_currency", lambda: [])
    assert "Немає даних" in texts(page)


def test_error_and_retry(monkeypatch):
    state = {"fail": True}

    def behaviour():
        if state["fail"]:
            raise ApiError("Не вдалося звʼязатися із сервером")
        return CUR

    _, page = open_page(currencies, monkeypatch, "fetch_currency", behaviour)
    assert "Не вдалося звʼязатися із сервером" in texts(page)
    state["fail"] = False
    retry = next(b for b in find(page, ft.TextButton) if b.content.value == "Повторити")
    run(retry.on_click(None))
    assert "Долар США" in texts(page)
