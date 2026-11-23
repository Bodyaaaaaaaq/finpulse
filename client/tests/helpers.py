"""Спільні допоміжні функції для тестів сторінок."""
import asyncio

import flet as ft


def run(coro):
    return asyncio.run(coro)


def find(control, cls):
    """Усі вкладені контроли типу cls (обхід content / controls / actions)."""
    found = []

    def walk(c):
        if isinstance(c, cls):
            found.append(c)
        for attr in ("content", "controls", "actions"):
            child = getattr(c, attr, None)
            if isinstance(child, list):
                for x in child:
                    walk(x)
            elif child is not None and not isinstance(child, (str, int, float)):
                walk(child)

    walk(control)
    return found


def texts(control):
    return [t.value for t in find(control, ft.Text) if t.visible]


class FakePage:
    """Мінімальна заміна ft.Page: збирає запущені через run_task завдання."""

    def __init__(self, width=390):
        self.width, self.tasks, self.updates = width, [], 0

    def update(self):
        self.updates += 1

    def run_task(self, handler, *args):
        self.tasks.append((handler, args))

    def run_pending(self):
        """Виконує всі завдання, поставлені сторінкою через run_task."""
        pending, self.tasks = self.tasks, []
        for handler, args in pending:
            run(handler(*args))


class Ctx:
    def __init__(self, wide=False):
        self.page, self.is_wide = FakePage(1280 if wide else 390), wide
        self.went = []  # маршрути, на які сторінка перейшла через ctx.go

    async def go(self, route):
        self.went.append(route)
