"""Pydantic schemas for API validation."""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class TranscriptionOptions(BaseModel):
    """Transcription options."""
    model: str = Field(default="nova-2", description="Deepgram model")
    language: str = Field(default="ru", description="Language code")
    chunk_duration: float = Field(default=30.0, description="Chunk duration in seconds")
    diarize: bool = Field(default=True, description="Enable speaker diarization")


class FileInfoResponse(BaseModel):
    """File information in response."""
    file_id: str
    filename: str
    status: str
    error: Optional[str] = None
    transcript: Optional[str] = None
    speakers_transcript: Optional[str] = None
    chunks_transcript: Optional[str] = None
    speaker_count: Optional[int] = None
    duration: Optional[float] = None


class BatchTranscribeResponse(BaseModel):
    """Response for batch transcription request."""
    task_id: str
    status: str
    files_count: int
    files: List[FileInfoResponse]
    estimated_completion_time: Optional[str] = None


class ProgressInfo(BaseModel):
    """Progress information."""
    total: int
    completed: int
    failed: int
    processing: int
    queued: int


class TaskStatusResponse(BaseModel):
    """Response for task status."""
    task_id: str
    status: str
    progress: ProgressInfo
    files: List[FileInfoResponse]
    created_at: str
    updated_at: str


class FileResultResponse(BaseModel):
    """Response for file result."""
    file_id: str
    filename: str
    status: str
    transcript: Optional[str] = None
    speakers_transcript: Optional[str] = None
    chunks_transcript: Optional[str] = None
    speaker_count: Optional[int] = None
    duration: Optional[float] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict] = None
    error: Optional[str] = None


class WebhookRegisterRequest(BaseModel):
    """Request to register webhook."""
    task_id: str
    webhook_url: str
    events: List[str] = Field(default=["completed", "failed"])


class WebhookRegisterResponse(BaseModel):
    """Response for webhook registration."""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    workers_active: Optional[int] = None

