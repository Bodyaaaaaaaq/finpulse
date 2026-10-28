"""Тести BE-4: GET /currency, /crypto, /metals (ТЗ 5.2, 5.3)."""
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.crypto_rate import CryptoRate
from app.models.currency_rate import CurrencyRate
from app.models.metal_rate import MetalRate, MetalType

client = TestClient(app)  # без входу: курси - публічні дані (ТЗ 5.1)
NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


@pytest.fixture
def rates():
    with SessionLocal() as db:
        db.add_all([
            CurrencyRate(code="CHF", name="Швейцарський франк", rate=Decimal("47.1"), updated_at=NOW),
            CurrencyRate(code="EUR", name="Євро", rate=Decimal("45.00"), previous_rate=Decimal("45.90"),
                         updated_at=NOW),
            CurrencyRate(code="USD", name="Долар США", rate=Decimal("41.50"), previous_rate=Decimal("41.00"),
                         updated_at=NOW),
            CurrencyRate(code="AUD", name="Австралійський долар", rate=Decimal("27.3"), updated_at=NOW),
            CryptoRate(coin_id="ethereum", symbol="ETH", name="Ethereum", rank=2, price_usd=Decimal("3200.5"),
                       change_24h=Decimal("-0.7"), updated_at=NOW),
            CryptoRate(coin_id="bitcoin", symbol="BTC", name="Bitcoin", rank=1, price_usd=Decimal("64230.12"),
                       change_24h=Decimal("1.8"), updated_at=NOW),
            CryptoRate(coin_id="new-coin", symbol="NEW", name="New Coin", rank=None, price_usd=Decimal("0.01"),
                       change_24h=None, updated_at=NOW),
            MetalRate(metal=MetalType.SILVER, price_per_gram_usd=Decimal("1.55"), updated_at=NOW),
            MetalRate(metal=MetalType.GOLD, price_per_gram_usd=Decimal("130"),
                      previous_price_per_gram_usd=Decimal("128"), updated_at=NOW),
        ])
        db.commit()


# --- /currency ---

def test_currency_is_public_and_empty_without_data():
    response = client.get("/api/currency")
    assert response.status_code == 200
    assert response.json() == []


def test_currency_format_and_order(rates):
    body = client.get("/api/currency").json()

    # Спочатку популярні (USD, EUR), потім решта за абеткою
    assert [row["code"] for row in body] == ["USD", "EUR", "AUD", "CHF"]
    usd = body[0]
    assert usd["name"] == "Долар США"
    assert usd["rate"] == 41.5  # число, а не рядок
    assert usd["previousRate"] == 41.0
    assert usd["changePercent"] == 1.22  # (41.5 - 41) / 41 * 100
    assert "updatedAt" in usd


def test_currency_change_is_negative_or_missing(rates):
    body = {row["code"]: row for row in client.get("/api/currency").json()}
    assert body["EUR"]["changePercent"] == -1.96
    assert body["CHF"]["changePercent"] is None
    assert body["CHF"]["previousRate"] is None


# --- /crypto ---

def test_crypto_format_and_order_by_rank(rates):
    body = client.get("/api/crypto").json()

    assert [row["symbol"] for row in body] == ["BTC", "ETH", "NEW"]  # без рейтингу - в кінці
    assert body[0] == {
        "symbol": "BTC", "name": "Bitcoin", "rank": 1, "priceUsd": 64230.12, "change24h": 1.8,
        "updatedAt": body[0]["updatedAt"],
    }


def test_crypto_limit(rates):
    assert [row["symbol"] for row in client.get("/api/crypto?limit=1").json()] == ["BTC"]


@pytest.mark.parametrize("limit", ["0", "101"])
def test_crypto_limit_out_of_range_returns_400(limit):
    response = client.get(f"/api/crypto?limit={limit}")
    assert response.status_code == 400
    assert response.json()["message"].startswith("Поле limit")


def test_crypto_limit_not_a_number_returns_400():
    response = client.get("/api/crypto?limit=abc")
    assert response.status_code == 400
    assert response.json() == {"message": "Поле limit має бути цілим числом"}


def test_crypto_search_by_symbol_or_name(rates):
    assert [row["symbol"] for row in client.get("/api/crypto?search=eth").json()] == ["ETH"]
    assert [row["symbol"] for row in client.get("/api/crypto?search=coin").json()] == ["BTC", "NEW"]


# --- /metals ---

def test_metals_format_and_order(rates):
    body = client.get("/api/metals").json()

    assert [row["metal"] for row in body] == ["GOLD", "SILVER"]
    gold = body[0]
    assert gold["name"] == "Золото"
    assert gold["pricePerGramUsd"] == 130.0
    assert gold["previousPricePerGramUsd"] == 128.0
    assert gold["changePercent"] == 1.56
    assert body[1]["changePercent"] is None
