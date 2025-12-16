# Quick Start Guide

## Быстрый запуск микросервиса транскрибации

### 1. Настройка окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cd transcription-service
cp .env.example .env
# Отредактируйте .env и укажите DEEPGRAM_API_KEY
```

### 2. Запуск через Docker Compose

```bash
docker-compose up -d
```

Это запустит:
- **API сервер:** http://localhost:8000
- **Redis:** порт 6379
- **3 Celery воркера:** для обработки задач
- **Celery Flower:** http://localhost:5555 (мониторинг)

### 3. Проверка работоспособности

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Должен вернуть:
# {"status":"ok","timestamp":"...","workers_active":3}
```

### 4. Тестовая транскрибация

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe/batch" \
  -F "files=@test_audio.wav" \
  -F 'options={"model":"nova-2","language":"ru","diarize":true}'
```

Ответ:
```json
{
  "task_id": "uuid-here",
  "status": "queued",
  "files_count": 1,
  "files": [...]
}
```

### 5. Проверка статуса

```bash
curl http://localhost:8000/api/v1/transcribe/status/{task_id}
```

### 6. Масштабирование воркеров

Для обработки больших объемов запустите больше воркеров:

```bash
# Добавить еще 2 воркера
docker-compose up -d transcription-worker-1 transcription-worker-2 transcription-worker-3

# Или использовать scale (если настроен)
docker-compose up -d --scale transcription-worker=5
```

### 7. Мониторинг

- **API Health:** http://localhost:8000/api/v1/health
- **Celery Flower:** http://localhost:5555
- **Логи воркеров:** `docker-compose logs -f transcription-worker-1`

## Интеграция с основным приложением

В основном приложении добавьте в `.env`:

```env
USE_TRANSCRIPTION_MICROSERVICE=true
TRANSCRIPTION_SERVICE_URL=http://transcription-api:8000
```

Основное приложение автоматически будет использовать микросервис вместо прямого вызова Deepgram SDK.

