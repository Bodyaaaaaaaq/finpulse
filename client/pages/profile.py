"""Профіль (FE-4): ім'я, email, баланс, зміна пароля, видалення акаунта з підтвердженням паролем."""
import flet as ft

from components.balance import format_points
from components.card import Card
from components.form import (danger_button, error_text, labeled, page_column, primary_button,
                             show_error, text_field)
from components.header import Header
from services.profile_service import submit_change_password, submit_delete_account
from state.auth_state import auth_state
from theme import MUTED, NEGATIVE, POSITIVE, PRIMARY


def avatar(name: str) -> ft.Control:
    """Синє коло з першою літерою імені."""
    initial = (name.strip()[:1] or "?").upper()
    return ft.Container(
        ft.Text(initial, size=24, weight=ft.FontWeight.W_600, color="white"),
        width=56, height=56, shape=ft.BoxShape.CIRCLE, bgcolor=PRIMARY,
        alignment=ft.Alignment.CENTER,
    )


def user_card() -> ft.Control:
    user = auth_state.user or {}
    lines = [
        ft.Text(auth_state.name or "Користувач", size=20, weight=ft.FontWeight.W_700),
        ft.Text(auth_state.email, size=14, weight=ft.FontWeight.W_500, color=MUTED),
    ]
    if user.get("address"):  # сервер поки не повертає адресу; покажемо, коли зʼявиться
        lines.append(ft.Text(user["address"], size=14, weight=ft.FontWeight.W_500, color=MUTED))
    return Card(
        ft.Row([avatar(auth_state.name), ft.Column(lines, spacing=2, expand=True)], spacing=16,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


def balance_row() -> ft.Control:
    return Card(
        ft.Row(
            [
                ft.Text("Баланс", size=14, weight=ft.FontWeight.W_600, color=MUTED),
                ft.Text(f"{format_points(auth_state.points)} балів", size=20,
                        weight=ft.FontWeight.W_800, color=PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=12,
    )


def build(ctx) -> ft.Control:
    old = text_field("••••••••", password=True)
    new = text_field("••••••••", password=True)
    error = error_text()
    success = ft.Text("", color=POSITIVE, size=14, weight=ft.FontWeight.W_500, visible=False)
    save = None

    async def on_save(e=None) -> None:
        save.disabled = True  # кнопка неактивна під час запиту
        show_error(error, "")
        success.visible = False
        ctx.page.update()
        message = await submit_change_password(old.value or "", new.value or "")
        if message:
            show_error(error, message)
        else:
            old.value = new.value = ""
            success.value = "Пароль змінено"
            success.visible = True
        save.disabled = False
        ctx.page.update()

    new.on_submit = on_save
    save = primary_button("Зберегти", on_save)

    async def on_delete(e=None) -> None:
        password = text_field("Пароль", password=True, autofocus=True)
        dialog_error = error_text()
        confirm = ft.TextButton(content=ft.Text("Видалити", color=NEGATIVE, weight=ft.FontWeight.W_700))

        async def on_cancel(e=None) -> None:
            ctx.page.pop_dialog()

        async def on_confirm(e=None) -> None:
            confirm.disabled = True
            show_error(dialog_error, "")
            ctx.page.update()
            message = await submit_delete_account(ctx, password.value or "")
            if message:  # успіх: submit_delete_account уже відкрив /login
                show_error(dialog_error, message)
                confirm.disabled = False
                ctx.page.update()
            else:
                ctx.page.pop_dialog()

        confirm.on_click = on_confirm
        password.on_submit = on_confirm
        ctx.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Видалити акаунт?"),
            content=ft.Column(
                [
                    ft.Text("Дію не можна скасувати. Введіть пароль для підтвердження."),
                    password,
                    dialog_error,
                ],
                tight=True, spacing=12,
            ),
            actions=[ft.TextButton(content="Скасувати", on_click=on_cancel), confirm],
        ))

    return page_column(ctx, [
        Header("Профіль"),
        user_card(),
        balance_row(),
        ft.Text("Змінити пароль", size=22, weight=ft.FontWeight.W_600),
        labeled("Поточний пароль", old),
        labeled("Новий пароль", new),
        error,
        success,
        save,
        danger_button("Видалити акаунт", on_delete),
    ])
