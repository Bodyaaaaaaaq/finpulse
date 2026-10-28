import flet as ft

from theme import CARD_BG


def Card(content: ft.Control, padding: float = 16, on_click=None) -> ft.Container:
    """Сіра картка зі скругленням 15 — основа карток курсів, новин, призів."""
    return ft.Container(
        content=content,
        bgcolor=CARD_BG,
        border_radius=ft.BorderRadius.all(15),
        padding=ft.Padding.all(padding),
        on_click=on_click,
    )
