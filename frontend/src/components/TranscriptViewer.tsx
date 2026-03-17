import { useState } from 'react';
import type { TaskFileInfo } from '../types';
import './TranscriptViewer.css';

interface TranscriptViewerProps {
  file: TaskFileInfo | null;
}

type Tab = 'full' | 'speakers' | 'chunks';

const TABS: { id: Tab; label: string }[] = [
  { id: 'full', label: 'Транскрипт' },
  { id: 'speakers', label: 'По спикерам' },
  { id: 'chunks', label: 'По фрагментам' },
];

function escapeHtml(s: string): string {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function formatSpeakers(text: string): string {
  return escapeHtml(text).replace(
    /^(Speaker\s*\d+|Спикер\s*\d+)\s*:/gim,
    (match) => `<span class="speaker">${match}</span>`,
  );
}

function formatChunks(text: string): string {
  return escapeHtml(text).replace(
    /\[(\d[\d:.–-]+\d)\]/g,
    (match) => `<span class="chunk-time">${match}</span>`,
  );
}

export default function TranscriptViewer({ file }: TranscriptViewerProps) {
  const [activeTab, setActiveTab] = useState<Tab>('full');

  if (!file) {
    return (
      <div className="result-panel">
        <div className="tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`tab${activeTab === tab.id ? ' active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="tab-content">
          <div className="no-result">Выберите файл для просмотра</div>
        </div>
      </div>
    );
  }

  const renderContent = () => {
    if (file.status === 'failed') {
      return (
        <div className="error-text">
          Ошибка: {file.error || 'неизвестная ошибка'}
        </div>
      );
    }

    if (file.status !== 'completed') {
      return <div className="no-result">Файл ещё обрабатывается...</div>;
    }

    switch (activeTab) {
      case 'full':
        return file.transcript ? (
          <div className="transcript-text">{file.transcript}</div>
        ) : (
          <div className="no-result">Транскрипт пуст</div>
        );

      case 'speakers':
        return file.speakers_transcript ? (
          <div
            className="transcript-text"
            dangerouslySetInnerHTML={{
              __html: formatSpeakers(file.speakers_transcript),
            }}
          />
        ) : (
          <div className="no-result">Данные по спикерам недоступны</div>
        );

      case 'chunks':
        return file.chunks_transcript ? (
          <div
            className="transcript-text"
            dangerouslySetInnerHTML={{
              __html: formatChunks(file.chunks_transcript),
            }}
          />
        ) : (
          <div className="no-result">Данные по фрагментам недоступны</div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="result-panel">
      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-content">{renderContent()}</div>
    </div>
  );
}
