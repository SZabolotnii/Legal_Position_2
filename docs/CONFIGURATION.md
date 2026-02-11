# Конфігурація додатку

## 📋 Огляд

Вся конфігурація додатку зберігається в **config/environments/default.yaml** як єдине джерело істини.

Pydantic моделі в **config/settings.py** використовуються **тільки для валідації** типів та значень, без дефолтних значень.

## 🎯 Принципи

### ✅ Правильний підхід

```
YAML файл → Єдине джерело істини (всі значення)
    ↓
Pydantic → Валідація типів (БЕЗ дефолтів)
    ↓
Python код → Використання через get_settings()
```

### ❌ Неправильний підхід (дубляж)

```python
# ❌ НЕ робити так!
class AppConfig(BaseModel):
    name: str = "Legal Position"  # ← Дубляж з YAML
```

## 📁 Структура конфігурації

### config/environments/default.yaml

```yaml
# Єдине джерело істини для всіх налаштувань
app:
  name: "Legal Position AI Analyzer"
  version: "1.0.0"
  debug: false
  environment: "production"

models:
  default_provider: "gemini"  # ← Провайдер за замовчуванням
  providers:
    - openai
    - anthropic
    - gemini
    - deepseek
```

### config/settings.py

```python
# Тільки типи та валідація, БЕЗ дефолтів
class AppConfig(BaseModel):
    name: str          # ← Тільки тип
    version: str       # ← Тільки тип
    debug: bool
    environment: str
```

### config/models.py

```python
# Динамічна генерація enums з YAML
GenerationModelName = Enum(
    'GenerationModelName',
    _registry.get_generation_models(),  # ← З YAML
    type=str
)
```

## 🔧 Використання

### Отримання налаштувань

```python
from config import get_settings

settings = get_settings()

# Доступ до значень
app_name = settings.app.name
default_provider = settings.models.default_provider
timeout = settings.session.timeout_minutes
```

### Отримання моделей

```python
from config import GenerationModelName, ModelProvider

# Enum згенерований з YAML
model = GenerationModelName.GEMINI_3_FLASH

# Провайдер
provider = ModelProvider.GEMINI
```

### Зміна дефолтного провайдера

**Крок 1:** Змінити в YAML

```yaml
# config/environments/default.yaml
models:
  default_provider: "gemini"  # ← Змінити тут
```

**Крок 2:** Оновити UI (якщо потрібно)

```python
# interface.py
generation_provider_dropdown = gr.Dropdown(
    value=ModelProvider.GEMINI.value  # ← Синхронізувати
)
```

## 📊 Поточні налаштування

### Провайдери

| Параметр | Значення | Файл |
|----------|----------|------|
| Default Provider (Generation) | gemini | YAML |
| Default Provider (Analysis) | gemini | YAML |
| Default Model (Generation) | gemini-3-flash-preview | YAML |
| Default Model (Analysis) | gemini-3-flash-preview | YAML |

### Сесії

| Параметр | Значення | Опис |
|----------|----------|------|
| timeout_minutes | 30 | Таймаут сесії |
| cleanup_interval_minutes | 5 | Інтервал очистки |
| max_sessions | 1000 | Максимум сесій |
| storage_type | memory | Тип зберігання |

### LlamaIndex

| Параметр | Значення | Опис |
|----------|----------|------|
| context_window | 20000 | Розмір контексту |
| chunk_size | 2048 | Розмір чанка |
| similarity_top_k | 20 | К-сть результатів |
| embed_model | text-embedding-3-small | Модель ембедінгу |

### Gradio

| Параметр | Значення | Опис |
|----------|----------|------|
| server_name | 0.0.0.0 | Адреса сервера |
| server_port | 7860 | Порт |
| share | true | Публічний доступ |

## 🔄 Ієрархія конфігурації

```
1. Environment Variables (.env)
   ↓
2. YAML Configuration (default.yaml)
   ↓
3. Pydantic Validation (settings.py)
   ↓
4. Runtime Settings (get_settings())
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
DEEPSEEK_API_KEY=sk-...
```

### YAML приоритет

Якщо потрібно перевизначити для різних середовищ:

