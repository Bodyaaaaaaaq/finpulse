"""Сторінки входу/реєстрації: наявність полів, блокування кнопки під час запиту, показ помилки."""
import asyncio
from types import SimpleNamespace

import flet as ft

import config
from pages import login, register
from services import auth_service


def run(coro):
    return asyncio.run(coro)


def find(control, cls):
    found = []

    def walk(c):
        if isinstance(c, cls):
            found.append(c)
        for attr in ("content", "controls"):
            child = getattr(c, attr, None)
            if isinstance(child, list):
                for x in child:
                    walk(x)
            elif child is not None and not isinstance(child, str):
                walk(child)

    walk(control)
    return found


class Ctx:
    def __init__(self):
        self.page = SimpleNamespace(update=lambda: None)
        self.routes = []

    async def go(self, route):
        self.routes.append(route)

    async def login(self, user):
        self.routes.append("/")


def test_login_page_layout_matches_design():
    page = login.build(Ctx())
    fields = find(page, ft.TextField)
    assert [f.password for f in fields] == [False, True]
    assert [b.content for b in find(page, ft.Button)] == ["Увійти"]
    texts = [t.value for t in find(page, ft.Text)]
    assert "FinPulse" in texts and "Курси, новини та гра в одному місці" in texts


def test_register_page_has_all_fields_including_address():
    page = register.build(Ctx())
    assert len(find(page, ft.TextField)) == 5
    assert "Адреса (обов’язково)" in [t.value for t in find(page, ft.Text)]


def test_register_page_without_address(monkeypatch):
    monkeypatch.setattr(register, "REGISTER_ADDRESS", False)
    page = register.build(Ctx())
    assert len(find(page, ft.TextField)) == 4


def _fill(page, values):
    for field, value in zip(find(page, ft.TextField), values):
        field.value = value


def test_login_shows_validation_error_and_reenables_button():
    ctx = Ctx()
    page = login.build(ctx)
    _fill(page, ["bad", "x"])
    button = find(page, ft.Button)[0]
    run(button.on_click(None))
    error = [t for t in find(page, ft.Text) if t.visible and t.color == "#D62E2E"][0]
    assert error.value == "Некоректний email" and button.disabled is False and ctx.routes == []


def test_login_button_disabled_during_request_and_error_shown(monkeypatch):
    ctx = Ctx()
    page = login.build(ctx)
    _fill(page, ["i@x.ua", "wrongpass"])
    button = find(page, ft.Button)[0]
    seen = {}

    async def slow_submit(c, email, password, client=None):
        seen["disabled_during"] = button.disabled
        return "Неправильний email або пароль"

    monkeypatch.setattr(login, "submit_login", slow_submit)
    run(button.on_click(None))
    assert seen["disabled_during"] is True and button.disabled is False
    shown = [t.value for t in find(page, ft.Text) if t.visible]
    assert "Неправильний email або пароль" in shown


def test_register_success_navigates_home(monkeypatch):
    ctx = Ctx()
    page = register.build(ctx)

    async def ok(c, *a, **k):
        await c.login({})
        return None

    monkeypatch.setattr(register, "submit_register", ok)
    run(find(page, ft.Button)[0].on_click(None))
    assert ctx.routes == ["/"]


def test_pages_use_the_shared_service():
    assert login.submit_login is auth_service.submit_login
    assert register.submit_register is auth_service.submit_register
