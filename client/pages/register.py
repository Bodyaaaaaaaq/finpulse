import flet as ft

from components.form import (auth_layout, error_text, labeled, link_button, primary_button,
                             show_error, text_field)
from config import REGISTER_ADDRESS
from services.auth_service import submit_register


def build(ctx) -> ft.Control:
    name = text_field("Іван", autofocus=True)
    email = text_field("name@example.com", keyboard_type=ft.KeyboardType.EMAIL)
    address = text_field("Місто, вулиця, будинок")
    password = text_field("••••••••", password=True)
    confirm = text_field("••••••••", password=True)
    error = error_text()
    button = None

    async def on_submit(e=None) -> None:
        button.disabled = True
        show_error(error, "")
        ctx.page.update()
        message = await submit_register(
            ctx, name.value or "", email.value or "", password.value or "", confirm.value or "",
            (address.value or "") if REGISTER_ADDRESS else None,
        )
        if message:
            show_error(error, message)
            button.disabled = False
            ctx.page.update()

    async def to_login(e) -> None:
        await ctx.go("/login")

    confirm.on_submit = on_submit
    button = primary_button("Створити акаунт", on_submit)

    fields = [labeled("Ім’я", name), labeled("Email", email)]
    if REGISTER_ADDRESS:
        fields.append(labeled("Адреса (обов’язково)", address))
    fields += [labeled("Пароль (мін. 8 символів)", password), labeled("Повторіть пароль", confirm)]

    return auth_layout(ctx, [
        ft.Text("Реєстрація", size=32, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
        *fields,
        error,
        button,
        ft.Row([link_button("Вже є акаунт? Увійти", to_login)], alignment=ft.MainAxisAlignment.CENTER),
    ], top_space=8)
