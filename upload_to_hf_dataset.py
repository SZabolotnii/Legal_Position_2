#!/usr/bin/env python3
"""
Скрипт для завантаження індексів векторної бази на Hugging Face Dataset
"""
import os
from pathlib import Path
from huggingface_hub import HfApi, login

def upload_indexes():
    """Завантажує індекси на HF Dataset"""
    
    # Використовуємо токен з environment variable або prompt
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("⚠️ HF_TOKEN not found in environment")
        print("Please set it: export HF_TOKEN=your_token_here")
        print("Or run: python -c 'from huggingface_hub import login; login()'")
        return
    
    print("🔐 Авторизація в Hugging Face...")
    
    api = HfApi(token=token)
    repo_id = "DocSA/legal-position-indexes"
    repo_type = "dataset"
    
    # Шлях до індексів
    index_path = Path("Save_Index_Ivan")
    
    if not index_path.exists():
        print(f"❌ Директорія {index_path} не знайдена!")
        return
    
    print(f"📦 Завантаження індексів з {index_path}...")
    print(f"📍 До датасету: {repo_id}")
    
    # Завантажуємо всю директорію
    api.upload_folder(
        folder_path=str(index_path),
        repo_id=repo_id,
        repo_type=repo_type,
        path_in_repo=".",  # Завантажити в корінь датасету
        commit_message="Upload vector database indexes for Legal Position Analyzer"
    )
    
    print("✅ Індекси успішно завантажено!")
    print(f"🌐 Датасет: https://huggingface.co/datasets/{repo_id}")
    
    # Перевіряємо розмір
    total_size = sum(f.stat().st_size for f in index_path.rglob('*') if f.is_file())
    print(f"📊 Загальний розмір: {total_size / (1024**2):.2f} MB")

if __name__ == "__main__":
    upload_indexes()
