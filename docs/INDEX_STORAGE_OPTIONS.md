# 🗄️ Альтернативи для зберігання векторної бази даних та індексів

## 📊 Поточна ситуація

- **Розмір індексів:** ~530 MB
- **Склад:** BM25 індекси, docstore, векторні представлення
- **Поточне рішення:** AWS S3

---

## 🔄 Альтернативні варіанти зберігання

### 1. 🤗 Hugging Face Datasets Hub

**Переваги:**
- ✅ Безкоштовно для публічних датасетів
- ✅ Нативна інтеграція з HF Spaces
- ✅ Git LFS для великих файлів
- ✅ Версіонування
- ✅ Швидке завантаження через CDN
- ✅ API для програмного доступу

**Недоліки:**
- ❌ Публічний доступ (якщо не приватний репозиторій)
- ❌ Обмеження на розмір файлів (5GB для LFS)

**Як використати:**
```python
from huggingface_hub import hf_hub_download, snapshot_download

# Завантажити всю папку індексів
snapshot_download(
    repo_id="DocSA/legal-position-indexes",
    repo_type="dataset",
    local_dir="Save_Index_Ivan"
)
```

**Налаштування:**
1. Створіть датасет: https://huggingface.co/new-dataset
2. Завантажте індекси:
```bash
git lfs install
git clone https://huggingface.co/datasets/DocSA/legal-position-indexes
cd legal-position-indexes
cp -r ../Save_Index_Ivan/* ./
git add .
git commit -m "Add indexes"
git push
```

---

### 2. ☁️ Google Cloud Storage (GCS)

**Переваги:**
- ✅ $0.02 за GB/місяць (дешевше за S3)
- ✅ Безкоштовні 5 GB (Always Free tier)
- ✅ Швидкий доступ з будь-якої точки світу
- ✅ Python SDK (google-cloud-storage)

**Недоліки:**
- ❌ Потрібна реєстрація GCP
- ❌ Додаткові credentials

**Як використати:**
```python
from google.cloud import storage

def download_from_gcs(bucket_name, prefix, local_dir):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    for blob in blobs:
        local_path = f"{local_dir}/{blob.name}"
        blob.download_to_filename(local_path)
```

**Вартість:** ~$0.01/місяць для 530MB

---

### 3. 📦 GitHub Releases

**Переваги:**
- ✅ Безкоштовно
- ✅ Простий доступ через URL
- ✅ Підтримка великих файлів (до 2GB)
- ✅ Не потрібні credentials

**Недоліки:**
- ❌ Обмеження: 2GB на файл
- ❌ Треба розбивати на частини
- ❌ Ручне оновлення

**Як використати:**
```python
import requests
import tarfile

def download_from_github_release():
    url = "https://github.com/DocSA/legal-position/releases/download/v1.0/save_index.tar.gz"
    response = requests.get(url, stream=True)
    
    with open("save_index.tar.gz", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Розпакувати
    with tarfile.open("save_index.tar.gz") as tar:
        tar.extractall(".")
```

---

### 4. 🌐 Azure Blob Storage

**Переваги:**
- ✅ Дешевий ($0.018 за GB/місяць)
- ✅ Безкоштовні 5 GB перших 12 місяців
- ✅ Python SDK (azure-storage-blob)
- ✅ Гарна інтеграція з Microsoft екосистемою

**Недоліки:**
- ❌ Потрібна реєстрація Azure
- ❌ Додаткові credentials

**Вартість:** ~$0.01/місяць для 530MB

---

### 5. 🗂️ Dropbox / Google Drive (через публічні посилання)

**Переваги:**
- ✅ Безкоштовно для невеликих обсягів
- ✅ Просто налаштувати
- ✅ Публічні посилання для завантаження

**Недоліки:**
- ❌ Не призначені для production
- ❌ Rate limits
- ❌ Можуть заблокувати посилання
- ❌ Повільне завантаження

**Не рекомендується для production!**

---

### 6. 📡 Cloudflare R2

**Переваги:**
- ✅ Безкоштовний egress (трафік на вихід)
- ✅ $0.015 за GB/місяць (дешевше за S3)
- ✅ S3-compatible API
- ✅ Безкоштовні 10 GB зберігання

**Недоліки:**
- ❌ Потрібна реєстрація Cloudflare
- ❌ Менш зрілий сервіс

**Вартість:** Безкоштовно (в межах 10GB)

---

### 7. 🏠 Вбудувати в Docker image (для HF Spaces)

**Переваги:**
- ✅ Все в одному місці
- ✅ Швидкий старт (без завантаження)
- ✅ Не потрібні додаткові сервіси

**Недоліки:**
- ❌ Великий розмір image (~1GB+)
- ❌ Повільне deployment
- ❌ Складніше оновлювати індекси

**Підходить для:** Статичних індексів, які рідко змінюються

---

### 8. 🎯 HF Space Persistent Storage

**Переваги:**
- ✅ Вбудоване в HF Spaces
- ✅ Не потрібні додаткові сервіси
- ✅ Дані зберігаються між перезапусками

