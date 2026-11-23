"""Повний список курсів одного розділу (валюти, метали): відкривається кнопкою «Усі» на головній."""
from typing import Awaitable, Callable, Optional

import flet as ft

from components.card import Card
from components.form import link_button, page_column
from components.header import Header
from components.loading_spinner import LoadingSpinner
from components.rate_row import list_row
from services.api_client import ApiError
from services.rates_service import RateItem, format_time, latest_update
from theme import MUTED, NEGATIVE


def build_list(ctx, title: str, fetch: Callable[[], Awaitable[list[RateItem]]],
               caption: Optional[str] = None) -> ft.Control:
    state = {"loading": True, "error": "", "items": []}
    body = ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def refresh() -> None:
        render()
        ctx.page.update()

    async def load() -> None:
        state.update(loading=True, error="")
        refresh()
        try:
            items = await fetch()
        except ApiError as e:
            items, error = [], e.message
        except Exception:
            items, error = [], "Сталася помилка"
        else:
            error = ""
        state.update(loading=False, error=error, items=items)
        refresh()

    async def on_retry(e=None) -> None:
        await load()

    async def on_back(e=None) -> None:
        await ctx.go("/")

    def render() -> None:
        controls: list[ft.Control] = []
        if state["loading"]:
            controls.append(LoadingSpinner())
        elif state["error"]:
            controls += [ft.Text(state["error"], color=NEGATIVE, size=14),
                         ft.Row([link_button("Повторити", on_retry)], alignment=ft.MainAxisAlignment.CENTER)]
        elif not state["items"]:
            controls.append(Card(ft.Text("Немає даних", color=MUTED)))
        else:
            updated = latest_update(state["items"])
            controls.append(ft.Text(f"Дані станом на {format_time(updated)}", size=13,
                                    weight=ft.FontWeight.W_600, color=MUTED, visible=updated is not None))
            controls += [list_row(i) for i in state["items"]]
        body.controls = controls

    heading = [Header(title)]
    if caption:
        heading.append(ft.Text(caption, size=13, weight=ft.FontWeight.W_600, color=MUTED))
    render()
    ctx.page.run_task(load)
    back = ft.Row([link_button("‹ Головна", on_back)], alignment=ft.MainAxisAlignment.START)
    return page_column(ctx, [back, *heading, body])
