# 📦 Налаштування Hugging Face Dataset для індексів

## Крок 1: Створення датасету на Hugging Face

1. **Перейдіть на:** https://huggingface.co/new-dataset

2. **Заповніть форму:**
   - Owner: `DocSA`
   - Dataset name: `legal-position-indexes`
   - License: `MIT`
   - Visibility: `Private` або `Public` (на ваш вибір)

3. **Натисніть:** Create dataset

## Крок 2: Клонування та налаштування

```bash
# Клонуйте створений датасет
git clone https://huggingface.co/datasets/DocSA/legal-position-indexes
cd legal-position-indexes

# Налаштуйте Git LFS для великих файлів
git lfs install

# Додайте треки для різних типів файлів індексів
git lfs track "*.json"
git lfs track "*.jsonl"
git lfs track "*.npy"
git lfs track "*.mmindex.json"
git lfs track "*.csc.index.npy"
git lfs track "*.index.json"

# Збережіть конфігурацію LFS
git add .gitattributes
git commit -m "Configure Git LFS"
```

## Крок 3: Завантаження індексів

```bash
# Скопіюйте індекси з вашого проєкту
cp -r ../Save_Index_Ivan/* ./

# Перевірте розмір
du -sh .

# Створіть README
cat > README.md << 'EOF'
---
license: mit
task_categories:
- text-retrieval
language:
- uk
tags:
- legal
- ukraine
- embeddings
- bm25
size_categories:
- n<1K
---

# Legal Position Indexes

Індекси для пошуку правових позицій Верховного Суду України.

## 📊 Вміст

- **BM25 Retriever**: Індекси для пошуку за ключовими словами
- **Document Store**: База судових рішень
- **Vector Embeddings**: Векторні представлення для семантичного пошуку

## 📁 Структура

```
legal-position-indexes/
├── docstore_es_filter.json      # Document store
├── bm25_retriever/              # BM25 індекси
│   ├── corpus.jsonl
│   ├── corpus.mmindex.json
│   ├── data.csc.index.npy
│   ├── indices.csc.index.npy
│   ├── indptr.csc.index.npy
│   ├── params.index.json
│   ├── retriever.json
│   └── vocab.index.json
├── bm25_retriever_meta/         # BM25 з метаданими
└── bm25_retriever_short/        # BM25 короткий
```

## 🚀 Використання

### Python

\`\`\`python
from huggingface_hub import snapshot_download

# Завантажити всі індекси
snapshot_download(
    repo_id="DocSA/legal-position-indexes",
    repo_type="dataset",
    local_dir="Save_Index_Ivan"
)
\`\`\`

### В проєкті Legal Position AI Analyzer

\`\`\`python
from index_loader import load_indexes_with_fallback

# Автоматично завантажить з HF Datasets
load_indexes_with_fallback()
\`\`\`

## 📊 Статистика

- **Розмір:** ~530 MB
- **Документів:** ~[NUMBER]
- **Мова:** Українська
- **Оновлено:** 10 лютого 2026 р.

## 📝 Ліцензія

MIT License

## 👥 Автори

Проєкт Legal Position AI Analyzer для Верховного Суду України
EOF

# Додайте всі файли
git add .

# Закомітьте
git commit -m "Add legal position indexes v1.0

- BM25 retrievers
- Document store
- Vector embeddings
- Total size: ~530MB"

# Завантажте на HF
git push
```

## Крок 4: Перевірка

1. **Перейдіть на:** https://huggingface.co/datasets/DocSA/legal-position-indexes

2. **Перевірте:**
   - ✅ Всі файли завантажені
   - ✅ README відображається
   - ✅ LFS файли правильно трекаються

## Крок 5: Інтеграція в проєкт

### Оновіть main.py або components.py:

```python
from index_loader import load_indexes_with_fallback

def initialize_components() -> bool:
    """Initialize all necessary components for the application."""
    try:
        # Завантажити індекси з HF Datasets (з fallback на S3)
        if not load_indexes_with_fallback():
            logger.error("Failed to load indexes")
            return False
        
        # Решта ініціалізації...
        # ...
        
        return True
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        return False
```

### Оновіть app.py для HF Spaces:

```python
#!/usr/bin/env python3
import os
from index_loader import load_indexes_with_fallback

# Завантажити індекси при старті
print("📥 Loading indexes...")
if load_indexes_with_fallback():
    print("✅ Indexes loaded successfully!")
else:
    print("⚠️ Warning: Indexes not available. Search will not work.")

# Запуск додатку
from interface import create_gradio_interface

if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        enable_queue=True
    )
```

## Крок 6: Налаштування для приватного датасету (опціонально)

Якщо ваш датасет приватний:

### На HF Spaces:

1. Settings > Variables and secrets
2. Додайте:
   ```
   HF_TOKEN=hf_xxxxxxxxxxxxx
   ```

### В коді:

```python
import os

load_indexes_with_fallback(
    token=os.getenv("HF_TOKEN")
)
```

## 🔄 Оновлення індексів

### Коли потрібно оновити індекси:

```bash
cd legal-position-indexes

# Оновіть файли
cp -r ../Save_Index_Ivan/* ./

# Закомітьте зміни
git add .
git commit -m "Update indexes v1.1"
git push

# Індекси автоматично оновляться на всіх інсталяціях
```

## ✅ Переваги цього підходу

- ✅ **Безкоштовно** - HF Datasets безкоштовний
- ✅ **Швидко** - CDN для швидкого завантаження
- ✅ **Просто** - Нативна інтеграція з HF Spaces
- ✅ **Версіонування** - Git історія змін
- ✅ **Fallback** - Автоматичний перехід на S3 при помилці
- ✅ **Оновлення** - Легко оновлювати індекси

## 📊 Порівняння з AWS S3

| Параметр | HF Datasets | AWS S3 |
|----------|-------------|--------|
| Вартість | $0 | ~$0.02/міс |
| Setup | Простий | Середній |
| Швидкість | Швидко | Швидко |
| Інтеграція з HF Spaces | Відмінна | Потребує credentials |
| Версіонування | Так (Git) | Ні (окремо) |

---

**Дата:** 10 лютого 2026 р.
