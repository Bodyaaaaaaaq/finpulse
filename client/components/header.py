import flet as ft


def Header(title: str) -> ft.Control:
    """Великий заголовок сторінки (як «Головна» в макеті)."""
    return ft.Text(title, size=32, weight=ft.FontWeight.W_800)
