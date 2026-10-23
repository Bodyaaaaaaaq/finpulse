from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_unknown_route_returns_message():
    # ТЗ 5.1: будь-яка помилка має вигляд { "message": "..." }
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "message" in response.json()
