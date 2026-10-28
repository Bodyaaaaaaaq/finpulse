import flet as ft

from components.placeholder import placeholder_page


def build(ctx) -> ft.Control:
    return placeholder_page("Конвертер", "FE-7")
