"""Task model for tracking transcription jobs."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class FileStatus(str, Enum):
    """Status of a single file transcription."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Status of a transcription task."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileInfo:
    """Information about a file in a transcription task."""
    
    def __init__(
        self,
        file_id: str,
        filename: str,
        status: FileStatus = FileStatus.QUEUED,
        error: Optional[str] = None
    ):
        self.file_id = file_id
        self.filename = filename
        self.status = status
        self.error = error
        self.result: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = {
            'file_id': self.file_id,
            'filename': self.filename,
            'status': self.status.value,
        }
        if self.error:
            result['error'] = self.error
        if self.result:
            result.update(self.result)
        return result


class TranscriptionTask:
    """Represents a transcription task with multiple files."""
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        options: Optional[Dict] = None
    ):
        self.task_id = task_id or str(uuid4())
        self.status = TaskStatus.QUEUED
        self.files: List[FileInfo] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.webhook_url = webhook_url
        self.options = options or {}
        self.error: Optional[str] = None
    
    def add_file(self, filename: str) -> str:
        """Add a file to the task and return its file_id."""
        file_id = str(uuid4())
        file_info = FileInfo(file_id=file_id, filename=filename)
        self.files.append(file_info)
        return file_id
    
    def get_file(self, file_id: str) -> Optional[FileInfo]:
        """Get file info by file_id."""
        for file_info in self.files:
            if file_info.file_id == file_id:
                return file_info
        return None
    
    def update_status(self):
        """Update task status based on file statuses."""
        if not self.files:
            return
        
        completed = sum(1 for f in self.files if f.status == FileStatus.COMPLETED)
        failed = sum(1 for f in self.files if f.status == FileStatus.FAILED)
        processing = sum(1 for f in self.files if f.status == FileStatus.PROCESSING)
        queued = sum(1 for f in self.files if f.status == FileStatus.QUEUED)
        
        if completed + failed == len(self.files):
            self.status = TaskStatus.COMPLETED if failed == 0 else TaskStatus.FAILED
        elif processing > 0 or queued > 0:
            self.status = TaskStatus.PROCESSING
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        self.update_status()
        
        completed = sum(1 for f in self.files if f.status == FileStatus.COMPLETED)
        failed = sum(1 for f in self.files if f.status == FileStatus.FAILED)
        processing = sum(1 for f in self.files if f.status == FileStatus.PROCESSING)
        queued = sum(1 for f in self.files if f.status == FileStatus.QUEUED)
        
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'progress': {
                'total': len(self.files),
                'completed': completed,
                'failed': failed,
                'processing': processing,
                'queued': queued,
            },
            'files': [f.to_dict() for f in self.files],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

