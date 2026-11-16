"""Сторінка профілю: дані користувача, зміна пароля, діалог видалення акаунта."""
import asyncio

import flet as ft

from pages import profile
from state.auth_state import auth_state


def run(coro):
    return asyncio.run(coro)


def find(control, cls):
    found = []

    def walk(c):
        if isinstance(c, cls):
            found.append(c)
        for attr in ("content", "controls", "actions"):
            child = getattr(c, attr, None)
            if isinstance(child, list):
                for x in child:
                    walk(x)
            elif child is not None and not isinstance(child, str):
                walk(child)

    walk(control)
    return found


class Page:
    def __init__(self):
        self.dialogs = []
        self.updates = 0

    def update(self):
        self.updates += 1

    def show_dialog(self, dialog):
        self.dialogs.append(dialog)

    def pop_dialog(self):
        return self.dialogs.pop() if self.dialogs else None


class Ctx:
    def __init__(self, wide=False):
        self.page, self.is_wide, self.expired = Page(), wide, 0

    async def session_expired(self):
        self.expired += 1


def setup_user():
    auth_state.set_session("t", {"name": "Іван", "email": "ivan@gmail.com", "points": 1500})


def texts(page):
    return [t.value for t in find(page, ft.Text) if t.visible]


def test_profile_shows_user_data():
    setup_user()
    page = profile.build(Ctx())
    shown = texts(page)
    for expected in ("Профіль", "Іван", "ivan@gmail.com", "Баланс", "1 500 балів", "Змінити пароль", "І"):
        assert expected in shown
    assert [f.password for f in find(page, ft.TextField)] == [True, True]
    assert [b.content for b in find(page, ft.Button)] == ["Зберегти", "Видалити акаунт"]


def test_profile_shows_address_when_server_returns_it():
    auth_state.set_session("t", {"name": "Іван", "email": "i@x.ua", "points": 0,
                                 "address": "м. Київ, вул. Хрещатик, 1"})
    assert "м. Київ, вул. Хрещатик, 1" in texts(profile.build(Ctx()))


def test_profile_wide_layout_is_centered():
    setup_user()
    page = profile.build(Ctx(wide=True))
    assert isinstance(page, ft.ResponsiveRow) and page.alignment == ft.MainAxisAlignment.CENTER


def _fill(page, old, new):
    fields = find(page, ft.TextField)
    fields[0].value, fields[1].value = old, new
    return fields


def test_save_validation_error_reenables_button():
    setup_user()
    page = profile.build(Ctx())
    _fill(page, "", "newpass12")
    save = find(page, ft.Button)[0]
    run(save.on_click(None))
    assert "Введіть поточний пароль" in texts(page) and save.disabled is False


def test_save_success_clears_fields_and_shows_message(monkeypatch):
    setup_user()
    page = profile.build(Ctx())
    fields = _fill(page, "oldpass1", "newpass12")
    save = find(page, ft.Button)[0]
    seen = {}

    async def ok(old, new, client=None):
        seen["disabled"], seen["args"] = save.disabled, (old, new)
        return None

    monkeypatch.setattr(profile, "submit_change_password", ok)
    run(save.on_click(None))
    assert seen == {"disabled": True, "args": ("oldpass1", "newpass12")}
    assert [f.value for f in fields] == ["", ""]
    assert "Пароль змінено" in texts(page) and save.disabled is False


def test_save_server_error_is_shown_and_fields_kept(monkeypatch):
    setup_user()
    page = profile.build(Ctx())
    fields = _fill(page, "wrongpass", "newpass12")

    async def fail(old, new, client=None):
        return "Неправильний поточний пароль"

    monkeypatch.setattr(profile, "submit_change_password", fail)
    run(find(page, ft.Button)[0].on_click(None))
    assert "Неправильний поточний пароль" in texts(page)
    assert fields[0].value == "wrongpass" and "Пароль змінено" not in texts(page)


def _open_dialog(ctx):
    setup_user()
    page = profile.build(ctx)
    run(find(page, ft.Button)[1].on_click(None))
    assert len(ctx.page.dialogs) == 1
    dialog = ctx.page.dialogs[0]
    confirm = find(dialog, ft.TextButton)[-1]
    return dialog, find(dialog, ft.TextField)[0], confirm


def test_delete_opens_confirmation_dialog_with_password_field():
    ctx = Ctx()
    dialog, password, _ = _open_dialog(ctx)
    assert dialog.modal is True and password.password is True


def test_delete_requires_password_and_keeps_dialog():
    ctx = Ctx()
    dialog, _, confirm = _open_dialog(ctx)
    run(confirm.on_click(None))
    assert "Введіть пароль для підтвердження" in texts(dialog)
    assert ctx.page.dialogs == [dialog] and ctx.expired == 0


def test_delete_wrong_password_shows_error_and_keeps_dialog(monkeypatch):
    ctx = Ctx()
    dialog, password, confirm = _open_dialog(ctx)
    password.value = "bad"

    async def fail(c, pwd, client=None):
        return "Неправильний пароль"

    monkeypatch.setattr(profile, "submit_delete_account", fail)
    run(confirm.on_click(None))
    assert "Неправильний пароль" in texts(dialog)
    assert confirm.disabled is False and ctx.page.dialogs == [dialog]


def test_delete_success_closes_dialog_and_ends_session(monkeypatch):
    ctx = Ctx()
    dialog, password, confirm = _open_dialog(ctx)
    password.value = "secret123"

    async def ok(c, pwd, client=None):
        await c.session_expired()
        return None

    monkeypatch.setattr(profile, "submit_delete_account", ok)
    run(confirm.on_click(None))
    assert ctx.page.dialogs == [] and ctx.expired == 1


def test_cancel_closes_dialog_without_request():
    ctx = Ctx()
    dialog, _, _ = _open_dialog(ctx)
    cancel = find(dialog, ft.TextButton)[0]
    run(cancel.on_click(None))
    assert ctx.page.dialogs == [] and ctx.expired == 0


def test_page_uses_shared_service():
    from services import profile_service
    assert profile.submit_change_password is profile_service.submit_change_password
    assert profile.submit_delete_account is profile_service.submit_delete_account
