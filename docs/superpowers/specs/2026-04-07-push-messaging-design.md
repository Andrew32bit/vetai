# Push Messaging for VetAI Telegram Bot

## Overview

Add outbound Telegram messages to VetAI: welcome after onboarding, 24h reminder for inactive users, and manual broadcast via admin endpoint + slash command.

## Components

### 1. Welcome Message (after onboarding)

**Trigger:** Successful `POST /api/v1/users/register` (pet added, onboarding complete).

**Message (RU):**
> Отлично! Всё готово 🐾 Попробуйте сфотографировать глаза, уши или кожу питомца — VetAI даст предварительную оценку за 30 секунд. Это бесплатно!
> [Проверить питомца]

**Message (EN):**
> All set! 🐾 Try taking a photo of your pet's eyes, ears, or skin — VetAI will give you a preliminary assessment in 30 seconds. It's free!
> [Check your pet]

**Language selection:** Based on `user.language_code` — starts with "ru" → RU, else EN.

**Button:** Inline keyboard with URL button pointing to Mini App (`https://t.me/vetai_app_bot/app`).

**Implementation:** Call `send_welcome_message(telegram_id, language_code)` at the end of `/register` endpoint in `user.py`. Function lives in `alerting.py`.

### 2. 24h Reminder (Azure Function timer)

**Trigger:** Azure Function with timer trigger, runs every hour.

**Query:** Users where:
- `created_at` between 23 and 25 hours ago
- Total usage = 0 (no photo, chat, or lab requests ever)
- `reminder_sent = False`

**Database change:** Add `reminder_sent` column to User model (`Boolean, default=False`).

**Message (RU):**
> Привет! Попробуйте сфотографировать глаза, уши или кожу питомца — VetAI даст предварительную оценку за 30 секунд. Это бесплатно 🐾
> [Проверить питомца]

**Message (EN):**
> Hi! Try taking a photo of your pet's eyes, ears, or skin — VetAI will give you a preliminary assessment in 30 seconds. It's free 🐾
> [Check your pet]

**Implementation:** New file `api/reminder_function.py` (Azure Function with TimerTrigger). Uses same DB connection and `sendMessage` pattern from `alerting.py`. After sending, sets `reminder_sent = True`.

**Error handling:** If `sendMessage` returns 403 (bot blocked by user), log and mark `reminder_sent = True` to avoid retrying. If network error, skip — will retry next hour.

### 3. Manual Broadcast (admin endpoint + slash command)

**Endpoint:** `POST /api/v1/users/admin/send-message`

**Auth:** Header `admin-key: vetai-admin-2026` (same as other admin endpoints).

**Request body:**
```json
{
  "text": "Message text",
  "target": "all" | "active" | 370577745
}
```

- `"all"` — all users except test (telegram_id=12345)
- `"active"` — users with at least 1 request (usage > 0)
- `integer` — specific telegram_id

**Response:**
```json
{
  "sent": 23,
  "failed": 2,
  "blocked": ["@username1"]
}
```

**Button:** Every broadcast automatically appends an inline keyboard with [Открыть VetAI / Open VetAI] URL button (language based on user's `language_code`).

**Rate limiting:** Max 1 broadcast per hour to prevent accidental spam.

**Slash command:** `/send_telega_promo` — Claude Code skill that asks for text + target, then calls the endpoint.

### Shared Infrastructure

**Message sending function** in `alerting.py`:
```python
def send_user_message(telegram_id: int, text: str, language: str = "ru") -> bool:
```
- Uses `urllib.request` POST to `https://api.telegram.org/bot{TOKEN}/sendMessage`
- Adds inline keyboard with Mini App URL button
- `parse_mode: "HTML"`
- Returns `True` on success, `False` on failure
- Logs blocked users (403 response)

**Mini App URL for button:** `https://t.me/vetai_app_bot/app`

## Database Migration

Add to User model in `database.py`:
```python
reminder_sent = Column(Boolean, default=False)
```

SQLite migration: `ALTER TABLE users ADD COLUMN reminder_sent BOOLEAN DEFAULT 0`

## Files to Create/Modify

| File | Action | What |
|------|--------|------|
| `backend/app/services/alerting.py` | Modify | Add `send_user_message()`, `send_welcome_message()` |
| `backend/app/routers/user.py` | Modify | Call welcome message in `/register`, add `/admin/send-message` endpoint |
| `backend/app/models/database.py` | Modify | Add `reminder_sent` field to User |
| `api/reminder_function.py` | Create | Azure Function timer for 24h reminders |
| `.claude/commands/send_telega_promo.md` | Create | Slash command for manual broadcast |

## Out of Scope

- Receiving messages from users (webhook/polling)
- Message templates UI
- Segmentation beyond all/active/specific user
- Analytics on message open rates
