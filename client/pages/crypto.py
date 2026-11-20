"""Криптовалюти (FE-5): топ монет за капіталізацією, ціна в USD, зміна за 24 год, пошук."""
import asyncio

import flet as ft

from components.card import Card
from components.form import link_button, page_column, text_field
from components.header import Header
from components.loading_spinner import LoadingSpinner
from components.rate_row import crypto_row
from services.api_client import ApiError
from services.rates_service import fetch_crypto, format_time, latest_update
from theme import MUTED, NEGATIVE

SEARCH_DELAY = 0.3  # пауза після останнього символу, щоб не слати запит на кожну літеру


def build(ctx) -> ft.Control:
    state = {"loading": True, "error": "", "items": [], "request": 0}
    search = text_field("Пошук монети")
    body = ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def refresh() -> None:
        render()
        ctx.page.update()

    async def load() -> None:
        state["request"] += 1
        mine = state["request"]
        state.update(loading=True, error="")
        refresh()
        try:
            items = await fetch_crypto(search.value or None)
        except ApiError as e:
            items, error = [], e.message
        except Exception:
            items, error = [], "Сталася помилка"
        else:
            error = ""
        if mine != state["request"]:
            return  # користувач уже змінив запит — ця відповідь застаріла
        state.update(loading=False, error=error, items=items)
        refresh()

    async def on_search(e=None) -> None:
        typed = search.value or ""
        await asyncio.sleep(SEARCH_DELAY)
        if (search.value or "") == typed:
            await load()

    async def on_retry(e=None) -> None:
        await load()

    def render() -> None:
        controls: list[ft.Control] = []
        if state["loading"] and not state["items"]:
            controls.append(LoadingSpinner())
        elif state["error"]:
            controls += [ft.Text(state["error"], color=NEGATIVE, size=14),
                         ft.Row([link_button("Повторити", on_retry)], alignment=ft.MainAxisAlignment.CENTER)]
        elif not state["items"]:
            controls.append(Card(ft.Text("Нічого не знайдено", color=MUTED)))
        else:
            updated = latest_update(state["items"])
            controls.append(ft.Text(f"Дані станом на {format_time(updated)}", size=13,
                                    weight=ft.FontWeight.W_600, color=MUTED, visible=updated is not None))
            controls += [crypto_row(i) for i in state["items"]]
        body.controls = controls

    search.on_change = on_search
    render()
    ctx.page.run_task(load)
    return page_column(ctx, [Header("Криптовалюти"), search, body])
