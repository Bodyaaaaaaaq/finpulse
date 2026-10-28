import flet as ft

from components.card import Card
from components.header import Header
from theme import MUTED


def placeholder_page(title: str, task: str) -> ft.Control:
    """Заглушка сторінки, поки її не реалізовано у відповідній задачі."""
    return ft.Column(
        [
            Header(title),
            Card(ft.Text(f"Сторінку буде реалізовано в задачі {task}", color=MUTED)),
        ],
        spacing=12,
    )
