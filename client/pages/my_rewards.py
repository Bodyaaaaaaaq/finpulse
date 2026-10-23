import flet as ft

from components.placeholder import placeholder_page


def build(ctx) -> ft.Control:
    return placeholder_page("Мої призи", "FE-9")
