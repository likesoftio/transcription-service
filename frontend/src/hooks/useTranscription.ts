import { useCallback, useEffect, useRef, useState } from 'react';
import { getTaskStatus, uploadFiles } from '../api/client';
import type { TaskFileInfo, UploadProgress } from '../types';

const ALLOWED_EXTENSIONS = new Set([
  '.mp3', '.mp4', '.mp2', '.aac', '.wav', '.flac', '.pcm',
  '.m4a', '.ogg', '.opus', '.webm', '.amr', '.3gp', '.wma',
  '.mov', '.avi', '.wmv', '.flv', '.mkv', '.mpeg', '.mpg',
]);

function getExtension(name: string): string {
  const i = name.lastIndexOf('.');
  return i >= 0 ? name.slice(i).toLowerCase() : '';
}

export function useTranscription() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskFiles, setTaskFiles] = useState<TaskFileInfo[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const addFiles = useCallback((fileList: FileList | File[]) => {
    const newFiles: File[] = [];
    const rejected: string[] = [];

    for (const f of Array.from(fileList)) {
      const ext = getExtension(f.name);
      if (!ALLOWED_EXTENSIONS.has(ext)) {
        rejected.push(f.name);
        continue;
      }
      newFiles.push(f);
    }

    if (rejected.length > 0) {
      alert(`Формат не поддерживается: ${rejected.join(', ')}`);
    }

    setSelectedFiles((prev) => {
      const existing = new Set(prev.map((f) => `${f.name}:${f.size}`));
      const unique = newFiles.filter((f) => !existing.has(`${f.name}:${f.size}`));
      return [...prev, ...unique];
    });
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearFiles = useCallback(() => {
    setSelectedFiles([]);
  }, []);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      setIsPolling(true);

      const poll = async () => {
        try {
          const data = await getTaskStatus(id);
          setTaskFiles(data.files);

          const progress = data.progress;
          const done = (progress.completed || 0) + (progress.failed || 0);
          const total = progress.total || 1;

          if (done >= total) {
            stopPolling();
          }
        } catch (e) {
          console.error('Poll error:', e);
        }
      };

      // Immediate first poll
      poll();

      pollIntervalRef.current = setInterval(poll, 3000);
    },
    [stopPolling],
  );

  const upload = useCallback(async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(null);

    try {
      const data = await uploadFiles(
        selectedFiles,
        { model: 'nova-2', language: 'ru', diarize: true, chunk_duration: 30 },
        (progress) => setUploadProgress(progress),
      );

      setTaskId(data.task_id);
      setTaskFiles(
        data.files.map((f) => ({
          file_id: f.file_id,
          filename: f.filename,
          status: f.status as TaskFileInfo['status'],
        })),
      );
      setIsUploading(false);
      startPolling(data.task_id);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : 'Ошибка загрузки');
      setIsUploading(false);
    }
  }, [selectedFiles, startPolling]);

  const reset = useCallback(() => {
    stopPolling();
    setTaskId(null);
    setTaskFiles([]);
    setSelectedFiles([]);
    setUploadProgress(null);
    setUploadError(null);
    setIsUploading(false);
  }, [stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return {
    selectedFiles,
    addFiles,
    removeFile,
    clearFiles,
    upload,
    uploadProgress,
    uploadError,
    isUploading,
    taskId,
    taskFiles,
    isPolling,
    reset,
  };
}
