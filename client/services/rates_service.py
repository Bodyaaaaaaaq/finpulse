"""Курси валют, криптовалют і металів (FE-5, сервер — BE-4). Адреси публічні: токен не потрібен."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from services.api_client import ApiClient, api as default_api

CURRENCY = "currency"
CRYPTO = "crypto"
METAL = "metal"


@dataclass(frozen=True)
class RateItem:
    kind: str                       # CURRENCY | CRYPTO | METAL
    code: str                       # USD, BTC, gold — ідентифікатор в межах kind
    title: str                      # що показуємо великим: USD, BTC, Gold
    name: str                       # Долар США, Bitcoin, Золото
    value: float
    unit: str                       # "₴" або "$"
    change: Optional[float] = None  # зміна, %: >0 зростання, <0 падіння, None — невідомо
    updated_at: Optional[datetime] = None

    @property
    def key(self) -> str:
        """Ключ для збереження вибору на головній: 'currency:USD'."""
        return f"{self.kind}:{self.code}"


def parse_time(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _currency(row: dict) -> RateItem:
    return RateItem(CURRENCY, row["code"], row["code"], row["name"], float(row["rate"]), "₴",
                    row.get("changePercent"), parse_time(row.get("updatedAt")))


def _crypto(row: dict) -> RateItem:
    return RateItem(CRYPTO, row["symbol"], row["symbol"], row["name"], float(row["priceUsd"]), "$",
                    row.get("change24h"), parse_time(row.get("updatedAt")))


def _metal(row: dict) -> RateItem:
    # Сервер віддає код металу великими літерами (GOLD) — нормалізуємо, щоб ключ збігався з вибором на головній
    code = str(row["metal"]).lower()
    return RateItem(METAL, code, code.capitalize(), row["name"],
                    float(row["pricePerGramUsd"]), "$", row.get("changePercent"),
                    parse_time(row.get("updatedAt")))


async def fetch_currency(client: ApiClient = default_api) -> list[RateItem]:
    return [_currency(r) for r in await client.get("/currency")]


async def fetch_crypto(search: Optional[str] = None, limit: int = 30,
                       client: ApiClient = default_api) -> list[RateItem]:
    params: dict = {"limit": limit}
    if search and search.strip():
        params["search"] = search.strip()
    return [_crypto(r) for r in await client.get("/crypto", params=params)]


async def fetch_metals(client: ApiClient = default_api) -> list[RateItem]:
    return [_metal(r) for r in await client.get("/metals")]


# ---------- відображення ----------
def _group(number: float, decimals: int) -> str:
    """81277.08 -> '81 277,08' (пробіл між тисячами, кома як десятковий роздільник, як у макеті)."""
    return f"{number:,.{decimals}f}".replace(",", " ").replace(".", ",")


def format_value(item: RateItem) -> str:
    if item.kind == CURRENCY:
        decimals = 4
    elif item.value >= 1:
        decimals = 2
    else:  # дрібні монети: 0,00001234 не можна округлювати до 0,00
        decimals = 4 if item.value >= 0.01 else 6
    return f"{_group(item.value, decimals)}{item.unit}"


def format_change(change: Optional[float]) -> str:
    """'▲ 1,8%' / '▼ 0,6%'; порожній рядок, якщо зміна невідома."""
    if change is None:
        return ""
    arrow = "▼" if change < 0 else "▲"
    return f"{arrow} {_group(abs(change), 1)}%"


def format_time(moment: Optional[datetime]) -> str:
    """Година:хвилина у місцевому часі комп'ютера, де запущено клієнт."""
    if moment is None:
        return ""
    if moment.tzinfo is not None:
        moment = moment.astimezone()
    return moment.strftime("%H:%M")


def latest_update(items: list[RateItem]) -> Optional[datetime]:
    times = [i.updated_at for i in items if i.updated_at is not None]
    return max(times) if times else None
