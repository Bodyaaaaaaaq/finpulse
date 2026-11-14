"""ApiClient: cookie-токен, видача токена сервером, розбір помилок, 401 (httpx.MockTransport, без сервера)."""
import asyncio

import httpx
import pytest

from services import api_client
from services.api_client import ApiClient, ApiError
from state.auth_state import auth_state


def run(coro):
    return asyncio.run(coro)


def make_client(monkeypatch, handler):
    real = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real(*args, **kwargs)

    monkeypatch.setattr(api_client.httpx, "AsyncClient", factory)
    return ApiClient(base_url="http://test")


def test_default_base_url_has_api_prefix():
    assert ApiClient().base_url.endswith("/api")


def test_get_returns_json(monkeypatch):
    c = make_client(monkeypatch, lambda r: httpx.Response(200, json={"status": "ok"}))
    assert run(c.get("/health")) == {"status": "ok"}


def test_empty_body_is_none(monkeypatch):
    c = make_client(monkeypatch, lambda r: httpx.Response(204))
    assert run(c.delete("/profile")) is None


def test_no_cookie_without_token(monkeypatch):
    seen = {}
    c = make_client(monkeypatch, lambda r: (seen.update(r.headers), httpx.Response(200, json={}))[1])
    run(c.get("/x"))
    assert "cookie" not in seen


def test_token_is_sent_as_cookie_like_the_server_expects(monkeypatch):
    auth_state.set_session("abc123")
    seen = {}
    c = make_client(monkeypatch, lambda r: (seen.update(r.headers), httpx.Response(200, json={}))[1])
    run(c.get("/x"))
    assert seen["cookie"] == "token=abc123"
    assert "authorization" not in seen


def test_token_from_set_cookie_is_stored(monkeypatch):
    c = make_client(monkeypatch, lambda r: httpx.Response(
        200, json={"id": "1"}, headers={"set-cookie": "token=jwt-from-server; HttpOnly; Path=/"}))
    run(c.post("/auth/login", json={"email": "a@b.c", "password": "12345678"}))
    assert auth_state.token == "jwt-from-server" and auth_state.is_authenticated


@pytest.mark.parametrize("body,expected", [
    ({"message": "Предмет уже зібрано"}, "Предмет уже зібрано"),
    ({"detail": "Not Found"}, "Not Found"),
    ({}, "Сталася помилка"),
])
def test_error_message_is_extracted(monkeypatch, body, expected):
    c = make_client(monkeypatch, lambda r: httpx.Response(409, json=body))
    with pytest.raises(ApiError) as e:
        run(c.get("/x"))
    assert e.value.message == expected and e.value.status == 409


def test_network_failure_becomes_api_error(monkeypatch):
    def boom(request):
        raise httpx.ConnectError("refused")

    c = make_client(monkeypatch, boom)
    with pytest.raises(ApiError) as e:
        run(c.get("/x"))
    assert e.value.status is None and "сервер" in e.value.message


def test_401_for_logged_in_user_clears_session_and_calls_hook(monkeypatch):
    auth_state.set_session("old", {"name": "A"})
    called = []

    async def hook():
        called.append(1)

    c = make_client(monkeypatch, lambda r: httpx.Response(401, json={"message": "Потрібно увійти в акаунт"}))
    c.on_unauthorized = hook
    with pytest.raises(ApiError):
        run(c.get("/profile"))
    assert not auth_state.is_authenticated and called == [1]


def test_401_on_wrong_password_does_not_trigger_hook(monkeypatch):
    called = []

    async def hook():
        called.append(1)

    c = make_client(monkeypatch, lambda r: httpx.Response(401, json={"message": "Неправильний email або пароль"}))
    c.on_unauthorized = hook
    with pytest.raises(ApiError) as e:
        run(c.post("/auth/login", json={}))
    assert e.value.message == "Неправильний email або пароль" and called == []


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_helpers_use_right_http_verb(monkeypatch, method):
    seen = {}
    c = make_client(monkeypatch, lambda r: (seen.update(m=r.method), httpx.Response(200, json={}))[1])
    run(getattr(c, method)("/x"))
    assert seen["m"] == method.upper()
