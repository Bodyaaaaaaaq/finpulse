import flet as ft
import pytest

from components.balance import balance_card, format_points, rail_header
from components.navbar import build_navigation_rail
from state.auth_state import auth_state


@pytest.mark.parametrize("n,expected", [(0, "0"), (150, "150"), (1500, "1 500"), (1234567, "1 234 567")])
def test_format_points(n, expected):
    assert format_points(n) == expected


def _texts(control):
    out = []

    def walk(c):
        if isinstance(c, ft.Text):
            out.append(c.value)
        for attr in ("content", "controls"):
            child = getattr(c, attr, None)
            if isinstance(child, list):
                for x in child:
                    walk(x)
            elif child is not None and not isinstance(child, str):
                walk(child)

    walk(control)
    return out


def test_balance_card_shows_name_and_points():
    auth_state.set_session("t", {"name": "Іван", "points": 1500})
    texts = _texts(balance_card())
    assert "Іван" in texts and "Ваш баланс" in texts and "1 500 балів" in texts


def test_rail_header_has_defaults_for_missing_user():
    auth_state.set_session("t")
    texts = _texts(rail_header())
    assert "Користувач" in texts and "0 балів" in texts


def test_desktop_rail_has_header_and_logout():
    auth_state.set_session("t", {"name": "Іван", "points": 5})
    rail = build_navigation_rail(object(), "/news")
    assert rail.leading is not None and "Іван" in _texts(rail.leading)
    assert rail.trailing.tooltip == "Вийти"
