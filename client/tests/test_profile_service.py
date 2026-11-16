import asyncio

from services import profile_service
from services.api_client import ApiError


def run(coro):
    return asyncio.run(coro)


class FakeApi:
    def __init__(self, error=None):
        self.error, self.calls = error, []

    async def patch(self, path, **kw):
        self.calls.append(("PATCH", path, kw.get("json")))
        if self.error:
            raise self.error
        return {"message": "Пароль змінено"}

    async def request(self, method, path, **kw):
        self.calls.append((method, path, kw.get("json")))
        if self.error:
            raise self.error
        return {"message": "Акаунт видалено"}


class FakeCtx:
    def __init__(self):
        self.expired = 0

    async def session_expired(self):
        self.expired += 1


def test_change_password_uses_camel_case_fields():
    api = FakeApi()
    assert run(profile_service.submit_change_password("oldpass1", "newpass12", api)) is None
    assert api.calls == [("PATCH", "/profile/password",
                          {"oldPassword": "oldpass1", "newPassword": "newpass12"})]


def test_change_password_validation_blocks_request():
    api = FakeApi()
    assert run(profile_service.submit_change_password("", "newpass12", api)) == "Введіть поточний пароль"
    assert run(profile_service.submit_change_password("oldpass1", "short", api)).startswith("Пароль має містити")
    assert run(profile_service.submit_change_password("samepass1", "samepass1", api)) == \
        "Новий пароль має відрізнятися від поточного"
    assert api.calls == []


def test_change_password_returns_server_error():
    api = FakeApi(ApiError("Неправильний поточний пароль", 400))
    assert run(profile_service.submit_change_password("oldpass1", "newpass12", api)) == \
        "Неправильний поточний пароль"


def test_delete_account_sends_password_and_ends_session():
    api, ctx = FakeApi(), FakeCtx()
    assert run(profile_service.submit_delete_account(ctx, "secret123", api)) is None
    assert api.calls == [("DELETE", "/profile", {"password": "secret123"})]
    assert ctx.expired == 1


def test_delete_account_wrong_password_keeps_session():
    api, ctx = FakeApi(ApiError("Неправильний пароль", 400)), FakeCtx()
    assert run(profile_service.submit_delete_account(ctx, "bad", api)) == "Неправильний пароль"
    assert ctx.expired == 0


def test_delete_account_requires_password():
    api, ctx = FakeApi(), FakeCtx()
    assert run(profile_service.submit_delete_account(ctx, "", api)) == "Введіть пароль для підтвердження"
    assert api.calls == [] and ctx.expired == 0
