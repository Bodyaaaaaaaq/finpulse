"""Усі курси валют (НБУ) — кнопка «Усі» в секції «Курси обміну» на головній."""
from pages.rates_list import build_list
from services.rates_service import fetch_currency


def build(ctx):
    return build_list(ctx, "Курси обміну", fetch_currency)
