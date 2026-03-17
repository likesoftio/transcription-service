# Transcription Service

Монорепа: React-фронтенд + FastAPI-бэкенд для пакетной транскрибации аудио/видео через Deepgram API.

## Возможности

- Drag-and-drop загрузка файлов через веб-интерфейс
- Пакетная обработка через Celery + Redis
- Горизонтальное масштабирование воркеров
- Автоконвертация аудио/видео в WAV через ffmpeg
- Диаризация спикеров, разбивка по фрагментам
- Webhook уведомления + polling API
- Rate limiting для Deepgram API

## Структура

```
transcription-service/
├── backend/                  # FastAPI + Celery
│   ├── app/
│   │   ├── api/              # Endpoints + Pydantic schemas
│   │   ├── core/             # Celery, Deepgram, Redis, ffmpeg
│   │   └── models/           # Domain models
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/       # DropZone, FileList, TaskStatus, TranscriptViewer
│   │   ├── hooks/            # useTranscription
│   │   └── api/              # Typed API client
│   ├── Dockerfile            # Multi-stage: Node build → Nginx
│   └── nginx.conf            # Прокси /api/ → backend
└── docker-compose.yml
```

## Быстрый старт

### 1. Настройка окружения

```bash
cp env.example .env
# Отредактируйте .env — укажите DEEPGRAM_API_KEY
```

### 2. Запуск

```bash
docker-compose up -d
```

Сервисы:
- **Фронтенд:** http://localhost:3000
- **Celery Flower:** http://localhost:5555
- **API (внутренний):** http://localhost:8000

### 3. Масштабирование воркеров

```bash
docker-compose up -d --scale transcription-worker=5
```

## Локальная разработка

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
celery -A app.core.queue worker --loglevel=info --queues=transcription

# Frontend
cd frontend
npm install
npm run dev    # http://localhost:5173, проксирует /api → localhost:8000
```

## API

Все эндпоинты под `/api/v1`:

### POST /transcribe/batch

Загрузка файлов для транскрибации.

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe/batch" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F 'options={"model":"nova-2","language":"ru","diarize":true}'
```

```json
{
  "task_id": "uuid",
  "status": "queued",
  "files_count": 2,
  "files": [{"file_id": "...", "filename": "audio1.wav", "status": "queued"}]
}
```

### GET /transcribe/status/{task_id}

```json
{
  "task_id": "uuid",
  "status": "processing",
  "progress": {"total": 2, "completed": 1, "failed": 0, "processing": 1, "queued": 0},
  "files": [...]
}
```

### GET /transcribe/result/{file_id}

Результат транскрибации файла (transcript, speakers_transcript, chunks_transcript).

### POST /webhook/register

Регистрация webhook URL для уведомлений о завершении.

### GET /health

Health check + количество активных воркеров.

## Конфигурация

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DEEPGRAM_API_KEY` | API ключ Deepgram | — |
| `CELERY_BROKER_URL` | Redis URL (брокер) | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis URL (результаты) | `redis://redis:6379/1` |
| `STORAGE_TTL_HOURS` | Время хранения результатов | `24` |
| `MAX_FILE_SIZE_MB` | Макс. размер файла | `100` |
| `MAX_FILES_PER_BATCH` | Макс. файлов в пакете | `50` |
| `CELERY_TASK_RATE_LIMIT` | Rate limit задач | `10/m` |
| `DEFAULT_MODEL` | Модель Deepgram | `nova-2` |
| `DEFAULT_LANGUAGE` | Язык транскрибации | `ru` |
| `FRONTEND_PORT` | Порт фронтенда | `3000` |

## Поддерживаемые форматы

**Аудио:** mp3, wav, flac, aac, ogg, opus, m4a, webm, pcm, mp2, amr, 3gp, wma

**Видео:** mp4, mov, avi, wmv, flv, mkv, mpeg, mpg
