# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Telegram Mini App for AI-powered pet health diagnosis (Russian market).
Three core features: photo analysis (CV), lab results OCR, symptom chat (LLM).
Ответ агента должен быть всегда на русском языке.

## Tech Stack
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy (async) + SQLite (dev) / PostgreSQL (prod)
- **Frontend:** React 18 + Vite + Tailwind CSS + @twa-dev/sdk (Telegram Mini App)
- **ML:** EfficientNet-B4 (photo classification), PaddleOCR (lab results), Claude API (chat)
- **Storage:** Yandex Cloud S3 for uploads
- **Deployment:** Docker → Yandex Cloud

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
- **Services** (`app/services/claude_service.py`): Anthropic SDK wrapper — `get_chat_response()` and `interpret_lab_results()`
- **ML** (`app/ml/`): `photo_classifier.py` (EfficientNet-B4 singleton), `ocr_service.py` (PaddleOCR/Tesseract singleton)
- **Models** (`app/models/database.py`): All SQLAlchemy models in one file — `User`, `Pet`, `Diagnosis`, `ChatSession`

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

Most endpoints and ML services are **stubs/placeholders** with TODO markers. Key unimplemented pieces:
- DB operations (no actual inserts/queries in routers yet)
- S3 file upload
- CV model inference & OCR extraction
- Telegram initData auth validation
- Payment integration (YooKassa / Telegram Stars)
- Subscription limit enforcement

## Important Notes
- **Language:** All UI text and AI responses must be in Russian
- **Telegram SDK:** Always call `WebApp.ready()` and `WebApp.expand()` on load
- **Auth:** Validate Telegram `initData` hash on backend — never trust client-side telegram_id alone
- **ML models:** Torch/PaddleOCR deps are commented out in requirements.txt — uncomment when ready
- **Environment:** Copy `.env.example` to `.env` and fill in real values before running
