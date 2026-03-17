# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Monorepo** with backend + frontend for an audio transcription microservice.

- **Backend:** FastAPI + Celery + Redis + Deepgram SDK. Accepts batch audio files via HTTP, queues them for async transcription via Deepgram API, stores results in Redis, and supports polling or webhook-based result retrieval. Russian-language focused (default language: `ru`).
- **Frontend:** React + TypeScript + Vite. Dark-themed UI for uploading files, monitoring progress, and viewing transcription results.

Part of the larger `calls-assistant` system — the main app toggles between direct Deepgram SDK usage and this microservice via `USE_TRANSCRIPTION_MICROSERVICE` env flag.

## Commands

```bash
# ── Backend ──
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
celery -A app.core.queue worker --loglevel=info --queues=transcription

# ── Frontend ──
cd frontend
npm install
npm run dev          # dev server at http://localhost:5173 (proxies /api to backend)
npm run build        # production build to dist/

# ── Docker (full stack: frontend + API + Redis + 3 workers + Flower) ──
docker-compose up -d
docker-compose logs -f transcription-worker-1

# Scale workers
docker-compose up -d --scale transcription-worker=5

# Manual integration test (requires running services)
cd backend && python test_api.py

# Celery Flower monitoring UI → http://localhost:5555
# Frontend → http://localhost:3000
# Backend API → http://localhost:8000
```

No pytest/unittest framework — `backend/test_api.py` is a manual integration script that hits live endpoints.

## Architecture

```
Browser → Nginx (frontend, port 3000) → /api/* proxy → FastAPI (port 8000)
                                                             ↓
                                                       Redis Queue (Celery broker, DB 0)
                                                             ↓
                                                       Celery Workers (stateless, horizontally scalable)
                                                             ↓
                                                       Deepgram API (remote transcription)
                                                             ↓
                                                       Redis (result backend, DB 1, TTL-based cleanup)
```

**Request flow:** POST files to `/api/v1/transcribe/batch` → get `task_id` immediately → poll `/api/v1/transcribe/status/{task_id}` or register webhook.

**Backend key modules (`backend/app/`):**
- `api/routes.py` — API endpoints (batch transcribe, status, results, webhook registration, health)
- `api/schemas.py` — Pydantic request/response models
- `core/queue.py` — Celery app creation and configuration (broker, routing, rate limits)
- `core/tasks.py` — Celery tasks (`transcribe_file_task`, `send_webhook_notification`); custom `TranscriptionTask` base class with `on_failure` handler; max 3 retries, 60s delay
- `core/storage.py` — Redis persistence layer (task metadata as Hash, file list as Set, results as String); singleton via `get_storage()`
- `core/transcription.py` — Deepgram SDK wrapper (`TranscriptionService`); handles utterance parsing, speaker diarization, chunked transcripts; singleton via `get_transcription_service()`
- `core/converter.py` — ffmpeg wrapper, converts any audio/video to WAV (PCM 16-bit, 16kHz, mono)
- `models/task.py` — Domain models (`TranscriptionTask`, `FileInfo`, `FileStatus`, `TaskStatus`); task auto-updates status based on child file states
- `config.py` — pydantic-settings `Settings` class, loads from `.env`

**Frontend key modules (`frontend/src/`):**
- `components/` — DropZone, FileList, ProgressBar, TaskStatus, TranscriptViewer
- `hooks/useTranscription.ts` — state management, upload via XHR, polling
- `api/client.ts` — typed API client
- `types.ts` — TypeScript interfaces

**Audio data is base64-encoded** when passed through Celery (JSON serialization constraint).

**Redis key patterns:**
- `task:{task_id}` — Hash with task metadata
- `task:{task_id}:files` — Set of file IDs
- `file:{file_id}:result` — JSON string with transcription result

## API Endpoints

All prefixed with `/api/v1`:
- `GET /health` — health check with worker count
- `POST /transcribe/batch` — submit files (multipart), returns task_id + file_ids
- `GET /transcribe/status/{task_id}` — task progress with file statuses/results
- `GET /transcribe/result/{file_id}` — single file transcription result
- `POST /webhook/register` — register webhook URL for completion notifications

## Key Configuration (env vars)

- `DEEPGRAM_API_KEY` — required for transcription
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Redis URLs (DB 0 / DB 1)
- `STORAGE_TTL_HOURS=24` — result retention
- `MAX_FILE_SIZE_MB=100`, `MAX_FILES_PER_BATCH=50`
- `CELERY_TASK_RATE_LIMIT=10/m`
- `DEFAULT_MODEL=nova-2`, `DEFAULT_LANGUAGE=ru`
- `FRONTEND_PORT=3000` — frontend exposed port
