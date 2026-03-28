# VetAI Telegram Mini App — Deploy Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Задеплоить VetAI как Telegram Mini App — backend на Yandex Cloud (Docker), frontend на CDN, бот в BotFather.

**Architecture:** Backend (FastAPI) в Docker-контейнере на Yandex Compute Instance за Nginx reverse proxy с Let's Encrypt SSL. Frontend (React) — статика, раздаётся тем же Nginx. Telegram бот регистрируется через BotFather, Mini App URL указывает на фронтенд.

**Tech Stack:** Docker, Docker Compose, Nginx, Let's Encrypt (certbot), Yandex Cloud CLI (yc), GitHub, BotFather.

**Текущее состояние:** Приложение работает локально. Онбординг, главная, чат, фото, анализы, история — все экраны рендерятся. Backend API роуты зарегистрированы (стабы). Нет: git-репо, .env, docker-compose, nginx, CI/CD.

---

## File Structure

### Create:
- `.env` — реальные переменные окружения (не коммитится)
- `docker-compose.yml` — оркестрация backend + nginx
- `nginx/nginx.conf` — reverse proxy + SSL + статика фронтенда
- `nginx/conf.d/vetai.conf` — server block для приложения
- `frontend/Dockerfile` — билд фронтенда для продакшна
- `.github/workflows/deploy.yml` — CI/CD pipeline

### Modify:
- `backend/app/main.py` — добавить инициализацию БД при старте
- `backend/app/models/database.py` — добавить `init_db()` для создания таблиц
- `backend/requirements.txt` — раскомментировать/добавить gunicorn
- `frontend/vite.config.js` — проверить base path для CDN

---

## Task 1: Инициализация Git-репозитория

**Files:**
- Create: `.git/` (via git init)

- [ ] **Step 1: Инициализировать git-репо**

```bash
cd /Users/andrewk/VsCode_projects/vetai
git init
```

- [ ] **Step 2: Первый коммит**

```bash
git add -A
git commit -m "feat: initial VetAI project — FastAPI backend + React Telegram Mini App"
```

- [ ] **Step 3: Создать GitHub-репозиторий и push**

```bash
gh repo create vetai --private --source=. --push
```

---

## Task 2: Создать .env файл с реальными значениями

**Files:**
- Create: `.env`

- [ ] **Step 1: Скопировать .env.example в .env**

```bash
cp .env.example .env
```

- [ ] **Step 2: Заполнить реальные значения**

Пользователь должен заполнить:
- `TELEGRAM_BOT_TOKEN` — получить у @BotFather (Task 7)
- `CLAUDE_API_KEY` — ключ от Anthropic
- `S3_ACCESS_KEY` / `S3_SECRET_KEY` — из Yandex Cloud Console
- `DATABASE_URL` — для прода: `postgresql+asyncpg://user:pass@db:5432/vetai`

- [ ] **Step 3: Проверить что .env в .gitignore**

```bash
grep "^\.env$" .gitignore
```
Expected: `.env` найден в .gitignore.

---

## Task 3: Добавить инициализацию БД при старте бэкенда

**Files:**
- Modify: `backend/app/models/database.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Добавить async init_db() в database.py**

В конец файла `backend/app/models/database.py` добавить:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

engine = create_async_engine(get_settings().DATABASE_URL, echo=get_settings().DEBUG)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with async_session() as session:
        yield session
```

- [ ] **Step 2: Подключить init_db() в main.py startup**

В `backend/app/main.py` заменить startup:

```python
@app.on_event("startup")
async def startup():
    from app.models.database import init_db
    await init_db()
```

- [ ] **Step 3: Проверить что бэкенд стартует**

```bash
cd backend && source .venv/bin/activate
python -c "from app.main import app; print('OK')"
```

- [ ] **Step 4: Коммит**

```bash
git add backend/app/models/database.py backend/app/main.py
git commit -m "feat: add async DB initialization on startup"
```

---

## Task 4: Добавить gunicorn в зависимости бэкенда

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Добавить gunicorn + asyncpg в requirements.txt**

Добавить в секцию Core:
```
gunicorn==23.0.0
asyncpg==0.30.0         # PostgreSQL async driver (prod)
```

- [ ] **Step 2: Обновить CMD в Dockerfile для production**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

- [ ] **Step 3: Проверить Docker-билд**

```bash
cd /Users/andrewk/VsCode_projects/vetai
docker build -t vetai-backend ./backend
```

- [ ] **Step 4: Коммит**

```bash
git add backend/requirements.txt backend/Dockerfile
git commit -m "feat: add gunicorn + asyncpg, update Dockerfile for production"
```

---

## Task 5: Frontend Dockerfile + production build

**Files:**
- Create: `frontend/Dockerfile`

- [ ] **Step 1: Создать multi-stage Dockerfile для фронтенда**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

- [ ] **Step 2: Проверить билд**

```bash
cd /Users/andrewk/VsCode_projects/vetai
docker build -t vetai-frontend ./frontend
```

- [ ] **Step 3: Коммит**

```bash
git add frontend/Dockerfile
git commit -m "feat: add frontend production Dockerfile"
```

---

## Task 6: Docker Compose + Nginx

**Files:**
- Create: `docker-compose.yml`
- Create: `nginx/vetai.conf`

