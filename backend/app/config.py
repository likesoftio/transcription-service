"""Configuration for transcription microservice."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Deepgram API
    DEEPGRAM_API_KEY: str = os.getenv('DEEPGRAM_API_KEY', '')
    
    # Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    CELERY_BROKER_URL: str = os.getenv('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
    CELERY_RESULT_BACKEND: str = os.getenv('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')
    
    # Storage
    STORAGE_TTL_HOURS: int = int(os.getenv('STORAGE_TTL_HOURS', '24'))
    
    # File limits
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    MAX_FILES_PER_BATCH: int = int(os.getenv('MAX_FILES_PER_BATCH', '50'))
    
    # Webhook
    WEBHOOK_TIMEOUT_SECONDS: int = int(os.getenv('WEBHOOK_TIMEOUT_SECONDS', '30'))
    
    # Celery workers
    CELERY_WORKER_CONCURRENCY: int = int(os.getenv('CELERY_WORKER_CONCURRENCY', '3'))
    CELERY_TASK_RATE_LIMIT: str = os.getenv('CELERY_TASK_RATE_LIMIT', '10/m')
    
    # Transcription options
    DEFAULT_MODEL: str = os.getenv('DEFAULT_MODEL', 'nova-2')
    DEFAULT_LANGUAGE: str = os.getenv('DEFAULT_LANGUAGE', 'ru')
    DEFAULT_CHUNK_DURATION: float = float(os.getenv('DEFAULT_CHUNK_DURATION', '30.0'))
    
    # API
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    class Config:
        env_file = '.env'
        case_sensitive = True


settings = Settings()

ALLOWED_EXTENSIONS = {
    # Audio
    ".mp3", ".mp4", ".mp2", ".aac", ".wav", ".flac", ".pcm",
    ".m4a", ".ogg", ".opus", ".webm", ".amr", ".3gp", ".wma",
    # Video (ffmpeg will extract audio track)
    ".mov", ".avi", ".wmv", ".flv", ".mkv", ".mpeg", ".mpg",
}

