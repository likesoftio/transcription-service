export interface HealthResponse {
  status: string;
  timestamp: string;
  workers_active: number;
}

export interface UploadFileInfo {
  file_id: string;
  filename: string;
  status: string;
}

export interface UploadResponse {
  task_id: string;
  status: string;
  files_count: number;
  files: UploadFileInfo[];
  estimated_completion_time: string | null;
}

export interface TaskFileInfo {
  file_id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  error?: string;
  transcript?: string;
  speakers_transcript?: string;
  chunks_transcript?: string;
  speaker_count?: number;
  duration?: number;
}

export interface TaskProgress {
  total: number;
  completed: number;
  failed: number;
  processing: number;
  queued: number;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  progress: TaskProgress;
  files: TaskFileInfo[];
  created_at: string;
  updated_at: string;
}

export interface TranscriptionOptions {
  model?: string;
  language?: string;
  diarize?: boolean;
  chunk_duration?: number;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}
