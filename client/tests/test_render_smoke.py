"""Дымовий тест: усі сторінки будуються в мобільному й десктопному вигляді без винятків."""
from types import SimpleNamespace

import flet as ft
import pytest

from router import ROUTES, Router
from state.auth_state import auth_state


class FakePage(SimpleNamespace):
    def update(self):
        pass


@pytest.mark.parametrize("width", [360, 390, 720, 1280])
@pytest.mark.parametrize("route", list(ROUTES) + ["/nope"])
def test_every_route_renders(route, width):
    auth_state.set_session("t", {"name": "Іван", "email": "i@x.ua", "points": 1500})
    page = FakePage(width=width, route=route, views=[])
    Router(page).render(route)
    view = page.views[0]
    assert isinstance(view, ft.View)
    private = route in ROUTES and not ROUTES[route].public
    if private:
        assert (view.navigation_bar is not None) == (width < 720)
