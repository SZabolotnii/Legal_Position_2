# 🔑 Налаштування API ключів для HF Space

## Обов'язкові кроки

### 1. Відкрийте налаштування Space:
https://huggingface.co/spaces/DocSA/LP_2-test/settings

### 2. Перейдіть до секції "Variables and secrets"

### 3. Додайте API ключі:

#### Обов'язково (мінімум один):

**Anthropic Claude** (рекомендовано):
```
Name: ANTHROPIC_API_KEY
Value: sk-ant-...
```

#### Опціонально:

**OpenAI GPT**:
```
Name: OPENAI_API_KEY
Value: sk-proj-...
```

**Google Gemini**:
```
Name: GEMINI_API_KEY
Value: AI...
```

**DeepSeek**:
```
Name: DEEPSEEK_API_KEY
Value: sk-...
```

### 4. Збережіть та перезапустіть Space

Space автоматично перезапуститься після додавання ключів.

## ✅ Перевірка

Після запуску Space:
1. Перейдіть на https://huggingface.co/spaces/DocSA/LP_2-test
2. У вкладці "Logs" перевірте:
   - `📦 Preparing vector database indexes...` - завантаження індексів
   - `✅ Indexes downloaded successfully` - індекси завантажені
   - `🚀 Starting Legal Position AI Analyzer` - додаток запущено

## 📊 Статус індексів

Індекси завантажуються автоматично з датасету:
https://huggingface.co/datasets/DocSA/legal-position-indexes

Розмір: ~530 MB
Час завантаження: 1-2 хвилини при першому запуску

## 🔧 Налаштування (опціонально)

Якщо хочете використати власні індекси з AWS S3:

```
Name: AWS_ACCESS_KEY_ID
Value: AKIA...

Name: AWS_SECRET_ACCESS_KEY
Value: your_secret_key

Name: S3_BUCKET_NAME
Value: your-bucket

Name: S3_INDEX_PREFIX
Value: legal-position-indexes/
```

## ⚠️ Важливо

- API ключі зберігаються як **Secrets** - вони недоступні публічно
- Для Anthropic рекомендуємо модель Claude Sonnet 4.5 (за замовчуванням)
- Переконайтесь що ваш API ключ має достатній баланс

## 🎯 Готово!

Після налаштування ключів ваш Legal Position AI Analyzer готовий до роботи:
https://huggingface.co/spaces/DocSA/LP_2-test
