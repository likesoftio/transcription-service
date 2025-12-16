# Transcription Microservice

Микросервис для пакетной транскрибации аудиофайлов с использованием Deepgram API.

## Возможности

- Пакетная загрузка файлов через multipart/form-data
- Асинхронная обработка через Celery
- Поддержка множественных воркеров для горизонтального масштабирования
- Webhook уведомления о завершении транскрибации
- Polling API для проверки статуса задач
- Rate limiting для контроля нагрузки на Deepgram API

## Архитектура

```
API (FastAPI) → Redis Queue → Celery Workers → Deepgram API
```

## Быстрый старт

### 1. Настройка окружения

Создайте `.env` файл:

```env
DEEPGRAM_API_KEY=your_api_key_here
REDIS_HOST=redis
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
STORAGE_TTL_HOURS=24
MAX_FILE_SIZE_MB=100
MAX_FILES_PER_BATCH=50
CELERY_WORKER_CONCURRENCY=3
CELERY_TASK_RATE_LIMIT=10/m
```

### 2. Запуск через Docker Compose

```bash
cd transcription-service
docker-compose up -d
```

Это запустит:
- API сервер на порту 8000
- Redis
- 3 Celery воркера
- Celery Flower (мониторинг) на порту 5555

### 3. Масштабирование воркеров

Для запуска большего количества воркеров:

```bash
# Фиксированное количество
docker-compose up -d transcription-worker-1 transcription-worker-2 transcription-worker-3

# Или через scale (если используете один сервис)
docker-compose up -d --scale transcription-worker=5
```

## API Endpoints

### POST /api/v1/transcribe/batch

Загрузка файлов для транскрибации.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/transcribe/batch" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F 'options={"model":"nova-2","language":"ru","diarize":true}' \
  -F "webhook_url=https://example.com/webhook"
```

**Response:**
```json
{
  "task_id": "uuid-here",
  "status": "queued",
  "files_count": 2,
  "files": [
    {
      "file_id": "file-uuid-1",
      "filename": "audio1.wav",
      "status": "queued"
    }
  ],
  "estimated_completion_time": "2025-12-16T20:00:00Z"
}
```

### GET /api/v1/transcribe/status/{task_id}

Проверка статуса задачи.

**Response:**
```json
{
  "task_id": "uuid-here",
  "status": "processing",
  "progress": {
    "total": 2,
    "completed": 1,
    "failed": 0,
    "processing": 1,
    "queued": 0
  },
  "files": [...],
  "created_at": "2025-12-16T19:00:00Z",
  "updated_at": "2025-12-16T19:05:00Z"
}
```

### GET /api/v1/transcribe/result/{file_id}

Получение результата транскрибации конкретного файла.

### POST /api/v1/webhook/register

Регистрация webhook URL для уведомлений.

### GET /api/v1/health

Health check с информацией о количестве активных воркеров.

## Мониторинг

- **Celery Flower:** http://localhost:5555
- **Health Check:** http://localhost:8000/api/v1/health

## Конфигурация

Все настройки через переменные окружения (см. `.env` пример выше).

## Разработка

### Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск API
uvicorn app.main:app --reload

# Запуск воркера (в отдельном терминале)
celery -A app.core.queue worker --loglevel=info --queues=transcription
```

## Интеграция с основным приложением

Основное приложение может вызывать микросервис через HTTP API вместо прямого использования Deepgram SDK.

