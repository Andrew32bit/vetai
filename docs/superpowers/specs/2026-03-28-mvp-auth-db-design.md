# MVP: Auth + DB + Лимиты — Design Spec

## Goal

Подключить реальную авторизацию через Telegram, сохранять пользователей в SQLite, трекать входы и ограничивать использование в бета-версии (3 запроса/день суммарно).

## Auth Flow

```
Пользователь открывает Mini App
  → Telegram передаёт initData
  → Фронтенд: WebApp.initDataUnsafe.user → POST /api/v1/users/auth
  → Бэкенд:
      Новый → создаёт User, возвращает { is_new: true }
      Существующий → обновляет last_login/login_count/username/platform, возвращает { is_new: false, user + pets }
  → Фронтенд:
      is_new → онбординг → POST /api/v1/users/register (pet + city)
      !is_new → localStorage = данные из БД → главная
```

## DB Changes

### Таблица `users` — новые поля

| Поле | Тип | Default | Описание |
|------|-----|---------|----------|
| username | str, nullable | null | @username Telegram |
| language_code | str | "ru" | Язык из Telegram |
| is_premium | bool | false | Telegram Premium |
| platform | str, nullable | null | ios/android/desktop/web |
| login_count | int | 1 | Счётчик входов |
| last_login | datetime | now | Последний вход |
| city | str, nullable | null | Город пользователя |

### Новая таблица `usage_log`

| Поле | Тип | Описание |
|------|-----|----------|
| id | int PK | |
| user_id | int FK → users | |
| feature | str | "photo" / "chat" / "lab" |
| used_at | datetime | Время использования |

Лимит: **3 запроса в день суммарно** (фото + чат + анализы). Проверка: `SELECT COUNT(*) FROM usage_log WHERE user_id=? AND date(used_at)=date('now')` → если >= 3 → HTTP 429.

## API Endpoints

### POST /api/v1/users/auth (новый)

Request:
```json
{
  "telegram_id": 123456789,
  "first_name": "Андрей",
  "last_name": "К",
  "username": "andrewk",
  "language_code": "ru",
  "is_premium": false,
  "platform": "android"
}
```

Response (новый пользователь):
```json
{ "is_new": true, "user_id": 1 }
```

Response (существующий):
```json
{
  "is_new": false,
  "user": {
    "id": 1,
    "telegram_id": 123456789,
    "first_name": "Андрей",
    "subscription_tier": "beta",
    "city": "Москва",
    "pets": [{ "id": 1, "name": "Барон", "species": "dog", "breed": "Овчарка" }]
  },
  "usage_today": 1,
  "usage_limit": 3
}
```

### POST /api/v1/users/register (обновить)

Вызывается после онбординга для существующего user (is_new=true). Добавляет pet + city.

Request:
```json
{
  "telegram_id": 123456789,
  "pet": { "name": "Барон", "species": "dog", "breed": "Овчарка" },
  "city": "Москва"
}
```

### GET /api/v1/users/me (обновить)

Header: `x-telegram-id: 123456789`
Возвращает user + pets + usage_today из БД.

## Frontend Changes

### App.jsx
- При старте: `WebApp.initDataUnsafe.user` → POST `/auth`
- `is_new` → онбординг, `!is_new` → localStorage = response.user → главная
- Определять `platform` из `WebApp.platform` или User-Agent

### Все страницы
- Реальный `telegram_id` из `WebApp.initDataUnsafe.user.id` вместо хардкода `"12345"`
- Хранить в React context или localStorage

### Лимиты в UI
- При 429 — показывать сообщение "Лимит 3 запроса в день исчерпан. Попробуйте завтра."
- На главной показывать остаток: "Осталось запросов: 2/3"

## Constraints

- SQLite для dev/beta (файл vetai.db), PostgreSQL для prod
- init_db() при старте бэкенда — создаёт таблицы если не существуют
- Лимит бета: 3 запроса/день суммарно на все функции
