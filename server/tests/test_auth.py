"""Тести BE-2: реєстрація, вхід, вихід, /auth/me (ТЗ 5.2, розділ 8)."""
from fastapi.testclient import TestClient

from app.main import app

USER = {"email": "Ivan@Gmail.com", "name": "Іван", "password": "password123"}


def new_client() -> TestClient:
    # Кожен тест - новий "браузер" без cookie
    return TestClient(app)


def register(client: TestClient, **changes):
    return client.post("/api/auth/register", json={**USER, **changes})


# --- Реєстрація ---

def test_register_returns_user_and_sets_cookie():
    client = new_client()
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ivan@gmail.com"  # збережено в нижньому регістрі
    assert body["name"] == "Іван"
    assert body["points"] == 0
    assert "createdAt" in body and "id" in body
    assert "password" not in body and "password_hash" not in body
    assert "token" in response.cookies


def test_register_same_email_returns_409():
    client = new_client()
    register(client)
    response = register(client, email="IVAN@gmail.com")  # той самий email, інший регістр

    assert response.status_code == 409
    assert response.json() == {"message": "Користувач з таким email уже існує"}


def test_register_short_password_returns_400():
    response = register(new_client(), password="1234567")
    assert response.status_code == 400
    assert response.json() == {"message": "Поле password закоротке: мінімум 8 символів"}


def test_register_bad_email_returns_400():
    response = register(new_client(), email="not-an-email")
    assert response.status_code == 400
    assert response.json() == {"message": "Неправильний email"}


def test_register_missing_name_returns_400():
    response = new_client().post("/api/auth/register", json={"email": "a@b.com", "password": "password123"})
    assert response.status_code == 400
    assert response.json() == {"message": "Не заповнено поле name"}


def test_register_too_long_password_returns_400():
    response = register(new_client(), password="я" * 40)  # 40 кириличних літер = 80 байтів
    assert response.status_code == 400
    assert response.json() == {"message": "Пароль задовгий"}


def test_broken_json_returns_400():
    response = new_client().post(
        "/api/auth/login", content="{oops", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Неправильний формат JSON"}


# --- Вхід ---

def test_login_with_correct_password():
    register(new_client())
    client = new_client()
    response = client.post("/api/auth/login", json={"email": "IVAN@gmail.com", "password": "password123"})

    assert response.status_code == 200
    assert response.json()["email"] == "ivan@gmail.com"
    assert "token" in response.cookies


def test_login_wrong_password_returns_401():
    register(new_client())
    response = new_client().post("/api/auth/login", json={"email": USER["email"], "password": "wrong-pass"})

    assert response.status_code == 401
    assert response.json() == {"message": "Неправильний email або пароль"}


def test_login_unknown_email_returns_same_401():
    response = new_client().post("/api/auth/login", json={"email": "nobody@gmail.com", "password": "whatever1"})
    assert response.status_code == 401
    assert response.json() == {"message": "Неправильний email або пароль"}


def test_sixth_failed_login_returns_429_even_with_correct_password():
    register(new_client())
    client = new_client()
    for _ in range(5):
        response = client.post("/api/auth/login", json={"email": USER["email"], "password": "wrong-pass"})
        assert response.status_code == 401

    response = client.post("/api/auth/login", json={"email": USER["email"], "password": "password123"})
    assert response.status_code == 429
    assert "Забагато спроб" in response.json()["message"]


def test_successful_login_resets_failed_attempts():
    register(new_client())
    client = new_client()
    for _ in range(4):
        client.post("/api/auth/login", json={"email": USER["email"], "password": "wrong-pass"})
    assert client.post("/api/auth/login", json={"email": USER["email"], "password": "password123"}).status_code == 200

    for _ in range(4):
        client.post("/api/auth/login", json={"email": USER["email"], "password": "wrong-pass"})
    assert client.post("/api/auth/login", json={"email": USER["email"], "password": "password123"}).status_code == 200


# --- /auth/me і вихід ---

def test_me_after_register():
    client = new_client()
    register(client)
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "ivan@gmail.com"


def test_me_without_login_returns_401():
    response = new_client().get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"message": "Потрібно увійти в акаунт"}


def test_me_with_fake_token_returns_401():
    client = new_client()
    client.cookies.set("token", "fake.token.value")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_removes_access():
    client = new_client()
    register(client)
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
