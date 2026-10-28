import flet as ft

from components.card import Card
from components.header import Header
from state.auth_state import auth_state
from theme import MUTED, PRIMARY


def build(ctx) -> ft.Control:
    async def fake_login(e: ft.Event[ft.Button]) -> None:
        # ТИМЧАСОВО (FE-1): імітація входу, щоб можна було переглянути захищені сторінки.
        # Справжню форму входу і запит до API робить FE-3.
        auth_state.set_session("dev-token", {"name": "Dev"})
        await ctx.go("/")

    async def to_register(e: ft.Event[ft.TextButton]) -> None:
        await ctx.go("/register")

    return ft.Column(
        [
            ft.Text("FinPulse", size=40, weight=ft.FontWeight.W_800, color=PRIMARY),
            Header("Вхід"),
            Card(ft.Text("Форму входу буде реалізовано в задачі FE-3", color=MUTED)),
            ft.Button(content="Увійти (тимчасово, для розробки)", on_click=fake_login),
            ft.TextButton(content="Немає акаунта? Зареєструватися", on_click=to_register),
        ],
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
