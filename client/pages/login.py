import flet as ft

from components.form import (auth_layout, error_text, labeled, link_button, primary_button,
                             show_error, text_field)
from services.auth_service import submit_login
from theme import MUTED, PRIMARY


def build(ctx) -> ft.Control:
    email = text_field("name@example.com", keyboard_type=ft.KeyboardType.EMAIL, autofocus=True)
    password = text_field("••••••••", password=True)
    error = error_text()
    button = None

    async def on_submit(e=None) -> None:
        button.disabled = True       # кнопка неактивна під час запиту
        show_error(error, "")
        ctx.page.update()
        message = await submit_login(ctx, email.value or "", password.value or "")
        if message:                  # успіх → submit_login уже перейшов на головну
            show_error(error, message)
            button.disabled = False
            ctx.page.update()

    async def to_register(e) -> None:
        await ctx.go("/register")

    password.on_submit = on_submit
    button = primary_button("Увійти", on_submit)

    return auth_layout(ctx, [
        ft.Text("FinPulse", size=40, weight=ft.FontWeight.W_800, color=PRIMARY,
                text_align=ft.TextAlign.CENTER),
        ft.Text("Курси, новини та гра в одному місці", size=14, weight=ft.FontWeight.W_600,
                color=MUTED, text_align=ft.TextAlign.CENTER),
        ft.Container(height=8),
        labeled("Email", email),
        labeled("Пароль", password),
        error,
        button,
        ft.Row([link_button("Немає акаунта? Зареєструватися", to_register)],
               alignment=ft.MainAxisAlignment.CENTER),
    ], top_space=48)
