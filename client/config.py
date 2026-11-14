"""Налаштування клієнта. Значення беруться зі змінних середовища / client/.env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

APP_TITLE = "FinPulse"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
# Усі адреси сервера починаються з /api (ТЗ 5.1)
API_URL = f"{API_BASE_URL}/api"

# Макет Figma: на реєстрації є обов'язкове поле «Адреса». Сервер (BE-2) поки його не зберігає;
# якщо поле не потрібне — REGISTER_ADDRESS=false у .env.
REGISTER_ADDRESS = os.getenv("REGISTER_ADDRESS", "true").lower() == "true"

# Від цієї ширини вікна замість нижньої панелі показується NavigationRail (десктоп).
WIDE_BREAKPOINT = 720
