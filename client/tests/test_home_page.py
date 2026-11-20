"""Головна: секції з курсами, режим «Редагувати», збереження вибору, помилки."""
import flet as ft
import pytest

from pages import home
from services.api_client import ApiError
from services.rates_service import RateItem
from state.home_state import HomeState
from tests.helpers import Ctx, find, run, texts


class Prefs:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value):
        self.data[key] = value


def make_items():
    return {
        "cur": [RateItem("currency", "USD", "USD", "Долар США", 44.6648, "₴", 0.37),
                RateItem("currency", "EUR", "EUR", "Євро", 51.2372, "₴", None),
                RateItem("currency", "GBP", "GBP", "Фунт стерлінгів", 58.0, "₴", -0.2)],
        "crypto": [RateItem("crypto", "BTC", "BTC", "Bitcoin", 81277.08, "$", 1.8),
                   RateItem("crypto", "ETH", "ETH", "Ethereum", 2636.52, "$", -0.6),
                   RateItem("crypto", "SOL", "SOL", "Solana", 142.1, "$", -2.3)],
        "metals": [RateItem("metal", "gold", "Gold", "Золото", 4378.78, "$", 1.2),
                   RateItem("metal", "silver", "Silver", "Срібло", 35.0, "$", None)],
    }


@pytest.fixture
def state(monkeypatch):
    fresh = HomeState()
    monkeypatch.setattr(home, "home_state", fresh)
    return fresh


@pytest.fixture
def data(monkeypatch):
    items = make_items()

    async def cur(): return items["cur"]
    async def crypto(search=None, limit=30, client=None): return items["crypto"]
    async def metals(): return items["metals"]

    monkeypatch.setattr(home, "fetch_currency", cur)
    monkeypatch.setattr(home, "fetch_crypto", crypto)
    monkeypatch.setattr(home, "fetch_metals", metals)
    return items


def open_home(wide=False):
    ctx = Ctx(wide)
    page = home.build(ctx)
    ctx.page.run_pending()
    return ctx, page


def edit_button(page):
    return next(b for b in find(page, ft.Button) if b.content in ("Редагувати", "Готово"))


def test_shows_selected_rates_by_section(state, data):
    _, page = open_home()
    shown = texts(page)
    for expected in ("Головна", "Курси обміну", "USD", "EUR", "Криптовалюти", "BTC", "ETH",
                     "Метали", "Gold", "44,6648₴", "51,2372₴", "81 277,08$", "2 636,52$", "4 378,78$"):
        assert expected in shown
    for hidden in ("GBP", "SOL", "Silver"):
        assert hidden not in shown
    assert edit_button(page).content == "Редагувати"


def test_metals_section_is_labeled_per_gram(state, data):
    _, page = open_home()
    assert "Метали" in texts(page) and "ціна за грам" in texts(page)
    other = [t for t in texts(page) if t == "ціна за грам"]
    assert len(other) == 1  # підпис лише в секції металів
    run(edit_button(page).on_click(None))
    assert "ціна за грам" in texts(page)


def test_shows_change_indicator_and_update_time(state, data):
    _, page = open_home()
    shown = texts(page)
    assert "▲ 0,4%" in shown and "▼ 0,6%" in shown and "▲ 1,8%" in shown  # 0,37 округляється до 0,4
    assert any(t.startswith("Дані станом на") for t in shown) is False  # у тестових даних немає часу
    green = {t.value for t in find(page, ft.Text) if t.visible and t.color == "#219A47"}
    red = {t.value for t in find(page, ft.Text) if t.visible and t.color == "#D62E2E"}
    assert "▲ 1,8%" in green and "▼ 0,6%" in red


def test_update_time_is_shown_when_known(state, monkeypatch, data):
    from datetime import datetime, timezone
    moment = datetime(2026, 11, 16, 9, 40, tzinfo=timezone.utc)
    data["cur"][0] = RateItem("currency", "USD", "USD", "Долар США", 44.6648, "₴", 0.37, moment)
    _, page = open_home()
    assert f"Дані станом на {moment.astimezone().strftime('%H:%M')}" in texts(page)


def test_loading_spinner_before_data_arrives(state, data):
    ctx = Ctx()
    page = home.build(ctx)  # завдання ще не виконано
    assert find(page, ft.ProgressRing)
    ctx.page.run_pending()
    assert not find(page, ft.ProgressRing)


def test_edit_mode_lists_everything_with_switches(state, data):
    ctx, page = open_home()
    run(edit_button(page).on_click(None))
    shown = texts(page)
    assert "Оберіть, що показувати на головній" in shown
    for expected in ("GBP", "Фунт стерлінгів", "SOL", "Solana", "Silver", "Срібло"):
        assert expected in shown
    assert edit_button(page).content == "Готово"
    switches = find(page, ft.Switch)
    assert len(switches) == 8
    assert [s.value for s in switches] == [True, True, False, True, True, False, True, False]


def test_switch_updates_and_saves_selection(state, data):
    prefs = Prefs()
    from state.home_state import HomeStore
    run(state.load(HomeStore(prefs)))
    ctx, page = open_home()
    run(edit_button(page).on_click(None))
    gbp = find(page, ft.Switch)[2]
    gbp.value = True
    run(gbp.on_change(None))
    assert state.is_selected("currency:GBP") and prefs.data  # збережено
    run(edit_button(page).on_click(None))  # «Готово»
    assert "GBP" in texts(page) and "58,0000₴" in texts(page)


def test_unselecting_everything_shows_hint(state, data):
    for key in list(state.selected):
        state.toggle(key)
    _, page = open_home()
    assert any("Нічого не вибрано" in t for t in texts(page))


def test_partial_failure_still_shows_loaded_sections(state, data, monkeypatch):
    async def broken(): raise ApiError("Не вдалося звʼязатися із сервером")
    monkeypatch.setattr(home, "fetch_metals", broken)
    _, page = open_home()
    shown = texts(page)
    assert "USD" in shown and "BTC" in shown and "Gold" not in shown
    assert not any("Не вдалося" in t for t in shown)


def test_total_failure_shows_error_and_retry(state, data, monkeypatch):
    calls = {"n": 0}

    async def broken():
        calls["n"] += 1
        raise ApiError("Не вдалося звʼязатися із сервером")

    async def broken_crypto(search=None, limit=30, client=None): await broken()

    monkeypatch.setattr(home, "fetch_currency", broken)
    monkeypatch.setattr(home, "fetch_crypto", broken_crypto)
    monkeypatch.setattr(home, "fetch_metals", broken)
    ctx, page = open_home()
    assert "Не вдалося звʼязатися із сервером" in texts(page)
    retry = next(b for b in find(page, ft.TextButton) if b.content.value == "Повторити")

    monkeypatch.setattr(home, "fetch_currency", lambda: _async(data["cur"]))
    run(retry.on_click(None))
    assert "USD" in texts(page)


async def _async(value):
    return value


def test_wide_layout_is_centered(state, data):
    _, page = open_home(wide=True)
    assert isinstance(page, ft.ResponsiveRow)
