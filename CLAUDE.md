# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Telegram Mini App for AI-powered pet health diagnosis (Russian + English markets).
Features: photo analysis (skin/eyes/ears + УЗИ/рентген/МРТ), lab results OCR, symptom chat (LLM).
Ответ агента должен быть всегда на русском языке.

## Knowledge Base (Obsidian)
Мозги проекта (стратегия, сессии, контент-план, архитектура, статус) лежат в Obsidian:
- **Vault:** `/Users/andrewk/Documents/Obsidian Vault`
- **Проектная папка:** `projects/VetAI/` (стратегия продвижения, статус реализации, стек, архитектура, сессии, контент-план канала, обзор) + `projects/VetAI/Pro/` (про-версия)
- Перед стратегическими/продуктовыми решениями или вопросами «что планировали / в каком статусе» — сначала смотри сюда, потом в код. Используй skill `obsidian:obsidian-cli` / `obsidian:obsidian-markdown` для чтения и правок.

## Telegram Bot
- **Bot:** @vetai_app_bot (ID: 8517858349)
- **Mini App:** Telegram Mini App через @vetai_app_bot
- **Канал:** @vetai_channel (для маркетинга)

## Tech Stack
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy (async) + SQLite
- **Frontend:** React 18 + Vite + Tailwind CSS + @twa-dev/sdk (Telegram Mini App)
- **AI Chat:** Groq (Llama 3.3 70B) → Claude Sonnet fallback при 429
- **AI Vision:** Groq (Llama 4 Scout) → Claude Vision fallback при 429
- **i18n:** Auto-detect from Telegram language_code (ru/en)

## Hosting
- **Backend:** Hugging Face Spaces (Free) — https://kombatdrew-vetai-backend.hf.space (Docker, порт 7860)
- **Frontend:** GitHub Pages — https://andrew32bit.github.io/vetai/ (BASE_PATH=`/vetai/`, деплой через `.github/workflows/deploy-frontend.yml`)
- **Database:** SQLite на диске HF Space (persistent storage)
- **Telegram webhook:** `https://kombatdrew-vetai-backend.hf.space/webhook`
- **Old (deprecated):** Azure App Service (vetai-backend.azurewebsites.net), Azure Static Web Apps, Render.com

## Dashboard Command
When asked for stats/dashboard, fetch from `https://kombatdrew-vetai-backend.hf.space/api/v1/users/admin/stats` (header: admin-key: vetai-admin-2026) and format as: Общее → По дням → Пользователи (with pets, source) → Последние обращения → Продвижение.

## Commands

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install
npm run dev    # → http://localhost:5173

# Docker
docker build -t vetai-backend ./backend
docker run -p 8000:8000 --env-file .env vetai-backend
```

## Architecture

### Backend (FastAPI)

Layered async-first architecture:

```
Routers (/api/v1/*)  →  Services  →  ML/Claude  →  DB Models
```

- **Config** (`app/config.py`): Pydantic settings from `.env`, `@lru_cache` singleton via `get_settings()`
- **Routers** (`app/routers/`): API endpoints — `user.py`, `diagnosis.py`, `chat.py`, `health.py`
- **Services** (`app/services/hf_service.py`): Groq + Claude fallback — `get_chat_response()`, `analyze_photo()`, `interpret_lab_results_image()`. Автоматическое переключение Groq→Claude при rate limit (429). Трекинг провайдера в `last_provider`.
- **Services** (`app/services/claude_service.py`): Прямой Claude API wrapper (не используется в основном потоке)
- **Services** (`app/services/usage_limiter.py`): Лимит запросов на пользователя (10/день), трекинг провайдера (groq/claude)
- **ML** (`app/ml/`): `photo_classifier.py` (EfficientNet-B4 заглушка), `ocr_service.py` (PaddleOCR/Tesseract заглушка)
- **Models** (`app/models/database.py`): All SQLAlchemy models — `User`, `Pet`, `Diagnosis`, `ChatSession`, `UsageLog`, `Feedback`

Auth: Telegram `x-telegram-id` header (initData hash validation not yet implemented).
API versioning: all routes under `/api/v1/`.

### Frontend (React + Telegram Mini App)

- **Entry** (`src/App.jsx`): Calls `WebApp.ready()` + `WebApp.expand()`, routes based on onboarding state in localStorage
- **Pages** (`src/pages/`): `OnboardingPage` (4-step flow), `HomePage`, `PhotoUploadPage`, `LabResultsPage`, `ChatPage`, `HistoryPage`
- **Components** (`src/components/`): `BottomNav` — 5-tab navigation
- **State**: localStorage for user persistence; Zustand installed but not yet used
- **API calls**: `fetch()` to `VITE_API_URL` (default `http://localhost:8000`), telegram ID sent via `x-telegram-id` header (hardcoded `"12345"` in dev)
- **Styling**: Tailwind with custom Telegram theme colors (`tg-blue`, `tg-bg`, etc.) mapped to CSS variables

### Database Schema

`User` → has many `Pet`, has many `Diagnosis`, has many `ChatSession`.
Subscription tiers: free (3 checks/mo), monthly (99₽), annual (1000₽).
JSON columns for flexible data: `result_json`, `messages_json`.

## Implementation Status

### Работает
- Chat (Groq Llama 70B + Claude Sonnet fallback) — ветеринарный чат с русскими метками (низкая/средняя/высокая/экстренная)
- Photo diagnosis (Groq Llama Scout + Claude Vision fallback) — анализ фото с конкретным диагнозом
- Lab results OCR (Groq Vision + Claude Vision fallback) — расшифровка анализов из фото/PDF
- Usage limiter (10 запросов/день) с трекингом провайдера
- Admin stats endpoint (/api/v1/users/admin/stats)
- DB operations (user auth, diagnosis save, usage logging)
- Все метки на русском (не_животное, здоров, низкая/средняя/высокая/экстренная)
- **Admin key вынесен в env** `ADMIN_KEY` (secrets.compare_digest, fail-closed) — не хардкод
- **Product-аналитика** — `POST /api/v1/analytics/events` (app_open, onboarding, ai_start/success/failure, invite/share, referral_landed), admin-воронка `GET /api/v1/analytics/funnel` (DAU/WAU/активация/ретеншн/рефералы), публичный `GET /api/v1/analytics/public-stats` (trust-бейдж)
- **Реферальная механика** — deep-link `?startapp=ref_<id>`, награда +5 запросов/день рефереру (кап 50), идемпотентно; инвайт-карточка на Home + шаринг результата
- **Ретеншн** — daily-usage streak (бейдж на Home) + фоновая задача напоминаний (`REMINDERS_ENABLED`, по умолчанию off)

### Не реализовано
- S3 file upload (фото хранятся только в памяти)
- Telegram initData auth validation (HMAC-подпись) — **критично**, см. [[Due Diligence 2026-07]]
- Payment integration (YooKassa / Telegram Stars)
- Subscription limit enforcement (все на beta tier)
- Push-уведомления (кроме re-engagement reminders)

## Important Notes
- **Language:** All UI text and AI responses must be in Russian
- **Telegram SDK:** Always call `WebApp.ready()` and `WebApp.expand()` on load
- **Auth:** Validate Telegram `initData` hash on backend — never trust client-side telegram_id alone
- **ML models:** Torch/PaddleOCR deps are commented out in requirements.txt — uncomment when ready
- **Environment:** Copy `.env.example` to `.env` and fill in real values before running
