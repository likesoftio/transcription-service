# Интеграция микросервиса транскрибации

## Обзор

Микросервис транскрибации выделен в отдельный сервис и может использоваться основным приложением через HTTP API.

## Варианты использования

### Вариант 1: Использование микросервиса (рекомендуется)

Основное приложение отправляет файлы в микросервис через HTTP API.

**Преимущества:**
- Горизонтальное масштабирование воркеров
- Независимое развертывание
- Изоляция транскрибации от основной логики

**Настройка:**

1. Добавьте в `.env` основного приложения:
```env
USE_TRANSCRIPTION_MICROSERVICE=true
TRANSCRIPTION_SERVICE_URL=http://transcription-api:8000
```

2. Запустите микросервис:
```bash
cd transcription-service
docker-compose up -d
```

3. Основное приложение автоматически будет использовать микросервис

### Вариант 2: Прямое использование (legacy)

Основное приложение использует Deepgram SDK напрямую.

**Настройка:**

```env
USE_TRANSCRIPTION_MICROSERVICE=false
```

## Архитектура интеграции

```
Main App (queue_processor.py)
    ↓ HTTP POST /api/v1/transcribe/batch
Transcription Microservice API
    ↓ Celery Tasks
Redis Queue
    ↓
Celery Workers (N instances)
    ↓
Deepgram API
```

## API микросервиса

### POST /api/v1/transcribe/batch

Отправка файлов для транскрибации.

**Пример использования из основного приложения:**

```python
from transcription_service_client import TranscriptionServiceClient

client = TranscriptionServiceClient(base_url="http://transcription-api:8000")
result = client.transcribe_files(
    file_paths=["/path/to/audio1.wav", "/path/to/audio2.wav"],
    webhook_url="https://your-app.com/webhook",
    options={"model": "nova-2", "language": "ru"}
)

task_id = result['task_id']
```

### GET /api/v1/transcribe/status/{task_id}

Проверка статуса задачи.

```python
status = client.get_task_status(task_id)
```

### GET /api/v1/transcribe/result/{file_id}

Получение результата транскрибации.

```python
result = client.get_file_result(file_id)
```

## Масштабирование

Для увеличения пропускной способности запустите больше воркеров:

```bash
cd transcription-service
docker-compose up -d --scale transcription-worker=10
```

Или добавьте больше сервисов в docker-compose.yml:
```yaml
transcription-worker-4:
  ...
transcription-worker-5:
  ...
```

## Мониторинг

- **Health Check:** `GET http://transcription-api:8000/api/v1/health`
- **Celery Flower:** `http://localhost:5555` (если запущен)

## Миграция с прямого использования

1. Убедитесь что микросервис запущен и доступен
2. Установите `USE_TRANSCRIPTION_MICROSERVICE=true`
3. Перезапустите основное приложение
4. Проверьте логи - должны быть запросы к микросервису

