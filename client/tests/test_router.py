import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from components.navbar import desktop_index, mobile_index  # noqa: E402
from router import ROUTES, Router, normalize  # noqa: E402
from state.auth_state import auth_state  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_session():
    auth_state.clear()
    yield
    auth_state.clear()


def make_router(width=390):
    return Router(SimpleNamespace(width=width, route="/", views=[]))


@pytest.mark.parametrize("raw,expected", [
    (None, "/"), ("", "/"), ("/", "/"), ("/news/", "/news"),
    ("/shop/my-rewards?x=1", "/shop/my-rewards"), ("/game#top", "/game"),
])
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_guest_is_sent_to_login_from_private_pages():
    r = make_router()
    for path, d in ROUTES.items():
        if not d.public:
            assert r.redirect_target(path) == "/login"


def test_guest_can_open_login_and_register():
    r = make_router()
    assert r.redirect_target("/login") is None
    assert r.redirect_target("/register") is None


def test_logged_in_user_is_sent_away_from_login():
    auth_state.set_session("t")
    r = make_router()
    assert r.redirect_target("/login") == "/"
    assert r.redirect_target("/register") == "/"
    assert r.redirect_target("/news") is None


def test_unknown_route_is_404_for_everyone():
    r = make_router()
    assert r.redirect_target("/nope") is None
    auth_state.set_session("t")
    assert r.redirect_target("/nope") is None


def test_full_lists_of_currency_and_metals_are_private_pages():
    r = make_router()
    assert r.redirect_target("/currency") == "/login" and r.redirect_target("/metals") == "/login"
    auth_state.set_session("t")
    assert r.redirect_target("/currency") is None and r.redirect_target("/metals") is None


def test_full_list_pages_highlight_home_tab():
    from components.navbar import mobile_index
    assert mobile_index("/currency") == 0 and mobile_index("/metals") == 0


def test_wide_breakpoint():
    assert not make_router(390).is_wide
    assert make_router(1200).is_wide


def test_mobile_more_tab_is_highlighted_for_hidden_sections():
    more = mobile_index("/more")
    for route in ("/game", "/shop", "/shop/my-rewards", "/profile"):
        assert mobile_index(route) == more


def test_desktop_index():
    assert desktop_index("/") == 0
    assert desktop_index("/shop/my-rewards") is not None
    assert desktop_index("/shop/my-rewards") != desktop_index("/shop")
    assert desktop_index("/more") is None
