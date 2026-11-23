"""Картка новини (макет Figma «Новини»): мініатюра, заголовок, «Категорія · час»."""
import flet as ft

from components.card import Card
from services.news_service import NewsItem, format_age
from theme import MUTED

THUMB = 84
THUMB_BG = "#ADADAD"  # нейтральний сірий — для невідомої категорії

# Плитка замість фото: колір і іконка за категорією (кольори узгоджені з логотипами на головній).
TILES = {
    "CURRENCY": (ft.Icons.CURRENCY_EXCHANGE, "#2F4A9A"),
    "CRYPTO": (ft.Icons.CURRENCY_BITCOIN, "#F7931A"),
    "ECONOMY": (ft.Icons.TRENDING_UP, "#26A17B"),
}


def tile(item: NewsItem) -> ft.Control:
    """Кольорова плитка з іконкою категорії — показується, коли в новини немає фото або воно не завантажилось."""
    icon, color = TILES.get(item.category, (ft.Icons.NEWSPAPER, THUMB_BG))
    return ft.Container(
        ft.Icon(icon, color="white", size=40),
        width=THUMB, height=THUMB, bgcolor=color, border_radius=12, alignment=ft.Alignment.CENTER,
    )


def thumbnail(item: NewsItem) -> ft.Control:
    if not item.image_url:
        return tile(item)
    return ft.Container(
        ft.Image(src=item.image_url, width=THUMB, height=THUMB, fit=ft.BoxFit.COVER,
                 error_content=tile(item)),
        width=THUMB, height=THUMB, border_radius=12, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=THUMB_BG,
    )


def meta_line(item: NewsItem) -> str:
    """'Валюти · 2 год тому'; частини, яких немає, пропускаються."""
    parts = [item.category_label, format_age(item.published_at)]
    return " · ".join(p for p in parts if p)


def news_card(item: NewsItem, on_open) -> ft.Control:
    return Card(
        ft.Row(
            [
                thumbnail(item),
                ft.Column(
                    [ft.Text(item.title, size=17, weight=ft.FontWeight.W_700, max_lines=3,
                             overflow=ft.TextOverflow.ELLIPSIS),
                     ft.Text(meta_line(item), size=13, weight=ft.FontWeight.W_600, color=MUTED)],
                    spacing=6, expand=True, tight=True,
                ),
            ],
            spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=12,
        on_click=lambda e, i=item: on_open(i),
    )
