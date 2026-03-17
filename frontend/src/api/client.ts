import type {
  HealthResponse,
  TaskStatusResponse,
  TranscriptionOptions,
  UploadProgress,
  UploadResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export function uploadFiles(
  files: File[],
  options: TranscriptionOptions,
  onProgress?: (progress: UploadProgress) => void,
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const fd = new FormData();
    files.forEach((f) => fd.append('files', f));
    fd.append('options', JSON.stringify(options));

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE_URL}/transcribe/batch`);

    xhr.upload.addEventListener('progress', (e) => {
      if (!e.lengthComputable) return;
      const percent = Math.round((e.loaded / e.total) * 100);
      onProgress?.({ loaded: e.loaded, total: e.total, percent });
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as UploadResponse);
      } else {
        let message = 'Ошибка загрузки';
        try {
          const body = JSON.parse(xhr.responseText);
          if (body.detail) message = body.detail;
        } catch {
          /* ignore */
        }
        reject(new Error(message));
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Ошибка сети'));
    });

    xhr.send(fd);
  });
}

export async function getTaskStatus(
  taskId: string,
): Promise<TaskStatusResponse> {
  const res = await fetch(`${BASE_URL}/transcribe/status/${taskId}`);
  if (!res.ok) {
    throw new Error(`Ошибка получения статуса: ${res.status}`);
  }
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Ошибка проверки: ${res.status}`);
  }
  return res.json();
}
