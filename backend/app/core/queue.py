"""Celery queue configuration for transcription tasks."""
import logging
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'transcription_service',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.core.tasks'],
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=900,  # 15 minutes max per task (ffmpeg + Deepgram)
    task_soft_time_limit=840,  # 14 minutes soft limit
)

# Task routing and rate limiting
celery_app.conf.task_routes = {
    'app.core.tasks.transcribe_file_task': {'queue': 'transcription'},
}

celery_app.conf.task_annotations = {
    'app.core.tasks.transcribe_file_task': {
        'rate_limit': settings.CELERY_TASK_RATE_LIMIT,
    },
}

logger.info(f"Celery app configured (broker: {settings.CELERY_BROKER_URL})")

