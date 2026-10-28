"""Тести BE-3: профіль, зміна пароля, видалення акаунта (ТЗ 5.2)."""
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.conversion_history import AssetType, ConversionHistory
from app.models.game_item import GameItem, GameItemStatus
from app.models.user import User

USER = {"email": "ivan@gmail.com", "name": "Іван", "password": "password123"}


def logged_in_client(**changes) -> TestClient:
    """Новий клієнт, який щойно зареєструвався (cookie з токеном уже є)."""
    client = TestClient(app)
    response = client.post("/api/auth/register", json={**USER, **changes})
    assert response.status_code == 201
    return client


def login(email: str, password: str):
    return TestClient(app).post("/api/auth/login", json={"email": email, "password": password})


def delete_account(client: TestClient, password: str):
    # httpx не дозволяє передати json у client.delete(), тому через request()
    return client.request("DELETE", "/api/profile", json={"password": password})


# --- Без входу ---

def test_profile_requires_login():
    client = TestClient(app)
    assert client.patch("/api/profile", json={"name": "Петро"}).status_code == 401
    assert client.patch("/api/profile/password", json={"oldPassword": "a", "newPassword": "b" * 8}).status_code == 401
    assert delete_account(client, "password123").status_code == 401


# --- PATCH /profile ---

def test_change_name():
    client = logged_in_client()
    response = client.patch("/api/profile", json={"name": "  Петро  "})

    assert response.status_code == 200
    assert response.json()["name"] == "Петро"
    assert client.get("/api/auth/me").json()["name"] == "Петро"


def test_change_email_then_login_with_new_email():
    client = logged_in_client()
    response = client.patch("/api/profile", json={"email": "Petro@Gmail.com"})

    assert response.status_code == 200
    assert response.json()["email"] == "petro@gmail.com"
    assert login("petro@gmail.com", "password123").status_code == 200
    assert login("ivan@gmail.com", "password123").status_code == 401


def test_change_email_to_taken_returns_409():
    logged_in_client(email="taken@gmail.com")
    client = logged_in_client()
    response = client.patch("/api/profile", json={"email": "TAKEN@gmail.com"})

    assert response.status_code == 409
    assert response.json() == {"message": "Користувач з таким email уже існує"}


def test_set_same_email_is_not_conflict():
    client = logged_in_client()
    assert client.patch("/api/profile", json={"email": "IVAN@gmail.com"}).status_code == 200


def test_empty_update_returns_400():
    client = logged_in_client()
    response = client.patch("/api/profile", json={})
    assert response.status_code == 400
    assert response.json() == {"message": "Немає даних для зміни: передайте name або email"}


def test_blank_name_returns_400():
    client = logged_in_client()
    response = client.patch("/api/profile", json={"name": "   "})
    assert response.status_code == 400
    assert response.json() == {"message": "Ім'я не може бути порожнім"}


# --- PATCH /profile/password ---

def test_change_password():
    client = logged_in_client()
    response = client.patch("/api/profile/password", json={"oldPassword": "password123", "newPassword": "newpass456"})

    assert response.status_code == 200
    assert login("ivan@gmail.com", "newpass456").status_code == 200
    assert login("ivan@gmail.com", "password123").status_code == 401


def test_change_password_with_wrong_old_password_returns_400():
    client = logged_in_client()
    response = client.patch("/api/profile/password", json={"oldPassword": "wrong-pass", "newPassword": "newpass456"})

    assert response.status_code == 400
    assert response.json() == {"message": "Неправильний поточний пароль"}
    assert login("ivan@gmail.com", "password123").status_code == 200


def test_new_password_too_short_returns_400():
    client = logged_in_client()
    response = client.patch("/api/profile/password", json={"oldPassword": "password123", "newPassword": "short"})
    assert response.status_code == 400
    assert response.json() == {"message": "Поле newPassword закоротке: мінімум 8 символів"}


# --- DELETE /profile ---

def test_delete_account():
    client = logged_in_client()
    response = delete_account(client, "password123")

    assert response.status_code == 200
    assert response.json() == {"message": "Акаунт видалено"}
    assert client.get("/api/auth/me").status_code == 401
    assert login("ivan@gmail.com", "password123").status_code == 401


def test_delete_account_with_wrong_password_returns_400():
    client = logged_in_client()
    response = delete_account(client, "wrong-pass")

    assert response.status_code == 400
    assert response.json() == {"message": "Неправильний пароль"}
    assert client.get("/api/auth/me").status_code == 200


def test_delete_account_cleans_related_data():
    """Історія конвертацій видаляється, а зібраний предмет гри лишається без власника."""
    client = logged_in_client()
    with SessionLocal() as db:
        user_id = db.query(User.id).filter(User.email == "ivan@gmail.com").scalar()
        db.add(ConversionHistory(
            user_id=user_id, from_type=AssetType.CURRENCY, to_type=AssetType.CURRENCY,
            from_code="USD", to_code="UAH", amount_from=Decimal("10"), amount_to=Decimal("415"),
        ))
        item_id = uuid.uuid4()
        db.add(GameItem(
            id=item_id, latitude=Decimal("49.84"), longitude=Decimal("24.03"), points=10,
            status=GameItemStatus.COLLECTED, collected_by_user_id=user_id,
        ))
        db.commit()

    assert delete_account(client, "password123").status_code == 200

    with SessionLocal() as db:
        assert db.query(ConversionHistory).count() == 0
        item = db.get(GameItem, item_id)
        assert item is not None
        assert item.collected_by_user_id is None
