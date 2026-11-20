"""Рядки курсів для головної й сторінки криптовалют (макет Figma)."""
import flet as ft

from components.card import Card
from services.rates_service import RateItem, format_change, format_value
from theme import MUTED, NEGATIVE, POSITIVE

# Кольори кіл-логотипів із макета; для невідомих кодів береться колір із палітри за кодом.
LOGO_COLORS = {
    "USD": "#2F4A9A", "EUR": "#2F4A9A", "GBP": "#7A2E4A", "PLN": "#C0343F",
    "BTC": "#F7931A", "ETH": "#1A1A1A", "SOL": "#7C4DDB", "USDT": "#26A17B",
    "BNB": "#E5B31B", "XRP": "#2B4A7F",
    "GOLD": "#D9A520", "SILVER": "#9AA3B0", "PLATINUM": "#6F8FAF", "PALLADIUM": "#8A7A99",
}
PALETTE = ["#2F4A9A", "#7A2E4A", "#C0343F", "#7C4DDB", "#26A17B", "#E5B31B", "#2B4A7F", "#D9A520"]


def logo_color(code: str) -> str:
    key = code.upper()
    return LOGO_COLORS.get(key, PALETTE[sum(map(ord, key)) % len(PALETTE)])


def logo(code: str, size: int = 44) -> ft.Control:
    """Кольорове коло з першою літерою коду (замість зображення логотипа)."""
    return ft.Container(
        ft.Text(code[:1].upper(), size=size * 0.45, weight=ft.FontWeight.W_700, color="white"),
        width=size, height=size, shape=ft.BoxShape.CIRCLE, bgcolor=logo_color(code),
        alignment=ft.Alignment.CENTER,
    )


def change_text(change, size: int = 14) -> ft.Control:
    """Стрілка й колір: зелений ▲ — зростання, червоний ▼ — падіння; без даних — порожньо."""
    label = format_change(change)
    color = NEGATIVE if (change is not None and change < 0) else POSITIVE
    return ft.Text(label, size=size, weight=ft.FontWeight.W_600, color=color, visible=bool(label))


def price_column(item: RateItem, value_size: int) -> ft.Control:
    return ft.Column(
        [ft.Text(format_value(item), size=value_size, weight=ft.FontWeight.W_600), change_text(item.change)],
        spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END, tight=True,
    )


def home_row(item: RateItem) -> ft.Control:
    """Рядок головної: логотип, код, курс (+ зміна)."""
    return Card(
        ft.Row(
            [logo(item.title, 52), ft.Text(item.title, size=24, weight=ft.FontWeight.W_600),
             ft.Container(expand=True), price_column(item, 22)],
            spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=12,
    )


def crypto_row(item: RateItem) -> ft.Control:
    """Рядок сторінки «Криптовалюти»: символ + назва ліворуч, ціна й зміна за 24 год праворуч."""
    return Card(
        ft.Row(
            [
                logo(item.title, 44),
                ft.Column(
                    [ft.Text(item.title, size=20, weight=ft.FontWeight.W_600),
                     ft.Text(item.name, size=14, weight=ft.FontWeight.W_600, color=MUTED)],
                    spacing=0, tight=True,
                ),
                ft.Container(expand=True),
                price_column(item, 20),
            ],
            spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=12,
    )


def edit_row(item: RateItem, selected: bool, on_change) -> ft.Control:
    """Рядок режиму «Редагувати»: логотип, код, назва й перемикач."""
    return Card(
        ft.Row(
            [
                logo(item.title, 28),
                ft.Text(item.title, size=17, weight=ft.FontWeight.W_600),
                ft.Text(item.name, size=13, weight=ft.FontWeight.W_600, color=MUTED, expand=True,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Switch(value=selected, active_color=POSITIVE, on_change=on_change),
            ],
            spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=8,
    )
