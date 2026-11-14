"""Елементи форм у стилі макета Figma: підпис над полем, світле поле, синя кнопка, червона помилка."""
import flet as ft

from theme import MUTED, NEGATIVE, PRIMARY

FIELD_BG = "#F7F7F7"
CARD_BG_SOFT = "#EBEBEB"  # картка форми на десктопі


def text_field(hint: str, *, password: bool = False, keyboard_type=None, on_submit=None,
               autofocus: bool = False) -> ft.TextField:
    return ft.TextField(
        hint_text=hint,
        hint_style=ft.TextStyle(color="#8A8A8A"),
        password=password,
        can_reveal_password=password,
        keyboard_type=keyboard_type or ft.KeyboardType.TEXT,
        filled=True,
        bgcolor=FIELD_BG,
        # Заокруглення задаємо в самій рамці (TextField.border_radius застаріло);
        # прозора лінія — щоб рамки не було видно, але кути лишились округлими.
        border=ft.OutlineInputBorder(
            border_radius=ft.BorderRadius.all(15),
            side=ft.BorderSide(0, ft.Colors.TRANSPARENT),
        ),
        content_padding=ft.Padding(left=16, top=16, right=16, bottom=16),
        text_size=16,
        on_submit=on_submit,
        autofocus=autofocus,
    )


def labeled(label: str, field: ft.Control) -> ft.Control:
    """Підпис над полем (як «Email», «Пароль» у макеті); поле розтягується на всю ширину форми."""
    return ft.Column(
        [ft.Text(label, size=13, weight=ft.FontWeight.W_600, color=MUTED), field],
        spacing=6,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def error_text() -> ft.Text:
    """Помилка сервера/валідації — червоним над кнопкою; ховається, поки порожня."""
    return ft.Text("", color=NEGATIVE, size=14, weight=ft.FontWeight.W_500, visible=False)


def show_error(label: ft.Text, message: str) -> None:
    label.value = message
    label.visible = bool(message)


def primary_button(text: str, on_click) -> ft.Button:
    """Синя кнопка на всю ширину форми (розтягується, бо лежить у Column з STRETCH)."""
    return ft.Button(
        content=text,
        on_click=on_click,
        height=52,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: PRIMARY, ft.ControlState.DISABLED: "#9CCBF5"},
            color={ft.ControlState.DEFAULT: "white", ft.ControlState.DISABLED: "white"},
            shape=ft.RoundedRectangleBorder(radius=26),
            text_style=ft.TextStyle(size=17, weight=ft.FontWeight.W_600),
        ),
    )


def link_button(text: str, on_click) -> ft.TextButton:
    return ft.TextButton(
        content=ft.Text(text, color=PRIMARY, weight=ft.FontWeight.W_600),
        on_click=on_click,
    )


def auth_layout(ctx, controls: list, *, top_space: int = 0) -> ft.Control:
    """Центрує форму входу/реєстрації.

    Мобільний: форма на всю ширину екрана з полями 19 px (як у макеті).
    Десктоп: вузька картка по центру (адаптивна ширина через ResponsiveRow), трохи нижче верху екрана.
    """
    wide = bool(getattr(ctx, "is_wide", False))
    form = ft.Column(
        controls,
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
    if wide:
        form = ft.Container(
            form,
            padding=ft.Padding.all(32),
            bgcolor=CARD_BG_SOFT,
            border_radius=ft.BorderRadius.all(24),
            shadow=ft.BoxShadow(blur_radius=24, color="#26000000", offset=ft.Offset(0, 6)),
        )
    height = getattr(getattr(ctx, "page", None), "height", None) or 800
    top = max(24, int(height * 0.1)) if wide else top_space
    return ft.Column(
        [
            ft.Container(height=top),
            ft.ResponsiveRow(
                [ft.Container(form, col={"xs": 12, "sm": 9, "md": 7, "lg": 5, "xl": 4, "xxl": 3})],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
