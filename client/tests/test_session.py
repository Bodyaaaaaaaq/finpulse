"""Сесія (FE-2): збереження токена, відновлення при запуску, оновлення профілю, вихід."""
import asyncio
from types import SimpleNamespace


from services import session_service
from services.api_client import ApiError
from state.auth_state import auth_state
from state.session_store import TOKEN_KEY, SessionStore


def run(coro):
    return asyncio.run(coro)


class FakePrefs:
    """Підміна ft.SharedPreferences."""

    def __init__(self, data=None, broken=False):
        self.data = dict(data or {})
        self.broken = broken

    async def get(self, key):
        if self.broken:
            raise RuntimeError("storage unavailable")
        return self.data.get(key)

    async def set(self, key, value):
        if self.broken:
            raise RuntimeError("storage unavailable")
        self.data[key] = value
        return True

    async def remove(self, key):
        if self.broken:
            raise RuntimeError("storage unavailable")
        self.data.pop(key, None)
        return True


class FakeApi:
    def __init__(self, me=None, error=None):
        self.me, self.error, self.calls = me, error, []

    async def get(self, path, **kw):
        self.calls.append(("GET", path))
        if self.error:
            raise self.error
        return self.me

    async def post(self, path, **kw):
        self.calls.append(("POST", path))
        if self.error:
            raise self.error


USER = {"id": "1", "name": "Іван", "email": "i@x.ua", "points": 150}


def test_store_roundtrip():
    store = SessionStore(FakePrefs())
    assert run(store.load_token()) is None
    run(store.save_token("abc"))
    assert run(store.load_token()) == "abc"
    run(store.clear())
    assert run(store.load_token()) is None


def test_store_survives_broken_storage():
    store = SessionStore(FakePrefs(broken=True))
    run(store.save_token("abc"))
    run(store.clear())
    assert run(store.load_token()) is None


def test_store_ignores_non_string_values():
    assert run(SessionStore(FakePrefs({TOKEN_KEY: 123})).load_token()) is None
    assert run(SessionStore(FakePrefs({TOKEN_KEY: ""})).load_token()) is None


def test_restore_without_saved_token():
    api = FakeApi(me=USER)
    assert run(session_service.restore_session(SessionStore(FakePrefs()), api)) is False
    assert api.calls == [] and not auth_state.is_authenticated


def test_restore_valid_token_sets_user():
    api = FakeApi(me=USER)
    assert run(session_service.restore_session(SessionStore(FakePrefs({TOKEN_KEY: "t"})), api)) is True
    assert auth_state.is_authenticated and auth_state.name == "Іван" and auth_state.points == 150
    assert api.calls == [("GET", "/auth/me")]


def test_restore_expired_token_is_dropped():
    prefs = FakePrefs({TOKEN_KEY: "old"})
    api = FakeApi(error=ApiError("Потрібно увійти в акаунт", 401))
    assert run(session_service.restore_session(SessionStore(prefs), api)) is False
    assert not auth_state.is_authenticated and TOKEN_KEY not in prefs.data


def test_restore_keeps_token_when_server_unreachable():
    prefs = FakePrefs({TOKEN_KEY: "tok"})
    api = FakeApi(error=ApiError("Не вдалося звʼязатися із сервером"))
    assert run(session_service.restore_session(SessionStore(prefs), api)) is False
    assert not auth_state.is_authenticated and prefs.data[TOKEN_KEY] == "tok"  # наступного запуску спробуємо знову


def test_refresh_user_updates_balance():
    auth_state.set_session("t", dict(USER))
    run(session_service.refresh_user(FakeApi(me={**USER, "points": 400})))
    assert auth_state.points == 400


def test_refresh_user_ignores_errors_and_guests():
    run(session_service.refresh_user(FakeApi(me=USER)))  # гість — нічого не робить
    assert auth_state.user is None
    auth_state.set_session("t", dict(USER))
    run(session_service.refresh_user(FakeApi(error=ApiError("x"))))
    assert auth_state.points == 150


def test_sign_out_calls_server_and_clears_everything():
    prefs = FakePrefs({TOKEN_KEY: "t"})
    api = FakeApi()
    auth_state.set_session("t", dict(USER))
    run(session_service.sign_out(SessionStore(prefs), api))
    assert api.calls == [("POST", "/auth/logout")]
    assert not auth_state.is_authenticated and prefs.data == {}


def test_sign_out_clears_even_if_server_fails():
    prefs = FakePrefs({TOKEN_KEY: "t"})
    auth_state.set_session("t", dict(USER))
    run(session_service.sign_out(SessionStore(prefs), FakeApi(error=ApiError("down"))))
    assert not auth_state.is_authenticated and prefs.data == {}


# ---- Router як контекст для сторінок
class RouterPage(SimpleNamespace):
    async def push_route(self, route):
        self.pushed.append(route)


def make_router(prefs=None):
    from router import Router

    page = RouterPage(width=390, route="/", views=[], pushed=[])
    return Router(page, SessionStore(prefs) if prefs is not None else None), page


def test_router_login_saves_token_and_goes_home():
    prefs = FakePrefs()
    r, page = make_router(prefs)
    auth_state.token = "jwt"
    run(r.login(USER))
    assert prefs.data[TOKEN_KEY] == "jwt" and auth_state.name == "Іван" and page.pushed == ["/"]


def test_router_session_expired_goes_to_login():
    prefs = FakePrefs({TOKEN_KEY: "t"})
    r, page = make_router(prefs)
    auth_state.set_session("t", dict(USER))
    run(r.session_expired())
    assert not auth_state.is_authenticated and prefs.data == {} and page.pushed == ["/login"]


def test_router_logout_without_store_still_works(monkeypatch):
    r, page = make_router()
    auth_state.set_session("t", dict(USER))
    run(r.logout())
    assert not auth_state.is_authenticated and page.pushed == ["/login"]


def test_router_logout_calls_server(monkeypatch):
    api = FakeApi()
    monkeypatch.setattr(session_service, "default_api", api, raising=False)
    import router as router_module

    async def fake_sign_out(store):
        await session_service.sign_out(store, api)

    monkeypatch.setattr(router_module, "sign_out", fake_sign_out)
    prefs = FakePrefs({TOKEN_KEY: "t"})
    r, page = make_router(prefs)
    auth_state.set_session("t", dict(USER))
    run(r.logout())
    assert api.calls == [("POST", "/auth/logout")] and prefs.data == {} and page.pushed == ["/login"]


def test_router_attach_subscribes_to_401():
    from services.api_client import api

    r, _ = make_router()
    r.attach()
    assert api.on_unauthorized == r.session_expired
    api.on_unauthorized = None
