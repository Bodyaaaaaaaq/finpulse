"""Налаштування клієнта. Значення беруться зі змінних середовища / client/.env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

APP_TITLE = "FinPulse"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

# Від цієї ширини вікна замість нижньої панелі показується NavigationRail (десктоп).
WIDE_BREAKPOINT = 720
