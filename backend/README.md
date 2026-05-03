---
title: VetAI Backend
emoji: 🐾
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
short_description: AI vet assistant backend (FastAPI + Groq + Claude fallback)
---

# VetAI Backend

FastAPI backend for the VetAI Telegram Mini App — AI-powered pet health diagnosis.

- Chat: Groq Llama 3.3 70B → Claude Sonnet fallback
- Photo / lab OCR: Groq Llama 4 Scout → Claude Vision fallback
- DB: SQLite, auto-backup to `kombatDrew/vetai-data` HF Dataset every 5 min
