import './FileList.css';

interface FileListProps {
  files: File[];
  onRemove: (index: number) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' Б';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' КБ';
  return (bytes / 1048576).toFixed(1) + ' МБ';
}

export default function FileList({ files, onRemove }: FileListProps) {
  if (files.length === 0) return null;

  return (
    <div className="file-list">
      {files.map((file, index) => (
        <div className="file-item" key={`${file.name}-${file.size}-${index}`}>
          <span className="file-item-name">{file.name}</span>
          <span className="file-item-size">{formatSize(file.size)}</span>
          <button
            className="file-item-remove"
            onClick={() => onRemove(index)}
            type="button"
          >
            &times;
          </button>
        </div>
      ))}
    </div>
  );
}
