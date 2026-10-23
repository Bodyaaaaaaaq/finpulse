import flet as ft

from config import APP_TITLE
from router import Router
from theme import apply_theme


async def main(page: ft.Page) -> None:
    page.title = APP_TITLE
    apply_theme(page)

    router = Router(page)
    page.on_route_change = router.on_route_change
    page.on_resize = router.on_resize
    page.on_view_pop = router.on_view_pop

    await router.on_route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
