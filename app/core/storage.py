"""Storage for transcription tasks and results."""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import redis
from app.config import settings
from app.models.task import TranscriptionTask

logger = logging.getLogger(__name__)


class Storage:
    """Redis-based storage for transcription tasks."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.ttl_seconds = settings.STORAGE_TTL_HOURS * 3600
        logger.info(f"Storage initialized (TTL: {settings.STORAGE_TTL_HOURS} hours)")
    
    def save_task(self, task: TranscriptionTask) -> None:
        """Save task to storage."""
        try:
            key = f"task:{task.task_id}"
            task_dict = {
                'task_id': task.task_id,
                'status': task.status.value,
                'webhook_url': task.webhook_url,
                'options': json.dumps(task.options),
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat(),
                'error': task.error,
            }
            
            # Save task metadata
            self.redis_client.hset(key, mapping=task_dict)
            self.redis_client.expire(key, self.ttl_seconds)
            
            # Save files list
            files_key = f"task:{task.task_id}:files"
            files_data = []
            for file_info in task.files:
                files_data.append(json.dumps({
                    'file_id': file_info.file_id,
                    'filename': file_info.filename,
                    'status': file_info.status.value,
                    'error': file_info.error,
                }))
            
            if files_data:
                self.redis_client.sadd(files_key, *files_data)
                self.redis_client.expire(files_key, self.ttl_seconds)
            
            logger.debug(f"Saved task {task.task_id}")
        except Exception as e:
            logger.error(f"Error saving task {task.task_id}: {e}", exc_info=True)
            raise
    
    def get_task(self, task_id: str) -> Optional[TranscriptionTask]:
        """Get task from storage."""
        try:
            key = f"task:{task_id}"
            if not self.redis_client.exists(key):
                return None
            
            task_data = self.redis_client.hgetall(key)
            if not task_data:
                return None
            
            task = TranscriptionTask(
                task_id=task_data['task_id'],
                webhook_url=task_data.get('webhook_url'),
                options=json.loads(task_data.get('options', '{}'))
            )
            task.status = task_data['status']
            task.created_at = datetime.fromisoformat(task_data['created_at'])
            task.updated_at = datetime.fromisoformat(task_data['updated_at'])
            task.error = task_data.get('error')
            
            # Load files
            files_key = f"task:{task_id}:files"
            files_data = self.redis_client.smembers(files_key)
            for file_json in files_data:
                file_data = json.loads(file_json)
                file_info = task.get_file(file_data['file_id'])
                if not file_info:
                    from app.models.task import FileInfo, FileStatus
                    file_info = FileInfo(
                        file_id=file_data['file_id'],
                        filename=file_data['filename'],
                        status=FileStatus(file_data['status']),
                        error=file_data.get('error')
                    )
                    task.files.append(file_info)
                else:
                    file_info.status = FileStatus(file_data['status'])
                    file_info.error = file_data.get('error')
            
            return task
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}", exc_info=True)
            return None
    
    def save_file_result(self, task_id: str, file_id: str, result: Dict, filename: Optional[str] = None) -> None:
        """Save transcription result for a file."""
        try:
            key = f"file:{file_id}:result"
            # Add filename to result if provided
            result_with_meta = result.copy()
            if filename:
                result_with_meta['filename'] = filename
            result_json = json.dumps(result_with_meta, default=str)
            self.redis_client.set(key, result_json, ex=self.ttl_seconds)
            logger.debug(f"Saved result for file {file_id}")
        except Exception as e:
            logger.error(f"Error saving file result {file_id}: {e}", exc_info=True)
            raise
    
    def get_file_result(self, file_id: str) -> Optional[Dict]:
        """Get transcription result for a file."""
        try:
            key = f"file:{file_id}:result"
            result_json = self.redis_client.get(key)
            if not result_json:
                return None
            return json.loads(result_json)
        except Exception as e:
            logger.error(f"Error getting file result {file_id}: {e}", exc_info=True)
            return None
    
    def update_file_status(
        self,
        task_id: str,
        file_id: str,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """Update file status in task."""
        try:
            task = self.get_task(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found")
                return
            
            file_info = task.get_file(file_id)
            if not file_info:
                logger.warning(f"File {file_id} not found in task {task_id}")
                return
            
            from app.models.task import FileStatus
            file_info.status = FileStatus(status)
            file_info.error = error
            
            # Update files list in Redis
            files_key = f"task:{task_id}:files"
            # Remove old entry
            old_data = json.dumps({
                'file_id': file_info.file_id,
                'filename': file_info.filename,
                'status': file_info.status.value,
                'error': file_info.error,
            })
            self.redis_client.srem(files_key, old_data)
            
            # Add updated entry
            new_data = json.dumps({
                'file_id': file_info.file_id,
                'filename': file_info.filename,
                'status': file_info.status.value,
                'error': file_info.error,
            })
            self.redis_client.sadd(files_key, new_data)
            
            # Save updated task
            self.save_task(task)
            
            logger.debug(f"Updated file {file_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating file status {file_id}: {e}", exc_info=True)
            raise


# Global storage instance
_storage: Optional[Storage] = None


def get_storage() -> Storage:
    """Get or create storage instance."""
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage

