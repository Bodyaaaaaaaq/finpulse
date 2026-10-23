"""Єдина світла тема (кольори взяті з макета Figma)."""
import flet as ft

BG = "#DFDFDF"        # фон екрана
CARD_BG = "#CCCCCC"   # картки
PRIMARY = "#0088FF"   # акцентний синій
POSITIVE = "#219A47"  # зростання
NEGATIVE = "#D62E2E"  # падіння / помилки
MUTED = "#616161"     # другорядний текст


def apply_theme(page: ft.Page) -> None:
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=PRIMARY)
    page.bgcolor = BG
    page.padding = 0
