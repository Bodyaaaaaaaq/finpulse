"""Роутінг клієнта: таблиця маршрутів, захист приватних сторінок, 404, адаптивна навігація."""
from dataclasses import dataclass
from typing import Callable, Optional

import flet as ft

from components.navbar import build_navigation_bar, build_navigation_rail
from config import WIDE_BREAKPOINT
from pages import (converter, crypto, game, home, login, more, my_rewards, news,
                   not_found, profile, register, shop)
from state.auth_state import auth_state
from theme import BG


@dataclass(frozen=True)
class RouteDef:
    path: str
    build: Callable[..., ft.Control]
    public: bool = False  # True — сторінка доступна лише НЕ залогіненим (вхід/реєстрація)


ROUTES: dict[str, RouteDef] = {r.path: r for r in [
    RouteDef("/login", login.build, public=True),
    RouteDef("/register", register.build, public=True),
    RouteDef("/", home.build),
    RouteDef("/converter", converter.build),
    RouteDef("/news", news.build),
    RouteDef("/crypto", crypto.build),
    RouteDef("/more", more.build),
    RouteDef("/game", game.build),
    RouteDef("/shop", shop.build),
    RouteDef("/shop/my-rewards", my_rewards.build),
    RouteDef("/profile", profile.build),
]}
NOT_FOUND = RouteDef("*", not_found.build)

# Курси валют і металів тепер на головній (вибір що показувати — кнопка «Редагувати»).
REDIRECTS = {"/currency": "/", "/metals": "/"}


def normalize(route: Optional[str]) -> str:
    """'/news/?a=1#x' -> '/news'; '' -> '/'."""
    path = (route or "/").split("?")[0].split("#")[0]
    if len(path) > 1:
        path = path.rstrip("/")
    return path or "/"


class Router:
    """Також виступає контекстом `ctx` для сторінок: ctx.page, ctx.go(), ctx.logout()."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._wide: Optional[bool] = None

    # ---- допоміжне ----
    @property
    def is_wide(self) -> bool:
        return (self.page.width or 0) >= WIDE_BREAKPOINT

    async def go(self, route: str) -> None:
        await self.page.push_route(route)

    async def logout(self) -> None:
        auth_state.clear()
        await self.go("/login")

    def redirect_target(self, route: str) -> Optional[str]:
        """Куди перекинути замість показу сторінки (або None, якщо показуємо як є)."""
        if route in REDIRECTS:
            return REDIRECTS[route]
        definition = ROUTES.get(route)
        if definition is None:
            return None  # невідомий маршрут -> 404 для всіх
        if definition.public and auth_state.is_authenticated:
            return "/"
        if not definition.public and not auth_state.is_authenticated:
            return "/login"
        return None

    # ---- події Flet ----
    async def on_route_change(self, e: Optional[ft.RouteChangeEvent] = None) -> None:
        raw = self.page.route
        route = normalize(raw)
        target = self.redirect_target(route)
        if target is not None and target != raw:
            await self.page.push_route(target)
            return
        self.render(route)

    async def on_resize(self, e: Optional[ft.PageResizeEvent] = None) -> None:
        if self._wide is not None and self._wide != self.is_wide:
            self.render(normalize(self.page.route))

    async def on_view_pop(self, e: ft.ViewPopEvent) -> None:
        await self.go("/")

    # ---- побудова вигляду ----
    def render(self, route: str) -> None:
        definition = ROUTES.get(route, NOT_FOUND)
        content = definition.build(self)
        self._wide = self.is_wide
        self.page.views.clear()
        self.page.views.append(self.build_view(route, definition, content))
        self.page.update()

    def build_view(self, route: str, definition: RouteDef, content: ft.Control) -> ft.View:
        body = ft.Column([content], scroll=ft.ScrollMode.AUTO, expand=True)
        padded = ft.Container(body, padding=ft.Padding(left=19, top=24, right=19, bottom=12), expand=True)

        # Вхід, реєстрація і 404 — без навігації (як у макеті).
        if definition.public or definition is NOT_FOUND:
            return ft.View(route=self.page.route, bgcolor=BG, padding=0,
                           controls=[ft.SafeArea(content=padded, expand=True)])

        if self.is_wide:
            layout = ft.Row(
                [build_navigation_rail(self, route), ft.VerticalDivider(width=1), padded],
                expand=True,
            )
            return ft.View(route=self.page.route, bgcolor=BG, padding=0,
                           controls=[ft.SafeArea(content=layout, expand=True)])

        return ft.View(route=self.page.route, bgcolor=BG, padding=0,
                       controls=[ft.SafeArea(content=padded, expand=True)],
                       navigation_bar=build_navigation_bar(self, route))