```
config/environments/
├── default.yaml      # ← Базові налаштування
├── development.yaml  # ← Для розробки (опціонально)
└── production.yaml   # ← Для production (опціонально)
```

## 🎨 Додавання нової моделі

### Крок 1: Додати в YAML

```yaml
# config/environments/default.yaml
models:
  generation:
    gemini:
      - name: "gemini-3-flash-preview"
        display_name: "Gemini 3 Flash"
        default: true
      - name: "gemini-4-ultra"  # ← Нова модель
        display_name: "Gemini 4 Ultra"
```

### Крок 2: Перезапустити додаток

Enum автоматично згенерується з нової конфігурації.

```python
# Автоматично доступно
from config import GenerationModelName
GenerationModelName.GEMINI_4_ULTRA  # ✅ Працює!
```

## 🔒 Валідація

### Автоматична валідація при завантаженні

```python
# config/loader.py
settings = loader.load_config(validate_api_keys=True)

# Перевіряє:
# ✅ Типи даних (int, str, bool, etc.)
# ✅ Обов'язкові поля
# ✅ Діапазони значень
# ✅ Формати (email, URL, etc.)
# ✅ API ключі (якщо validate_api_keys=True)
```

### Кастомна валідація

```python
# config/settings.py
@validator('storage_type')
def validate_storage_type(cls, v):
    allowed = ["memory", "redis"]
    if v not in allowed:
        raise ValueError(f"storage_type must be one of {allowed}")
    return v
```

## 📝 Найкращі практики

### ✅ DO

1. **Всі дефолти в YAML**
   ```yaml
   session:
     timeout_minutes: 30  # ✅
   ```

2. **Pydantic тільки для типів**
   ```python
   class SessionConfig(BaseModel):
       timeout_minutes: int  # ✅ Тільки тип
   ```

3. **Використання через get_settings()**
   ```python
   settings = get_settings()
   timeout = settings.session.timeout_minutes  # ✅
   ```

### ❌ DON'T

1. **Не дублювати значення**
   ```python
   # ❌ Неправильно
   timeout_minutes: int = 30  # Дубляж з YAML
   ```

2. **Не хардкодити в коді**
   ```python
   # ❌ Неправильно
   TIMEOUT = 30  # Має бути в YAML
   ```

3. **Не ігнорувати валідацію**
   ```python
   # ❌ Неправильно
   arbitrary_types_allowed = True  # Без необхідності
   ```

## 🐛 Troubleshooting

### Проблема: Зміни в YAML не застосовуються

**Рішення:** Перезапустити додаток

```bash
# Зупинити
Ctrl+C

# Запустити знову
python main.py
```

### Проблема: Помилка валідації

```
pydantic.error_wrappers.ValidationError:
  timeout_minutes
    field required (type=value_error.missing)
```

**Рішення:** Перевірити наявність поля в YAML

```yaml
# config/environments/default.yaml
session:
  timeout_minutes: 30  # ← Додати, якщо відсутнє
```

### Проблема: Модель не знайдена

```
AttributeError: 'GenerationModelName' has no attribute 'GEMINI_3_FLASH'
```

**Рішення:** Перевірити назву в YAML та перезапустити

```yaml
models:
  generation:
    gemini:
      - name: "gemini-3-flash-preview"  # ← Точна назва
```

## 🔍 Перевірка конфігурації

### Команда для перевірки

```python
from config import get_settings

settings = get_settings()

print(f"App: {settings.app.name}")
print(f"Default provider: {settings.models.default_provider}")
print(f"Session timeout: {settings.session.timeout_minutes}m")
```

### Очікуваний вихід

```
App: Legal Position AI Analyzer
Default provider: gemini
Session timeout: 30m
```

## 📚 Додаткова інформація

- **Повна конфігурація:** [config/environments/default.yaml](../config/environments/default.yaml)
- **Pydantic моделі:** [config/settings.py](../config/settings.py)
- **Генерація enums:** [config/models.py](../config/models.py)
- **Завантажувач:** [config/loader.py](../config/loader.py)

---

**Останнє оновлення:** 2025-12-28

**Статус:** ✅ Без дубляжів, Gemini за замовчуванням
