import type { UploadProgress } from '../types';
import './ProgressBar.css';

interface ProgressBarProps {
  progress: UploadProgress | null;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' Б';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' КБ';
  return (bytes / 1048576).toFixed(1) + ' МБ';
}

export default function ProgressBar({ progress }: ProgressBarProps) {
  const percent = progress?.percent ?? 0;
  const loaded = progress?.loaded ?? 0;
  const total = progress?.total ?? 0;

  return (
    <div className="upload-section">
      <div className="upload-section-label">Загрузка файлов...</div>
      <div className="progress-container">
        <div
          className="progress-bar"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="progress-label">
        <span>{percent}%</span>
        <span>
          {total > 0 ? `${formatSize(loaded)} / ${formatSize(total)}` : ''}
        </span>
      </div>
    </div>
  );
}
