import asyncio

from services import auth_service
from services.api_client import ApiError


def run(coro):
    return asyncio.run(coro)


class FakeApi:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []

    async def post(self, path, **kw):
        self.calls.append((path, kw.get("json")))
        if self.error:
            raise self.error
        return self.result


class FakeCtx:
    def __init__(self):
        self.users = []

    async def login(self, user):
        self.users.append(user)


USER = {"id": "1", "name": "Іван", "email": "i@x.ua", "points": 0}


def test_login_normalizes_email_and_keeps_password_as_is():
    api = FakeApi(USER)
    run(auth_service.login("  Ivan@X.UA ", " pass ", api))
    assert api.calls == [("/auth/login", {"email": "ivan@x.ua", "password": " pass "})]


def test_register_payload_and_address():
    api = FakeApi(USER)
    run(auth_service.register(" Іван ", "I@X.ua", "12345678", " Львів ", api))
    assert api.calls == [("/auth/register", {"email": "i@x.ua", "name": "Іван", "password": "12345678",
                                              "address": "Львів"})]


def test_register_without_address_omits_it():
    api = FakeApi(USER)
    run(auth_service.register("Іван", "i@x.ua", "12345678", None, api))
    assert "address" not in api.calls[0][1]


def test_submit_login_success_calls_ctx_login():
    ctx, api = FakeCtx(), FakeApi(USER)
    assert run(auth_service.submit_login(ctx, "i@x.ua", "secret123", api)) is None
    assert ctx.users == [USER]


def test_submit_login_validation_error_makes_no_request():
    ctx, api = FakeCtx(), FakeApi(USER)
    assert run(auth_service.submit_login(ctx, "bad", "x", api)) == "Некоректний email"
    assert api.calls == [] and ctx.users == []


def test_submit_login_returns_server_message():
    ctx, api = FakeCtx(), FakeApi(error=ApiError("Неправильний email або пароль", 401))
    assert run(auth_service.submit_login(ctx, "i@x.ua", "wrong", api)) == "Неправильний email або пароль"
    assert ctx.users == []


def test_submit_login_returns_rate_limit_message():
    ctx, api = FakeCtx(), FakeApi(error=ApiError("Забагато спроб входу. Спробуйте через 15 хв", 429))
    assert "Забагато спроб" in run(auth_service.submit_login(ctx, "i@x.ua", "x", api))


def test_submit_register_success():
    ctx, api = FakeCtx(), FakeApi(USER)
    assert run(auth_service.submit_register(ctx, "Іван", "i@x.ua", "12345678", "12345678", "Львів", api)) is None
    assert ctx.users == [USER]


def test_submit_register_password_mismatch_makes_no_request():
    ctx, api = FakeCtx(), FakeApi(USER)
    msg = run(auth_service.submit_register(ctx, "Іван", "i@x.ua", "12345678", "1234567x", "Львів", api))
    assert msg == "Паролі не збігаються" and api.calls == []


def test_submit_register_duplicate_email_message_from_server():
    ctx, api = FakeCtx(), FakeApi(error=ApiError("Користувач з таким email уже існує", 409))
    msg = run(auth_service.submit_register(ctx, "Іван", "i@x.ua", "12345678", "12345678", "Львів", api))
    assert msg == "Користувач з таким email уже існує" and ctx.users == []


def test_submit_register_network_error_message():
    ctx, api = FakeCtx(), FakeApi(error=ApiError("Не вдалося звʼязатися із сервером"))
    assert "сервер" in run(auth_service.submit_register(ctx, "Іван", "i@x.ua", "12345678", "12345678", None, api))
