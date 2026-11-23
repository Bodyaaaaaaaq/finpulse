"""Новини (FE-6): стрічка карток, фільтр за категорією, пошук, «Показати ще»; клік відкриває статтю в браузері."""
import asyncio

import flet as ft

from components.card import Card
from components.form import link_button, page_column, text_field
from components.header import Header
from components.loading_spinner import LoadingSpinner
from components.news_card import news_card
from services.api_client import ApiError
from services.news_service import CATEGORIES, PAGE_SIZE, fetch_news
from theme import MUTED, NEGATIVE, PRIMARY

SEARCH_DELAY = 0.3  # пауза після останнього символу, щоб не слати запит на кожну літеру
CHIP_BG = "#F7F7F7"


async def open_url(url: str) -> None:
    await ft.UrlLauncher().launch_url(url)


def build(ctx) -> ft.Control:
    state = {"category": None, "loading": True, "more": False, "error": "",
             "items": [], "total": 0, "request": 0}
    search = text_field("Пошук у новинах")
    chips = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    body = ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def refresh() -> None:
        render()
        ctx.page.update()

    async def load(append: bool = False) -> None:
        state["request"] += 1
        mine = state["request"]
        offset = len(state["items"]) if append else 0
        state.update(loading=not append, more=append, error="")
        if not append:
            state["items"], state["total"] = [], 0
        refresh()
        try:
            page = await fetch_news(state["category"], search.value or None, offset, PAGE_SIZE)
        except ApiError as e:
            page, error = None, e.message
        except Exception:
            page, error = None, "Сталася помилка"
        else:
            error = ""
        if mine != state["request"]:
            return  # користувач змінив категорію чи пошук — ця відповідь застаріла
        state.update(loading=False, more=False, error=error)
        if page is not None:
            state["items"] = state["items"] + page.items if append else page.items
            state["total"] = page.total
        refresh()

    async def on_search(e=None) -> None:
        typed = search.value or ""
        await asyncio.sleep(SEARCH_DELAY)
        if (search.value or "") == typed:
            await load()

    async def on_category(code) -> None:
        if code == state["category"]:
            return
        state["category"] = code
        await load()

    async def on_more(e=None) -> None:
        await load(append=True)

    async def on_retry(e=None) -> None:
        await load(append=bool(state["items"]))

    async def on_open(item) -> None:
        try:
            await open_url(item.source_url)
        except Exception:
            state["error"] = "Не вдалося відкрити посилання"
            refresh()

    def chip(code, label) -> ft.Control:
        active = code == state["category"]
        return ft.Container(
            ft.Text(label, size=15, weight=ft.FontWeight.W_600, color="white" if active else "black"),
            bgcolor=PRIMARY if active else CHIP_BG, border_radius=20,
            padding=ft.Padding(left=16, top=8, right=16, bottom=8),
            on_click=lambda e, c=code: ctx.page.run_task(on_category, c),
        )

    def render() -> None:
        chips.controls = [chip(c, label) for c, label in CATEGORIES]
        controls: list[ft.Control] = []
        if state["loading"]:
            controls.append(LoadingSpinner())
        else:
            controls += [news_card(i, lambda item: ctx.page.run_task(on_open, item)) for i in state["items"]]
            if not state["items"] and not state["error"]:
                controls.append(Card(ft.Text("Новин не знайдено", color=MUTED)))
            if state["error"]:
                controls += [ft.Text(state["error"], color=NEGATIVE, size=14),
                             ft.Row([link_button("Повторити", on_retry)], alignment=ft.MainAxisAlignment.CENTER)]
            elif state["more"]:
                controls.append(LoadingSpinner())
            elif len(state["items"]) < state["total"]:
                controls.append(ft.Row([link_button("Показати ще", on_more)],
                                       alignment=ft.MainAxisAlignment.CENTER))
        body.controls = controls

    search.on_change = on_search
    render()
    ctx.page.run_task(load)
    return page_column(ctx, [Header("Новини"), chips, search, body])
