"""Головна (FE-5): курси валют, криптовалют і металів. Кнопка «Редагувати» — вибір, що показувати."""
import asyncio

import flet as ft

from components.card import Card
from components.form import link_button, page_column, pill_button
from components.header import Header
from components.loading_spinner import LoadingSpinner
from components.rate_row import edit_row, home_row
from services.api_client import ApiError
from services.rates_service import (CRYPTO, CURRENCY, METAL, fetch_crypto, fetch_currency,
                                    fetch_metals, format_time, latest_update)
from state.home_state import home_state
from theme import MUTED, NEGATIVE

SECTIONS = [(CURRENCY, "Курси обміну"), (CRYPTO, "Криптовалюти"), (METAL, "Метали")]
# Підпис поруч із заголовком секції: ціни металів — за 1 грам, а не за унцію
SECTION_CAPTIONS = {METAL: "ціна за грам"}
CRYPTO_LIMIT = 20  # скільки монет пропонуємо в режимі «Редагувати»


def build(ctx) -> ft.Control:
    state = {"editing": False, "loading": True, "error": "", "items": []}
    body = ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def refresh() -> None:
        render()
        ctx.page.update()

    async def on_toggle_edit(e=None) -> None:
        state["editing"] = not state["editing"]
        refresh()

    async def on_retry(e=None) -> None:
        await load()

    async def load() -> None:
        state.update(loading=True, error="")
        refresh()
        results = await asyncio.gather(fetch_currency(), fetch_crypto(limit=CRYPTO_LIMIT), fetch_metals(),
                                       return_exceptions=True)
        items, errors = [], []
        for result in results:
            if isinstance(result, ApiError):
                errors.append(result.message)
            elif isinstance(result, Exception):
                errors.append("Сталася помилка")
            else:
                items.extend(result)
        state["items"] = items
        # Показуємо те, що вдалося завантажити; помилка — лише коли не завантажилось нічого
        state["error"] = errors[0] if errors and not items else ""
        state["loading"] = False
        refresh()

    def switch_handler(key: str):
        async def on_change(e=None) -> None:
            home_state.toggle(key)
            await home_state.save()
        return on_change

    def section_title(kind: str, text: str) -> ft.Control:
        title = ft.Text(text, size=22, weight=ft.FontWeight.W_600)
        caption = SECTION_CAPTIONS.get(kind)
        if not caption:
            return title
        return ft.Row([title, ft.Text(caption, size=13, weight=ft.FontWeight.W_600, color=MUTED)],
                      spacing=8, vertical_alignment=ft.CrossAxisAlignment.END)

    def render() -> None:
        editing = state["editing"]
        header = ft.Row(
            [Header("Головна"), pill_button("Готово" if editing else "Редагувати", on_toggle_edit)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        controls: list[ft.Control] = [header]

        if state["loading"] and not state["items"]:
            controls.append(LoadingSpinner())
        elif state["error"]:
            controls += [ft.Text(state["error"], color=NEGATIVE, size=14),
                         ft.Row([link_button("Повторити", on_retry)], alignment=ft.MainAxisAlignment.CENTER)]
        elif editing:
            controls.append(ft.Text("Оберіть, що показувати на головній", size=14,
                                    weight=ft.FontWeight.W_600, color=MUTED))
            for kind, title in SECTIONS:
                rows = [i for i in state["items"] if i.kind == kind]
                if rows:
                    controls.append(section_title(kind, title))
                    controls += [edit_row(i, home_state.is_selected(i.key), switch_handler(i.key)) for i in rows]
        else:
            shown = [i for i in state["items"] if home_state.is_selected(i.key)]
            if shown:
                controls.append(ft.Text(f"Дані станом на {format_time(latest_update(shown))}", size=13,
                                        weight=ft.FontWeight.W_600, color=MUTED,
                                        visible=latest_update(shown) is not None))
            for kind, title in SECTIONS:
                rows = [i for i in shown if i.kind == kind]
                if rows:
                    controls.append(section_title(kind, title))
                    controls += [home_row(i) for i in rows]
            if not shown:
                controls.append(Card(ft.Text("Нічого не вибрано. Натисніть «Редагувати», щоб додати курси.",
                                             color=MUTED)))
        body.controls = controls

    render()
    ctx.page.run_task(load)
    return page_column(ctx, [body])
