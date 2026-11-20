from datetime import datetime, timezone

import pytest

from services import rates_service as rs
from services.api_client import ApiError
from tests.helpers import run

CURRENCY_JSON = [
    {"code": "USD", "name": "Долар США", "rate": 44.6648, "previousRate": 44.5, "changePercent": 0.37,
     "updatedAt": "2026-11-16T09:40:00Z"},
    {"code": "EUR", "name": "Євро", "rate": 51.2372, "previousRate": None, "changePercent": None,
     "updatedAt": "2026-11-16T09:40:00Z"},
]
CRYPTO_JSON = [
    {"symbol": "BTC", "name": "Bitcoin", "rank": 1, "priceUsd": 81277.08, "change24h": 1.8,
     "updatedAt": "2026-11-16T09:40:00Z"},
    {"symbol": "ETH", "name": "Ethereum", "rank": 2, "priceUsd": 2636.52, "change24h": -0.6,
     "updatedAt": "2026-11-16T09:41:00Z"},
]
METALS_JSON = [
    {"metal": "gold", "name": "Золото", "pricePerGramUsd": 4378.78, "previousPricePerGramUsd": 4300.0,
     "changePercent": 1.83, "updatedAt": "2026-11-16T09:40:00Z"},
]


class FakeApi:
    def __init__(self, data=None, error=None):
        self.data, self.error, self.calls = data or {}, error, []

    async def get(self, path, **kw):
        self.calls.append((path, kw.get("params")))
        if self.error:
            raise self.error
        return self.data[path]


def api():
    return FakeApi({"/currency": CURRENCY_JSON, "/crypto": CRYPTO_JSON, "/metals": METALS_JSON})


def test_fetch_currency_parses_camel_case():
    usd, eur = run(rs.fetch_currency(api()))
    assert (usd.kind, usd.code, usd.title, usd.name, usd.value, usd.unit) == \
        ("currency", "USD", "USD", "Долар США", 44.6648, "₴")
    assert usd.change == 0.37 and eur.change is None
    assert usd.key == "currency:USD"
    assert usd.updated_at == datetime(2026, 11, 16, 9, 40, tzinfo=timezone.utc)


def test_fetch_crypto_passes_limit_and_search():
    client = api()
    btc, eth = run(rs.fetch_crypto(client=client))
    assert client.calls == [("/crypto", {"limit": 30})]
    assert (btc.title, btc.value, btc.unit, btc.change) == ("BTC", 81277.08, "$", 1.8)
    assert eth.change == -0.6
    run(rs.fetch_crypto("  bit ", limit=5, client=client))
    assert client.calls[-1] == ("/crypto", {"limit": 5, "search": "bit"})


def test_fetch_metals_title_is_capitalized_code():
    (gold,) = run(rs.fetch_metals(api()))
    assert gold.code == "gold"


def test_fetch_metals_normalizes_server_uppercase_code():
    # реальний сервер повертає "GOLD"; ключ має збігатися з типовим вибором головної (metal:gold)
    row = dict(METALS_JSON[0], metal="GOLD")
    (gold,) = run(rs.fetch_metals(FakeApi({"/metals": [row]})))
    assert (gold.code, gold.key, gold.title) == ("gold", "metal:gold", "Gold")
    from state.home_state import DEFAULT_SELECTED
    assert gold.key in DEFAULT_SELECTED
    assert (gold.key, gold.title, gold.name, gold.value, gold.unit) == \
        ("metal:gold", "Gold", "Золото", 4378.78, "$")


def test_fetch_propagates_api_error():
    with pytest.raises(ApiError):
        run(rs.fetch_metals(FakeApi(error=ApiError("Не вдалося звʼязатися із сервером"))))


def item(kind, value, unit="$", change=None):
    return rs.RateItem(kind, "X", "X", "x", value, unit, change)


@pytest.mark.parametrize("it, expected", [
    (item("currency", 44.6648, "₴"), "44,6648₴"),
    (item("currency", 51.2372, "₴"), "51,2372₴"),
    (item("crypto", 81277.08), "81 277,08$"),
    (item("crypto", 2636.52), "2 636,52$"),
    (item("crypto", 1.0), "1,00$"),
    (item("crypto", 0.1234), "0,1234$"),
    (item("crypto", 0.00001234), "0,000012$"),
    (item("metal", 4378.78), "4 378,78$"),
])
def test_format_value_matches_design(it, expected):
    assert rs.format_value(it) == expected


@pytest.mark.parametrize("change, expected", [
    (1.8, "▲ 1,8%"), (-0.6, "▼ 0,6%"), (0.0, "▲ 0,0%"), (12.34, "▲ 12,3%"), (None, ""),
])
def test_format_change(change, expected):
    assert rs.format_change(change) == expected


def test_format_time_and_latest_update():
    early = datetime(2026, 11, 16, 9, 40, tzinfo=timezone.utc)
    late = datetime(2026, 11, 16, 9, 41, tzinfo=timezone.utc)
    assert rs.format_time(late) == late.astimezone().strftime("%H:%M")
    assert rs.format_time(None) == ""
    items = [rs.RateItem("c", "A", "A", "a", 1, "$", None, early),
             rs.RateItem("c", "B", "B", "b", 1, "$", None, late),
             rs.RateItem("c", "C", "C", "c", 1, "$", None, None)]
    assert rs.latest_update(items) == late
    assert rs.latest_update([]) is None


def test_parse_time_rejects_garbage():
    assert rs.parse_time("не дата") is None and rs.parse_time(None) is None
