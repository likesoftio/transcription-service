#!/usr/bin/env python3
"""Test transcription microservice API."""
import sys
import time
import json
from pathlib import Path
import httpx

API_URL = "http://localhost:8000/api/v1"

def main():
    print("=" * 60)
    print("Тестирование микросервиса транскрибации")
    print("=" * 60)
    
    # Check health
    print("\n1. Проверка health check...")
    try:
        response = httpx.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ API доступен: {data}")
    except Exception as e:
        print(f"❌ API недоступен: {e}")
        return 1
    
    # Find test files
    print("\n2. Поиск тестовых файлов...")
    input_dir = Path("/app/input")
    if not input_dir.exists():
        input_dir = Path("input")
    
    SUPPORTED_EXTENSIONS = {
        ".mp3", ".mp4", ".mp2", ".aac", ".wav", ".flac", ".pcm",
        ".m4a", ".ogg", ".opus", ".webm", ".amr", ".3gp", ".wma",
        ".mov", ".avi", ".wmv", ".flv", ".mkv", ".mpeg", ".mpg",
    }
    files = [
        f for f in input_dir.rglob("*")
        if f.suffix.lower() in SUPPORTED_EXTENSIONS and f.stat().st_size > 100000
    ][:2]  # > 100KB
    
    if not files:
        print("❌ Не найдено подходящих файлов (>100KB)")
        return 1
    
    print(f"Найдено {len(files)} файлов:")
    for f in files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  - {f.name} ({size_mb:.2f} MB)")
    
    # Send files
    print("\n3. Отправка файлов на транскрибацию...")
    try:
        file_data = []
        for f in files:
            file_data.append(("files", (f.name, open(f, "rb"), "application/octet-stream")))
        
        options = {
            "model": "nova-2",
            "language": "ru",
            "diarize": True,
            "chunk_duration": 30.0
        }
        
        response = httpx.post(
            f"{API_URL}/transcribe/batch",
            files=file_data,
            data={"options": json.dumps(options)},
            timeout=300.0
        )
        response.raise_for_status()
        
        result = response.json()
        task_id = result['task_id']
        
        print(f"✅ Задача создана:")
        print(f"   Task ID: {task_id}")
        print(f"   Статус: {result['status']}")
        print(f"   Файлов: {result['files_count']}")
        
        # Close files
        for _, t in file_data:
            t[1].close()
        
        # Wait and check status
        print("\n4. Ожидание обработки (30 секунд)...")
        time.sleep(30)
        
        print("\n5. Проверка статуса...")
        response = httpx.get(f"{API_URL}/transcribe/status/{task_id}", timeout=10)
        response.raise_for_status()
        status = response.json()
        
        progress = status.get('progress', {})
        print(f"   Статус задачи: {status['status']}")
        print(f"   Прогресс: {progress.get('completed', 0)}/{progress.get('total', 0)} завершено")
        
        files_info = status.get('files', [])
        for f_info in files_info:
            print(f"\n   📄 {f_info.get('filename')}:")
            print(f"      Статус: {f_info.get('status')}")
            if f_info.get('status') == 'completed':
                transcript = f_info.get('transcript', '')
                if transcript:
                    preview = transcript[:100] + "..." if len(transcript) > 100 else transcript
                    print(f"      Транскрипт: {preview}")
                print(f"      Спикеров: {f_info.get('speaker_count', 'N/A')}")
                print(f"      Длительность: {f_info.get('duration', 'N/A')} сек")
        
        print("\n" + "=" * 60)
        print("✅ Тестирование завершено")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

