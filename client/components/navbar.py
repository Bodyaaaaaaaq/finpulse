"""Навігація: NavigationBar (мобільний) та NavigationRail (десктоп)."""
from dataclasses import dataclass
from typing import Optional

import flet as ft


@dataclass(frozen=True)
class NavItem:
    route: str
    label: str
    icon: ft.IconData
    selected_icon: ft.IconData


HOME = NavItem("/", "Головна", ft.Icons.HOME_OUTLINED, ft.Icons.HOME)
CONVERTER = NavItem("/converter", "Конвертер", ft.Icons.CURRENCY_EXCHANGE, ft.Icons.CURRENCY_EXCHANGE)
NEWS = NavItem("/news", "Новини", ft.Icons.NEWSPAPER_OUTLINED, ft.Icons.NEWSPAPER)
CRYPTO = NavItem("/crypto", "Криптовалюти", ft.Icons.CURRENCY_BITCOIN, ft.Icons.CURRENCY_BITCOIN)
MORE = NavItem("/more", "Інше", ft.Icons.MORE_HORIZ, ft.Icons.MORE_HORIZ)
GAME = NavItem("/game", "Гра", ft.Icons.MAP_OUTLINED, ft.Icons.MAP)
SHOP = NavItem("/shop", "Магазин", ft.Icons.STOREFRONT_OUTLINED, ft.Icons.STOREFRONT)
REWARDS = NavItem("/shop/my-rewards", "Мої призи", ft.Icons.CARD_GIFTCARD_OUTLINED, ft.Icons.CARD_GIFTCARD_OUTLINED)
PROFILE = NavItem("/profile", "Профіль", ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON)

# Нижня панель на мобільному — 5 вкладок, як у макеті.
MOBILE_TABS = [HOME, CONVERTER, NEWS, CRYPTO, MORE]
# Маршрути, які на мобільному підсвічують вкладку «Інше».
MORE_ROUTES = {"/more", "/game", "/shop", "/shop/my-rewards", "/profile"}
# Бічна панель на десктопі — всі розділи одразу.
DESKTOP_ITEMS = [HOME, CONVERTER, NEWS, CRYPTO, GAME, SHOP, REWARDS, PROFILE]


def mobile_index(route: str) -> int:
    if route in MORE_ROUTES:
        return MOBILE_TABS.index(MORE)
    for i, item in enumerate(MOBILE_TABS):
        if item.route == route:
            return i
    return 0


def desktop_index(route: str) -> Optional[int]:
    for i, item in enumerate(DESKTOP_ITEMS):
        if item.route == route:
            return i
    return None


def build_navigation_bar(ctx, route: str) -> ft.NavigationBar:
    async def on_change(e: ft.Event[ft.NavigationBar]) -> None:
        await ctx.go(MOBILE_TABS[e.control.selected_index].route)

    return ft.NavigationBar(
        selected_index=mobile_index(route),
        on_change=on_change,
        destinations=[
            ft.NavigationBarDestination(icon=i.icon, selected_icon=i.selected_icon, label=i.label)
            for i in MOBILE_TABS
        ],
    )


def build_navigation_rail(ctx, route: str) -> ft.NavigationRail:
    async def on_change(e: ft.Event[ft.NavigationRail]) -> None:
        await ctx.go(DESKTOP_ITEMS[e.control.selected_index].route)

    async def on_logout(e: ft.Event[ft.IconButton]) -> None:
        await ctx.logout()

    return ft.NavigationRail(
        selected_index=desktop_index(route),
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=90,
        on_change=on_change,
        destinations=[
            ft.NavigationRailDestination(icon=i.icon, selected_icon=i.selected_icon, label=i.label)
            for i in DESKTOP_ITEMS
        ],
        trailing=ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Вийти", on_click=on_logout),
    )
