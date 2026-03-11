---
license: mit
task_categories:
- text-retrieval
- sentence-similarity
language:
- uk
tags:
- legal
- ukrainian-law
- supreme-court
- vector-database
- embeddings
size_categories:
- n<1K
---

# Legal Position Indexes

**Індекси векторної бази даних для Legal Position AI Analyzer**

## 📋 Опис

Цей датасет містить передобчислені індекси для швидкого пошуку релевантних судових рішень та правових позицій Верховного Суду України.

### Склад індексів:

- **BM25 Retriever** - індекс для пошуку за ключовими словами
- **BM25 Retriever Meta** - індекс з метаданими
- **BM25 Retriever Short** - скорочений індекс
- **ChromaDB with HuggingFace Embeddings** - векторні представлення документів
- **Docstore** - сховище документів з фільтрацією

## 🔧 Використання

### Завантаження через Python:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="DocSA/legal-position-indexes",
    repo_type="dataset",
    local_dir="Save_Index_Ivan"
)
```

### Використання в Legal Position AI Analyzer:

Індекси автоматично завантажуються при запуску додатку на Hugging Face Spaces.

## 📊 Характеристики

- **Розмір:** ~530 MB
- **Мова:** Українська
- **Джерело:** Судові рішення Верховного Суду України
- **Embeddings:** OpenAI text-embedding-3-small
- **BM25 Parameters:** k1=1.5, b=0.75

## 🔗 Пов'язані ресурси

- **Application:** [Legal Position AI Analyzer](https://huggingface.co/spaces/DocSA/LP_2-test)
- **Organization:** [DocSA](https://huggingface.co/DocSA)

## 📄 Ліцензія

MIT License - вільне використання з attribution
