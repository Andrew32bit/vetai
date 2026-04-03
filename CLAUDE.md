# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Telegram Mini App for AI-powered pet health diagnosis (Russian + English markets).
Features: photo analysis (skin/eyes/ears + УЗИ/рентген/МРТ), lab results OCR, symptom chat (LLM).
Ответ агента должен быть всегда на русском языке.

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

## Hosting (Azure)
- **Frontend:** Azure Static Web Apps (Free) — salmon-hill-0a38f9b10.1.azurestaticapps.net
- **Backend:** Azure App Service F1 (Free) — vetai-backend.azurewebsites.net
- **Database:** SQLite on App Service disk, backup every 5 min → Azure Cosmos DB (Free 25GB)
- **Old (deprecated):** Render.com (vetai-backend-app.onrender.com), GitHub Pages

## Dashboard Command
When asked for stats/dashboard, fetch from `https://vetai-backend.azurewebsites.net/api/v1/users/admin/stats` (header: admin-key: vetai-admin-2026) and format as: Общее → По дням → Пользователи (with pets, source) → Последние обращения → Продвижение.

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

### Не реализовано
- S3 file upload (фото хранятся только в памяти)
- Telegram initData auth validation
- Payment integration (YooKassa / Telegram Stars)
- Subscription limit enforcement (все на beta tier)
- Реферальная механика
- Push-уведомления

## Important Notes
- **Language:** All UI text and AI responses must be in Russian
- **Telegram SDK:** Always call `WebApp.ready()` and `WebApp.expand()` on load
- **Auth:** Validate Telegram `initData` hash on backend — never trust client-side telegram_id alone
- **ML models:** Torch/PaddleOCR deps are commented out in requirements.txt — uncomment when ready
- **Environment:** Copy `.env.example` to `.env` and fill in real values before running
