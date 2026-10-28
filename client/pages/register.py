import flet as ft

from components.card import Card
from components.header import Header
from theme import MUTED


def build(ctx) -> ft.Control:
    async def to_login(e: ft.Event[ft.TextButton]) -> None:
        await ctx.go("/login")

    return ft.Column(
        [
            Header("Реєстрація"),
            Card(ft.Text(
                "Форму реєстрації (імʼя, email, адреса, пароль, повтор пароля) буде реалізовано в задачі FE-3",
                color=MUTED,
            )),
            ft.TextButton(content="Вже є акаунт? Увійти", on_click=to_login),
        ],
        spacing=12,
    )
