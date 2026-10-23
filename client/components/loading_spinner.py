import flet as ft

from theme import MUTED


def LoadingSpinner(text: str = "Завантаження…") -> ft.Control:
    return ft.Row(
        [ft.ProgressRing(width=24, height=24, stroke_width=3), ft.Text(text, color=MUTED)],
        alignment=ft.MainAxisAlignment.CENTER,
    )
