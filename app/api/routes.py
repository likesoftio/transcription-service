"""API routes for transcription service."""
import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.api.schemas import (
    BatchTranscribeResponse,
    TaskStatusResponse,
    FileResultResponse,
    WebhookRegisterRequest,
    WebhookRegisterResponse,
    HealthResponse,
    TranscriptionOptions,
)
from app.core.storage import get_storage
from app.core.queue import celery_app
from app.core.tasks import transcribe_file_task
from app.config import settings
from app.models.task import TranscriptionTask, FileStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["transcription"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get active workers count
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        workers_count = len(active_workers) if active_workers else 0
    except Exception:
        workers_count = None
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        workers_active=workers_count
    )


@router.post("/transcribe/batch", response_model=BatchTranscribeResponse)
async def transcribe_batch(
    files: List[UploadFile] = File(...),
    options: str = Form(None),
    webhook_url: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload multiple files for transcription.
    
    Args:
        files: List of audio files to transcribe
        options: JSON string with transcription options
        webhook_url: Optional webhook URL for notifications
        
    Returns:
        Task information with file IDs
    """
    # Validate file count
    if len(files) > settings.MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum {settings.MAX_FILES_PER_BATCH} files per batch"
        )
    
    # Parse options
    transcription_options = {}
    if options:
        import json
        try:
            transcription_options = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid options JSON")
    
    # Merge with defaults
    final_options = {
        'model': transcription_options.get('model', settings.DEFAULT_MODEL),
        'language': transcription_options.get('language', settings.DEFAULT_LANGUAGE),
        'chunk_duration': transcription_options.get('chunk_duration', settings.DEFAULT_CHUNK_DURATION),
        'diarize': transcription_options.get('diarize', True),
    }
    
    # Create task
    storage = get_storage()
    task = TranscriptionTask(webhook_url=webhook_url, options=final_options)
    
    # Validate and add files
    file_responses = []
    for file in files:
        # Validate file size
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Add file to task
        file_id = task.add_file(file.filename)
        
        # Encode audio data as base64 for Celery serialization
        import base64
        audio_data_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Create Celery task
        transcribe_file_task.delay(
            task_id=task.task_id,
            file_id=file_id,
            audio_data_base64=audio_data_base64,
            filename=file.filename,
            options=final_options
        )
        
        file_responses.append({
            'file_id': file_id,
            'filename': file.filename,
            'status': 'queued'
        })
    
    # Save task
    storage.save_task(task)
    
    # Estimate completion time (rough estimate: 1 minute per file)
    estimated_time = datetime.utcnow() + timedelta(minutes=len(files))
    
    logger.info(f"Created transcription task {task.task_id} with {len(files)} files")
    
    return BatchTranscribeResponse(
        task_id=task.task_id,
        status="queued",
        files_count=len(files),
        files=file_responses,
        estimated_completion_time=estimated_time.isoformat()
    )


@router.get("/transcribe/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a transcription task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task status with progress and results
    """
    storage = get_storage()
    task = storage.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Load results for completed files
    files_response = []
    for file_info in task.files:
        file_dict = file_info.to_dict()
        
        # Load result if completed
        if file_info.status == FileStatus.COMPLETED:
            result = storage.get_file_result(file_info.file_id)
            if result:
                file_dict.update({
                    'transcript': result.get('transcript'),
                    'speakers_transcript': result.get('speakers_transcript'),
                    'chunks_transcript': result.get('chunks_transcript'),
                    'speaker_count': result.get('speaker_count'),
                    'duration': result.get('duration'),
                })
        
        files_response.append(file_dict)
    
    task_dict = task.to_dict()
    task_dict['files'] = files_response
    
    return TaskStatusResponse(**task_dict)


@router.get("/transcribe/result/{file_id}", response_model=FileResultResponse)
async def get_file_result(file_id: str):
    """
    Get transcription result for a specific file.
    
    Args:
        file_id: File ID
        
    Returns:
        File transcription result
    """
    storage = get_storage()
    
    # Find task containing this file
    # Note: In production, you might want to store file_id -> task_id mapping
    # For now, we'll search through tasks (not efficient for large scale)
    result = storage.get_file_result(file_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="File result not found")
    
    # Try to find file info from any task
    # This is a simplified approach - in production, maintain file_id -> task_id mapping
    file_info = None
    # We'll return what we have from result
    
    return FileResultResponse(
        file_id=file_id,
        filename=result.get('filename', 'unknown'),
        status='completed',
        transcript=result.get('transcript'),
        speakers_transcript=result.get('speakers_transcript'),
        chunks_transcript=result.get('chunks_transcript'),
        speaker_count=result.get('speaker_count'),
        duration=result.get('duration'),
        metadata=result.get('metadata'),
    )


@router.post("/webhook/register", response_model=WebhookRegisterResponse)
async def register_webhook(request: WebhookRegisterRequest):
    """
    Register webhook URL for task notifications.
    
    Args:
        request: Webhook registration request
        
    Returns:
        Registration confirmation
    """
    storage = get_storage()
    task = storage.get_task(request.task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.webhook_url = request.webhook_url
    storage.save_task(task)
    
    logger.info(f"Registered webhook for task {request.task_id}: {request.webhook_url}")
    
    return WebhookRegisterResponse(
        success=True,
        message=f"Webhook registered for task {request.task_id}"
    )

