"""Celery tasks for transcription."""
import logging
import httpx
from celery import Task
from app.core.queue import celery_app
from app.core.transcription import TranscriptionService
from app.core.converter import convert_to_wav
from app.core.storage import get_storage
from app.config import settings

logger = logging.getLogger(__name__)

# Global transcription service instance
_transcription_service: TranscriptionService = None


def get_transcription_service() -> TranscriptionService:
    """Get or create transcription service instance."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service


def _is_retryable_error(exc: Exception) -> bool:
    """Check if an error is retryable (not a permanent client error)."""
    exc_str = str(exc).lower()
    # Non-retryable: auth errors, bad request, forbidden
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status in (400, 401, 403):
            return False
    for code in ('400', '401', '403', 'unauthorized', 'forbidden', 'invalid api key'):
        if code in exc_str:
            return False
    return True


class TranscriptionTask(Task):
    """Custom task class with error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        file_id = kwargs.get('file_id') if kwargs else None
        task_id_db = kwargs.get('task_id') if kwargs else None

        if file_id and task_id_db:
            try:
                storage = get_storage()
                storage.update_file_status(
                    task_id_db,
                    file_id,
                    'failed',
                    str(exc)
                )
                logger.error(f"Task {task_id} failed for file {file_id}: {exc}")
            except Exception as e:
                logger.error(f"Failed to update status for file {file_id}: {e}")


@celery_app.task(
    bind=True,
    base=TranscriptionTask,
    name='app.core.tasks.transcribe_file_task',
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def transcribe_file_task(
    self,
    task_id: str,
    file_id: str,
    file_path: str,
    filename: str,
    options: dict,
    audio_data_base64: str = None,
) -> bool:
    """
    Transcribe a single file.

    Args:
        task_id: Task ID
        file_id: File ID
        file_path: Path to uploaded file on shared volume
        filename: Original filename
        options: Transcription options
        audio_data_base64: (deprecated) base64-encoded audio data

    Returns:
        True if successful, False otherwise
    """
    import os

    storage = get_storage()

    try:
        # Update status to processing
        storage.update_file_status(task_id, file_id, 'processing')

        # Read audio data from file
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            # Clean up uploaded file
            os.unlink(file_path)
        elif audio_data_base64:
            import base64
            audio_data = base64.b64decode(audio_data_base64)
        else:
            raise FileNotFoundError(f"Upload file not found: {file_path}")

        # Convert to WAV via ffmpeg
        audio_data = convert_to_wav(audio_data, filename)

        # Get transcription service
        transcription_service = get_transcription_service()
        
        # Transcribe file
        result = transcription_service.transcribe(
            audio_data=audio_data,
            filename=filename,
            model=options.get('model', settings.DEFAULT_MODEL),
            language=options.get('language', settings.DEFAULT_LANGUAGE),
            chunk_duration=options.get('chunk_duration', settings.DEFAULT_CHUNK_DURATION),
            diarize=options.get('diarize', True)
        )
        
        if not result:
            storage.update_file_status(task_id, file_id, 'failed', 'Transcription returned no results')
            return False
        
        # Save result
        storage.save_file_result(task_id, file_id, result, filename=filename)
        
        # Update file info with result
        task = storage.get_task(task_id)
        if task:
            file_info = task.get_file(file_id)
            if file_info:
                from app.models.task import FileStatus
                file_info.result = result
                file_info.status = FileStatus.COMPLETED
                storage.save_task(task)
        
        # Update status to completed
        storage.update_file_status(task_id, file_id, 'completed')
        
        # Check if task is complete and send webhook if needed
        task = storage.get_task(task_id)
        if task:
            task.update_status()
            storage.save_task(task)
            
            # Send webhook if task is complete and webhook URL is set
            if task.status.value in ['completed', 'failed'] and task.webhook_url:
                send_webhook_notification.delay(task_id, task.status.value)
        
        logger.info(f"Successfully transcribed file {file_id}: {filename}")
        return True
        
    except Exception as exc:
        logger.error(f"Error in transcribe_file_task for file {file_id}: {exc}", exc_info=True)

        # Update status to error
        try:
            storage.update_file_status(task_id, file_id, 'failed', str(exc))
        except Exception as e:
            logger.error(f"Failed to update error status: {e}")

        # Check if task is complete and send webhook if needed
        task = storage.get_task(task_id)
        if task:
            task.update_status()
            storage.save_task(task)

            if task.status.value == 'failed' and task.webhook_url:
                send_webhook_notification.delay(task_id, 'failed')

        # Only retry retryable errors
        if _is_retryable_error(exc):
            raise self.retry(exc=exc)
        raise


@celery_app.task(name='app.core.tasks.send_webhook_notification')
def send_webhook_notification(task_id: str, status: str):
    """
    Send webhook notification about task completion.
    
    Args:
        task_id: Task ID
        status: Task status (completed or failed)
    """
    storage = get_storage()
    task = storage.get_task(task_id)
    
    if not task or not task.webhook_url:
        return
    
    try:
        # Prepare webhook payload
        task_dict = task.to_dict()
        payload = {
            'task_id': task_id,
            'status': status,
            'progress': task_dict['progress'],
            'timestamp': task_dict['updated_at'],
        }
        
        # Send webhook
        with httpx.Client(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
            response = client.post(task.webhook_url, json=payload)
            response.raise_for_status()
        
        logger.info(f"Webhook notification sent for task {task_id}")
    except Exception as e:
        logger.error(f"Failed to send webhook for task {task_id}: {e}", exc_info=True)

