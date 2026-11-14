# FinPulse — клієнт (Flet)

Каркас клієнта (**FE-1**): проєкт Flet, роутинг, адаптивна навігація, сторінка 404.
Шапка/навігація та стан сесії (**FE-2**): баланс у навігації, збереження входу, вихід, обробка 401.

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

## Вхід і реєстрація (FE-3)

Екрани зроблено за макетом Figma («Вхід», «Реєстрація»).

- Клієнтська валідація (`services/validation.py`): формат email, імʼя, адреса, пароль ≥ 8 символів (і ≤ 72 байтів — обмеження bcrypt), збіг паролів. Показується перша знайдена помилка.
- Помилки сервера (неправильний пароль, email уже існує, 429 «забагато спроб», сервер недоступний) показуються червоним текстом над кнопкою.
- Під час запиту кнопка неактивна; Enter у останньому полі відправляє форму.
- Логіка запитів — `services/auth_service.py` (`submit_login`, `submit_register`); після успіху викликається `ctx.login(user)` (FE-2) і відкривається головна.
- Поле «Адреса» є в макеті, але сервер (BE-2) його поки не зберігає — запит надсилає `address`, сервер його ігнорує. Щоб прибрати поле: `REGISTER_ADDRESS=false` у `client/.env`.

## Сесія (FE-2)

Сервер (BE-2) після входу/реєстрації ставить httpOnly-cookie `token` (JWT на 7 днів).

- `services/api_client.py` читає `token` із `Set-Cookie` відповіді й додає його у `Cookie` кожного запиту. Усі адреси — відносно `API_BASE_URL + /api`.
- `state/auth_state.py` — токен і дані користувача (`name`, `email`, `points`).
- `state/session_store.py` — збереження токена між запусками (Flet `SharedPreferences`).
- `services/session_service.py` — `restore_session` (при запуску перевіряє токен запитом `GET /auth/me`), `refresh_user` (оновити баланс), `sign_out` (`POST /auth/logout` + очищення).
- Якщо сервер відповів 401 для залогіненого користувача (токен прострочений) — стан очищується й відкривається `/login`.
- Для сторінок (`ctx`): `await ctx.login(user)` — викликати після успішного входу/реєстрації (FE-3), `await ctx.logout()` — вихід.
- Баланс: десктоп — шапка NavigationRail (ім'я, бали), мобільний — картка «Ваш баланс» на сторінці «Інше»; після зміни балансу (збір предмета, обмін) викликайте `refresh_user()`.

## Структура

```
client/
├─ main.py            точка входу
├─ router.py          таблиця маршрутів, guard, 404, вибір навігації
├─ config.py, theme.py
├─ pages/             по файлу на сторінку (build(ctx) -> Control)
├─ components/        Header, Card, LoadingSpinner, balance, navbar, placeholder
├─ services/          api_client.py, session_service.py
├─ state/             auth_state.py, session_store.py
├─ assets/
└─ tests/
```

## Як додати сторінку

1. Створити `pages/<name>.py` з функцією `build(ctx) -> ft.Control` (`ctx.go(route)` — перехід, `ctx.logout()` — вихід).
2. Додати `RouteDef("/path", <name>.build)` у `ROUTES` в `router.py`.
3. За потреби додати пункт у `components/navbar.py`.

## Тимчасове в FE-1

