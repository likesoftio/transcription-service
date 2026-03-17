import { useCallback, useState } from 'react';
import './App.css';
import DropZone from './components/DropZone';
import FileList from './components/FileList';
import ProgressBar from './components/ProgressBar';
import TaskStatus from './components/TaskStatus';
import TranscriptViewer from './components/TranscriptViewer';
import { useTranscription } from './hooks/useTranscription';

export default function App() {
  const {
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
    reset,
  } = useTranscription();

  const [activeFileId, setActiveFileId] = useState<string | null>(null);

  const activeFile = taskFiles.find((f) => f.file_id === activeFileId) ?? null;

  const isUploadPhase = !isUploading && !taskId;
  const isUploadingPhase = isUploading;
  const isResultsPhase = !isUploading && !!taskId;

  const handleSelectFile = useCallback((fileId: string) => {
    setActiveFileId(fileId);
  }, []);

  const handleReset = useCallback(() => {
    setActiveFileId(null);
    reset();
  }, [reset]);

  return (
    <div className="app">
      <header className="header">
        <h1>Транскрибация</h1>
        <p>Загрузите аудио или видео файлы для распознавания речи</p>
      </header>

      {/* Upload phase */}
      {isUploadPhase && (
        <>
          <DropZone onFilesAdded={addFiles} />
          <FileList files={selectedFiles} onRemove={removeFile} />
          {selectedFiles.length > 0 && (
            <div className="actions">
              <button
                className="btn btn-secondary"
                onClick={clearFiles}
                type="button"
              >
                Очистить
              </button>
              <button
                className="btn btn-primary"
                onClick={upload}
                type="button"
              >
                Транскрибировать
              </button>
            </div>
          )}
          {uploadError && (
            <div className="upload-error">{uploadError}</div>
          )}
        </>
      )}

      {/* Uploading phase */}
      {isUploadingPhase && <ProgressBar progress={uploadProgress} />}

      {/* Results phase */}
      {isResultsPhase && taskId && (
        <>
          <TaskStatus
            taskId={taskId}
            files={taskFiles}
            activeFileId={activeFileId}
            onSelectFile={handleSelectFile}
          />
          <TranscriptViewer file={activeFile} />
          <div className="new-task">
            <button
              className="btn btn-secondary"
              onClick={handleReset}
              type="button"
            >
              Новая задача
            </button>
          </div>
        </>
      )}
    </div>
  );
}
