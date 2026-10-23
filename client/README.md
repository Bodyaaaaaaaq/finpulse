# FinPulse — клієнт (Flet)

Каркас клієнта (задача **FE-1**): проєкт Flet, роутинг, адаптивна навігація, сторінка 404.

## Запуск

```bash
cd client
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
flet run                         # десктоп-вікно
flet run --web                   # у браузері
```

Тести: `pip install -r requirements-dev.txt && pytest`

## Маршрути

| Адреса | Доступ | Сторінка | Задача |
| --- | --- | --- | --- |
| `/login`, `/register` | не залогінені | Вхід, реєстрація | FE-3 |
| `/` | залогінені | Головна (курси валют, крипти, металів) | FE-5 |
| `/converter` | залогінені | Конвертер | FE-7 |
| `/news` | залогінені | Новини | FE-6 |
| `/crypto` | залогінені | Криптовалюти | FE-5 |
| `/more` | залогінені | Меню «Інше» (Гра, Магазин, Мої призи, Профіль, Вийти) | FE-1 |
| `/game` | залогінені | Гра | FE-8 |
| `/shop`, `/shop/my-rewards` | залогінені | Магазин, мої призи | FE-9 |
| `/profile` | залогінені | Профіль | FE-4 |
| `/currency`, `/metals` | — | перенаправляють на `/` | — |
| будь-що інше | усі | 404 | FE-1 |

Метали окремої сторінки не мають: що показувати на головній (валюти, крипта, метали), користувач обирає кнопкою «Редагувати».

## Навігація

- Ширина < 720 px — нижня панель із 5 вкладками (Головна, Конвертер, Новини, Криптовалюти, Інше).
- Ширина ≥ 720 px — бічна NavigationRail з усіма розділами і кнопкою «Вийти».
- Не залогінений користувач на приватній сторінці потрапляє на `/login`, залогінений на `/login` потрапляє на `/`.

## Структура

```
client/
├─ main.py            точка входу
├─ router.py          таблиця маршрутів, guard, 404, вибір навігації
├─ config.py, theme.py
├─ pages/             по файлу на сторінку (build(ctx) -> Control)
├─ components/        Header, Card, LoadingSpinner, navbar, placeholder
├─ services/          api_client.py
├─ state/             auth_state.py
├─ assets/
└─ tests/
```

## Як додати сторінку

1. Створити `pages/<name>.py` з функцією `build(ctx) -> ft.Control` (`ctx.go(route)` — перехід, `ctx.logout()` — вихід).
2. Додати `RouteDef("/path", <name>.build)` у `ROUTES` в `router.py`.
3. За потреби додати пункт у `components/navbar.py`.

## Тимчасове в FE-1

- На `/login` є кнопка «Увійти (тимчасово)», яка вмикає фейкову сесію. Прибрати у FE-3.
- Сесія зберігається тільки в памʼяті і зникає після перезавантаження. Збереження токена — FE-2.