- [ ] **Step 1: Создать nginx/vetai.conf**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (static files)
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check proxy
    location /health {
        proxy_pass http://backend:8000;
    }

    # Docs proxy (dev only, remove in prod)
    location /docs {
        proxy_pass http://backend:8000;
    }
    location /openapi.json {
        proxy_pass http://backend:8000;
    }
}
```

- [ ] **Step 2: Создать docker-compose.yml**

```yaml
services:
  backend:
    build: ./backend
    env_file: .env
    restart: always
    expose:
      - "8000"
    volumes:
      - db-data:/app/data

  frontend:
    build: ./frontend
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/vetai.conf:/etc/nginx/conf.d/default.conf
      - ./certbot/www:/var/www/certbot
      - ./certbot/conf:/etc/letsencrypt
    depends_on:
      - backend

volumes:
  db-data:
```

- [ ] **Step 3: Проверить docker compose up**

```bash
cd /Users/andrewk/VsCode_projects/vetai
docker compose up --build -d
curl -s http://localhost/health
curl -s http://localhost/ | head -5
docker compose down
```

Expected: health отдаёт `{"status":"ok","service":"vetai"}`, главная отдаёт HTML.

- [ ] **Step 4: Коммит**

```bash
git add docker-compose.yml nginx/
git commit -m "feat: add docker-compose + nginx reverse proxy"
```

---

## Task 7: Регистрация Telegram бота и Mini App

**Ручной шаг — выполняет пользователь в Telegram.**

- [ ] **Step 1: Создать бота в @BotFather**

В Telegram написать @BotFather:
```
/newbot
Имя: VetAI - AI Ветеринар
Username: vetai_app_bot (или другой свободный)
```
Скопировать полученный токен в `.env` → `TELEGRAM_BOT_TOKEN`.

- [ ] **Step 2: Настроить бота**

В @BotFather:
```
/setdescription — AI-ветеринар: диагностика по фото, расшифровка анализов, чат с AI
/setabouttext — Проверьте здоровье питомца за 30 секунд
/setuserpic — загрузить иконку 640x640 PNG
/setcommands — start - Открыть приложение
```

- [ ] **Step 3: Создать Mini App**

В @BotFather:
```
/newapp
Выбрать бота → vetai_app_bot
Название: VetAI
Описание: AI-ветеринар
URL: https://your-domain.com (ваш реальный домен с HTTPS)
```

- [ ] **Step 4: Добавить кнопку Mini App в чат**

В @BotFather:
```
/setmenubutton
Выбрать бота → vetai_app_bot
URL: https://your-domain.com
Text: Открыть VetAI
```

- [ ] **Step 5: Обновить .env**

```
TELEGRAM_BOT_TOKEN=<token от BotFather>
TELEGRAM_WEBAPP_URL=https://your-domain.com
```

А также в фронтенде:
```
VITE_API_URL=https://your-domain.com
```

---

## Task 8: Деплой на Yandex Cloud

**Files:**
- No new files (инфраструктурные команды)

- [ ] **Step 1: Установить и настроить yc CLI**

```bash
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
yc init
```

Пользователь проходит интерактивную настройку (OAuth, cloud ID, folder ID).

- [ ] **Step 2: Создать VM**

```bash
yc compute instance create \
  --name vetai-prod \
  --zone ru-central1-a \
  --cores 2 --memory 4 \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-22-04-lts,size=30 \
  --ssh-key ~/.ssh/id_rsa.pub \
  --nat
```

Запомнить внешний IP из вывода.

- [ ] **Step 3: Настроить DNS**

Привязать домен (A-запись) к внешнему IP VM.

- [ ] **Step 4: Подготовить сервер**

```bash
ssh ubuntu@<VM_IP>

# Установить Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker ubuntu
newgrp docker

# Установить certbot
sudo apt-get install -y certbot
```

- [ ] **Step 5: Клонировать репо и создать .env**

```bash
ssh ubuntu@<VM_IP>
git clone https://github.com/<username>/vetai.git
cd vetai
cp .env.example .env
nano .env  # заполнить реальные значения
```

- [ ] **Step 6: Получить SSL-сертификат**

```bash
sudo certbot certonly --standalone -d your-domain.com
```

Обновить `nginx/vetai.conf` — добавить SSL:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://backend:8000;
    }
}
```

- [ ] **Step 7: Запустить docker compose**

```bash
cd ~/vetai
docker compose up --build -d
```

- [ ] **Step 8: Верифицировать деплой**

```bash
curl -s https://your-domain.com/health
# Expected: {"status":"ok","service":"vetai"}

curl -s https://your-domain.com/ | head -3
# Expected: <!DOCTYPE html>...
```

---

## Task 9: Smoke-тест в Telegram

- [ ] **Step 1: Открыть бота в Telegram Desktop**

Найти бота по username, нажать START, открыть Mini App через кнопку меню.

- [ ] **Step 2: Проверить онбординг**

Пройти все 4 шага: приветствие → выбор питомца → данные → тариф.

- [ ] **Step 3: Проверить навигацию**

Открыть каждый таб: Главная, Фото, Анализы, Чат, История.

- [ ] **Step 4: Проверить чат**

Отправить сообщение в чат — должен прийти ответ от AI (или stub-ответ если Claude API ещё не подключен).

- [ ] **Step 5: Проверить на мобильном**

Открыть бота в Telegram iOS и Android — Mini App должно корректно отображаться.

---

## Checklist перед публикацией (из devops-agent)

- [ ] Бот отвечает на /start
- [ ] Mini App загружается по HTTPS
- [ ] WebApp.ready() вызывается при загрузке
- [ ] Иконка бота 640x640 PNG
- [ ] Описание бота заполнено (русский)
- [ ] Команды бота зарегистрированы в BotFather
- [ ] Тестирование в Telegram Desktop + iOS + Android
