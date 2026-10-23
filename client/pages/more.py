import flet as ft

from components.card import Card
from components.header import Header
from theme import NEGATIVE

# (маршрут, назва, іконка) — розділи, які на мобільному ховаються під вкладку «Інше».
MENU = [
    ("/game", "Гра «Пошук на карті»", ft.Icons.SPORTS_ESPORTS_OUTLINED),
    ("/shop", "Магазин", ft.Icons.STOREFRONT_OUTLINED),
    ("/shop/my-rewards", "Мої призи", ft.Icons.CARD_GIFTCARD_OUTLINED),
    ("/profile", "Профіль", ft.Icons.PERSON_OUTLINE),
]


def build(ctx) -> ft.Control:
    def make_handler(route: str):
        async def handler(e: ft.Event[ft.ListTile]) -> None:
            await ctx.go(route)
        return handler

    async def on_logout(e: ft.Event[ft.Button]) -> None:
        await ctx.logout()

    # TODO (FE-2): блок «Ваш баланс» зверху, коли буде auth_state.user.
    items = [
        Card(
            ft.ListTile(
                leading=ft.Icon(icon),
                title=ft.Text(title, weight=ft.FontWeight.W_600),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                on_click=make_handler(route),
            ),
            padding=4,
        )
        for route, title, icon in MENU
    ]
    return ft.Column(
        [
            Header("Інше"),
            *items,
            ft.Button(content="Вийти", color=NEGATIVE, on_click=on_logout),
        ],
        spacing=12,
    )
