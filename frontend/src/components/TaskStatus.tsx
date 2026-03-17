import type { TaskFileInfo } from '../types';
import './TaskStatus.css';

interface TaskStatusProps {
  taskId: string;
  files: TaskFileInfo[];
  activeFileId: string | null;
  onSelectFile: (fileId: string) => void;
}

const STATUS_BADGE: Record<string, { className: string; label: string }> = {
  queued: { className: 'badge-queued', label: 'в очереди' },
  processing: { className: 'badge-processing', label: 'обработка' },
  completed: { className: 'badge-completed', label: 'готово' },
  failed: { className: 'badge-failed', label: 'ошибка' },
};

function formatDuration(seconds: number): string {
  const s = Math.round(seconds);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}м ${sec}с`;
}

export default function TaskStatus({
  taskId,
  files,
  activeFileId,
  onSelectFile,
}: TaskStatusProps) {
  const completed = files.filter(
    (f) => f.status === 'completed' || f.status === 'failed',
  ).length;
  const total = files.length || 1;
  const progressPercent = Math.round((completed / total) * 100);

  return (
    <div className="task-section">
      <div className="task-header">
        <h2>Результаты</h2>
        <span className="task-id">ID: {taskId}</span>
      </div>

      <div className="overall-progress">
        <span className="overall-progress-text">
          Обработано: <span>{completed}/{files.length}</span>
        </span>
        <div className="progress-container">
          <div
            className="progress-bar"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="file-status-list">
        {files.map((file) => {
          const badge = STATUS_BADGE[file.status] || STATUS_BADGE.queued;
          const metaParts: string[] = [];
          if (file.duration) metaParts.push(formatDuration(file.duration));
          if (file.speaker_count)
            metaParts.push(`${file.speaker_count} спик.`);

          return (
            <div
              key={file.file_id}
              className={`file-card${file.file_id === activeFileId ? ' active' : ''}`}
              onClick={() => onSelectFile(file.file_id)}
            >
              <div className="file-card-top">
                <span className="file-card-name">{file.filename}</span>
                <span className={`badge ${badge.className}`}>
                  {badge.label}
                </span>
              </div>
              {metaParts.length > 0 && (
                <div className="file-card-meta">{metaParts.join(' \u00b7 ')}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
