import flet as ft

from config import APP_TITLE
from router import Router
from services.session_service import restore_session
from state.home_state import HomeStore, home_state
from state.session_store import SessionStore
from theme import apply_theme


async def main(page: ft.Page) -> None:
    page.title = APP_TITLE
    apply_theme(page)

    # Збереження токена між запусками; сесія відновлюється запитом /auth/me.
    prefs = ft.SharedPreferences()
    page.services.append(prefs)
    store = SessionStore(prefs)
    await restore_session(store)
    await home_state.load(HomeStore(prefs))  # вибір курсів на головній

    router = Router(page, store)
    router.attach()
    page.on_route_change = router.on_route_change
    page.on_resize = router.on_resize
    page.on_view_pop = router.on_view_pop

    await router.on_route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
