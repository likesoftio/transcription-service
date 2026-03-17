import { useCallback, useMemo, useRef, useState } from 'react';
import './DropZone.css';

interface DropZoneProps {
  onFilesAdded: (files: FileList) => void;
}

export default function DropZone({ onFilesAdded }: DropZoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        onFilesAdded(e.target.files);
        e.target.value = '';
      }
    },
    [onFilesAdded],
  );

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onFilesAdded(e.dataTransfer.files);
      }
    },
    [onFilesAdded],
  );

  const waveformBars = useMemo(() => {
    return Array.from({ length: 40 }, (_, i) => ({
      key: i,
      delay: (Math.random() * 1.8).toFixed(2) + 's',
      height: Math.floor(Math.random() * 15 + 3) + 'px',
    }));
  }, []);

  return (
    <div>
      <div
        className={`drop-zone${dragOver ? ' drag-over' : ''}`}
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <span className="drop-zone-icon">&#9113;</span>
        <div className="drop-zone-text">
          Перетащите файлы сюда или <strong>выберите</strong>
        </div>
        <span className="drop-zone-hint">
          mp3 &middot; wav &middot; mp4 &middot; ogg &middot; flac &middot; mov &middot; mkv &middot; и другие
        </span>
        <input
          type="file"
          ref={inputRef}
          onChange={handleChange}
          multiple
          accept=".mp3,.mp4,.mp2,.aac,.wav,.flac,.pcm,.m4a,.ogg,.opus,.webm,.amr,.3gp,.wma,.mov,.avi,.wmv,.flv,.mkv,.mpeg,.mpg"
        />
      </div>
      <div className="waveform-bar">
        {waveformBars.map((bar) => (
          <span
            key={bar.key}
            style={{ animationDelay: bar.delay, height: bar.height }}
          />
        ))}
      </div>
    </div>
  );
}
