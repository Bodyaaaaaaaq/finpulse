"""Запуск сервера з Visual Studio (кнопка F5).

У Solution Explorer: правий клік на run.py -> Set as Startup Item, потім F5.
Swagger: http://127.0.0.1:8000/api/docs
"""
import os
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    # Працюємо з папки server, щоб завжди знаходився файл .env
    os.chdir(Path(__file__).resolve().parent)
    port = int(os.getenv("PORT", "8000"))
    # reload=False, щоб у VS працювали точки зупину (breakpoints)
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
