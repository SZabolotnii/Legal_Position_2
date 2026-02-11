# 🚀 Інструкція з розгортання на Hugging Face Spaces

## 📋 Підготовка

### 1. Перевірте необхідні файли

Переконайтеся, що у вас є:
- ✅ `app.py` - точка входу
- ✅ `requirements.txt` - залежності
- ✅ `README_HF.md` - опис для HF (перейменувати в README.md)
- ✅ `.env.example` - приклад змінних оточення
- ✅ Вся папка `config/`
- ✅ Файли: `interface.py`, `main.py`, `prompts.py`, `utils.py`, `components.py`
- ✅ Папки: `src/`, `embeddings/`

### 2. Підготовка локальних індексів

Якщо у вас є локальні індекси в `Save_Index_Ivan/`:
```bash
# Створіть tar.gz архів індексів
tar -czf save_index.tar.gz Save_Index_Ivan/
```

## 🔧 Розгортання на Hugging Face Spaces

### Варіант 1: Через веб-інтерфейс

1. **Перейдіть на https://huggingface.co/spaces/DocSA/LP_2-test**

2. **Files > Add file**
   - Завантажте всі необхідні файли
   - Структура повинна відповідати структурі проєкту

3. **Settings > Variables and secrets**
   
   Додайте секрети (API ключі):
   ```
   ANTHROPIC_API_KEY = ваш_ключ
   OPENAI_API_KEY = ваш_ключ (опціонально)
   GEMINI_API_KEY = ваш_ключ (опціонально)
   DEEPSEEK_API_KEY = ваш_ключ (опціонально)
   ```
   
   AWS (якщо потрібно завантажувати з S3):
   ```
   AWS_ACCESS_KEY_ID = ваш_ключ
   AWS_SECRET_ACCESS_KEY = ваш_секрет
   ```

4. **Перейменуйте README_HF.md в README.md**
   - Це важливо для коректного відображення на HF

### Варіант 2: Через Git

1. **Клонуйте HF Space репозиторій:**
   ```bash
   git clone https://huggingface.co/spaces/DocSA/LP_2-test
   cd LP_2-test
   ```

2. **Скопіюйте файли проєкту:**
   ```bash
   # З вашого проєкту
   cp -r /path/to/Legal_Position_2/* ./
   
   # Перейменуйте README
   mv README_HF.md README.md
   ```

3. **Додайте файли до git:**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push
   ```

4. **Налаштуйте секрети через веб-інтерфейс HF**

## 📦 Структура файлів на HF Spaces

```
LP_2-test/
├── app.py                      # Точка входу
├── README.md                   # Опис (з README_HF.md)
├── requirements.txt            # Залежності Python
├── .env.example               # Приклад змінних оточення
├── interface.py               # Gradio інтерфейс
├── main.py                    # Основна логіка
├── prompts.py                 # Промпти
├── utils.py                   # Утиліти
├── components.py              # Компоненти
├── config/                    # Конфігурація
│   ├── __init__.py
│   ├── settings.py
│   ├── models.py
│   ├── loader.py
│   ├── validator.py
│   └── environments/
│       └── default.yaml
├── src/                       # Модулі
│   └── session/
├── embeddings/                # Embedding моделі
│   ├── __init__.py
│   └── gemini_embedding.py
├── docs/                      # Документація
└── Save_Index_Ivan/          # Індекси (якщо є локально)
```

## ⚙️ Налаштування після розгортання

### 1. Перевірте логи
- HF Spaces > Logs
- Переконайтеся, що немає помилок при завантаженні

### 2. Протестуйте функціональність
- Генерація правової позиції
- Пошук прецедентів
- Аналіз релевантності

### 3. Налаштуйте sleep timeout (опціонально)
- Settings > Sleep time
- За замовчуванням: 48 годин неактивності

## 🐛 Усунення проблем

### Проблема: "No module named 'config'"
**Рішення:** Переконайтеся, що папка `config/` повністю завантажена

### Проблема: "API key not found"
**Рішення:** 
1. Перевірте Settings > Variables and secrets
2. Переконайтеся, що ключ правильно введено
3. Перезапустіть Space (Factory reboot)

### Проблема: "File not found: Save_Index_Ivan"
**Рішення:**
Два варіанти:
1. Завантажте локальні індекси на HF Space
2. Налаштуйте AWS S3 для автоматичного завантаження

### Проблема: Memory/Disk exceeded
**Рішення:**
1. Видаліть непотрібні файли з `test_results/`, `test_docs/`
2. Використовуйте меншу модель за замовчуванням
3. Розгляньте upgrade до більшого HF Space

## 📊 Моніторинг

### Метрики для відстеження:
- CPU/RAM usage
- Disk space
- Response time
- API quota usage

### Логи:
```bash
# Перегляд логів в реальному часі
# HF Spaces > Logs > "Show logs"
```

## 🔄 Оновлення Space

### Через Git:
```bash
cd LP_2-test
git pull origin main  # Якщо є зміни на HF
# Внесіть свої зміни
git add .
git commit -m "Update: опис змін"
git push
```

### Через веб-інтерфейс:
1. Files > Edit file
2. Внесіть зміни
3. Commit changes

## 📞 Підтримка

- HF Community: https://huggingface.co/spaces/DocSA/LP_2-test/discussions
- Issues: створіть discussion на HF Space

## ✅ Чек-лист перед запуском

- [ ] `app.py` створено і налаштовано
- [ ] `README.md` (з README_HF.md) готовий
- [ ] `requirements.txt` актуальний
- [ ] API ключі додано в Secrets
- [ ] Конфігурація `config/` завантажена
- [ ] Індекси `Save_Index_Ivan/` готові (або AWS налаштовано)
- [ ] Всі `.py` файли завантажені
- [ ] Space запущено і відповідає
- [ ] Базова функціональність протестована

---

**Дата:** 10 лютого 2026 р.
**Версія:** 1.0.0
