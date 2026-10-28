import flet as ft

from theme import MUTED, PRIMARY


def build(ctx) -> ft.Control:
    async def to_home(e: ft.Event[ft.Button]) -> None:
        await ctx.go("/")

    return ft.Column(
        [
            ft.Text("404", size=96, weight=ft.FontWeight.W_800, color=PRIMARY),
            ft.Text("Сторінку не знайдено", size=22, weight=ft.FontWeight.W_600),
            ft.Text("Можливо, адресу введено з помилкою або сторінку видалено.", color=MUTED),
            ft.Button(content="На головну", on_click=to_home),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
        expand=True,
    )