**Недоліки:**
- ❌ Доступно тільки для платних планів
- ❌ Обмежений об'єм

**Вартість:** Від $5/місяць (Supporter tier)

---

## 🏆 Рекомендовані рішення

### Для production (на вибір):

#### 🥇 **Варіант 1: Hugging Face Datasets** (Найкращий для HF Spaces)
```yaml
Вартість: Безкоштовно
Складність: Низька
Швидкість: Висока
Надійність: Висока
```

#### 🥈 **Варіант 2: Cloudflare R2** (Найдешевший)
```yaml
Вартість: Безкоштовно (до 10GB)
Складність: Середня
Швидкість: Висока
Надійність: Висока
```

#### 🥉 **Варіант 3: Google Cloud Storage** (Перевірений)
```yaml
Вартість: ~$0.01/місяць
Складність: Середня
Швидкість: Висока
Надійність: Дуже висока
```

---

## 📝 Порівняльна таблиця

| Сервіс | Вартість/міс | Setup | Швидкість | Надійність | Рекомендація |
|--------|--------------|-------|-----------|------------|--------------|
| **HF Datasets** | $0 | ⭐⭐⭐ | ⚡⚡⚡ | ✅✅✅ | ⭐⭐⭐⭐⭐ |
| **Cloudflare R2** | $0 | ⭐⭐ | ⚡⚡⚡ | ✅✅✅ | ⭐⭐⭐⭐ |
| **GCS** | $0.01 | ⭐⭐ | ⚡⚡⚡ | ✅✅✅ | ⭐⭐⭐⭐ |
| **AWS S3** | $0.02 | ⭐⭐ | ⚡⚡⚡ | ✅✅✅ | ⭐⭐⭐ |
| **Azure Blob** | $0.01 | ⭐⭐ | ⚡⚡ | ✅✅✅ | ⭐⭐⭐ |
| **GitHub Releases** | $0 | ⭐⭐⭐ | ⚡⚡ | ✅✅ | ⭐⭐ |
| **Docker Image** | $0 | ⭐ | ⚡⚡⚡ | ✅✅ | ⭐⭐ |
| **Dropbox/Drive** | $0 | ⭐⭐⭐ | ⚡ | ✅ | ⭐ |

---

## 🚀 План міграції на Hugging Face Datasets (Рекомендовано)

### Крок 1: Створення датасету
```bash
# 1. Створіть новий датасет на HF
# https://huggingface.co/new-dataset
# Назва: DocSA/legal-position-indexes

# 2. Клонуйте репозиторій
git clone https://huggingface.co/datasets/DocSA/legal-position-indexes
cd legal-position-indexes

# 3. Налаштуйте Git LFS
git lfs install
git lfs track "*.json"
git lfs track "*.jsonl"
git lfs track "*.npy"
git lfs track "*.index.*"
```

### Крок 2: Завантаження індексів
```bash
# Скопіюйте індекси
cp -r ../Save_Index_Ivan/* ./

# Додайте README
cat > README.md << 'EOF'
---
license: mit
---

# Legal Position Indexes

Індекси для Legal Position AI Analyzer.

## Вміст

- BM25 retriever
- Document store
- Vector embeddings

## Використання

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="DocSA/legal-position-indexes",
    repo_type="dataset",
    local_dir="Save_Index_Ivan"
)
```
EOF

# Закомітьте
git add .
git commit -m "Add legal position indexes"
git push
```

### Крок 3: Оновлення коду
```python
# Додайте в main.py або components.py

from huggingface_hub import snapshot_download
from pathlib import Path

def download_indexes_from_hf():
    """Download indexes from Hugging Face Datasets."""
    local_dir = Path("Save_Index_Ivan")
    
    if not local_dir.exists() or not list(local_dir.iterdir()):
        print("📥 Downloading indexes from Hugging Face...")
        snapshot_download(
            repo_id="DocSA/legal-position-indexes",
            repo_type="dataset",
            local_dir=str(local_dir),
            allow_patterns=["*"]
        )
        print("✅ Indexes downloaded successfully!")
    else:
        print("✅ Indexes already exist locally")

# Викликайте при ініціалізації
download_indexes_from_hf()
```

---

## 💡 Мій рекомендований підхід

**Використайте Hugging Face Datasets** з fallback на AWS S3:

```python
def load_indexes():
    """Load indexes with fallback strategy."""
    try:
        # Спробувати завантажити з HF Datasets
        download_indexes_from_hf()
    except Exception as e:
        print(f"⚠️ HF download failed: {e}")
        try:
            # Fallback на AWS S3
            download_from_s3()
        except Exception as e2:
            print(f"⚠️ S3 download failed: {e2}")
            print("❌ No indexes available")
```

**Переваги цього підходу:**
- ✅ Безкоштовно
- ✅ Швидко
- ✅ Надійно (fallback)
- ✅ Нативна інтеграція з HF Spaces

---

**Дата:** 10 лютого 2026 р.
