"""Усі метали — кнопка «Усі» в секції «Метали» на головній."""
from pages.rates_list import build_list
from services.rates_service import fetch_metals


def build(ctx):
    return build_list(ctx, "Метали", fetch_metals, caption="ціна за грам")
