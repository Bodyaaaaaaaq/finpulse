"""Блок користувача й балансу балів (FE-2)."""
import flet as ft

from components.card import Card
from state.auth_state import auth_state
from theme import MUTED, PRIMARY


def format_points(points: int) -> str:
    """1500 -> '1 500'."""
    return f"{points:,}".replace(",", " ")


def balance_card() -> ft.Control:
    """Картка «Ваш баланс» для сторінки «Інше» (мобільний)."""
    return Card(
        ft.Row(
            [
                ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, color=PRIMARY, size=32),
                ft.Column(
                    [
                        ft.Text(auth_state.name or "Користувач", weight=ft.FontWeight.W_600),
                        ft.Text("Ваш баланс", size=12, color=MUTED),
                    ],
                    spacing=0,
                    expand=True,
                ),
                ft.Text(f"{format_points(auth_state.points)} балів", size=20,
                        weight=ft.FontWeight.W_800, color=PRIMARY),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


def rail_header() -> ft.Control:
    """Шапка бічної панелі (десктоп): ім'я та бали."""
    return ft.Container(
        ft.Column(
            [
                ft.Text("FinPulse", size=18, weight=ft.FontWeight.W_800, color=PRIMARY),
                ft.Text(auth_state.name or "Користувач", size=12, weight=ft.FontWeight.W_600,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{format_points(auth_state.points)} балів", size=12, color=MUTED),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=4, top=12, right=4, bottom=8),
        width=90,
    )
