# Уніфікація конфігурації Max Tokens

## Що було зроблено

Параметр `max_tokens` було винесено з коду в централізовану конфігурацію YAML для спрощення управління та уніфікації налаштувань.

## Зміни в конфігурації

### 1. Додано нову секцію в `config/environments/default.yaml`:

```yaml
# Generation Settings
generation:
  max_tokens:
    openai: 8192
    anthropic: 8192
    gemini: 8192
    deepseek: 8192
  max_tokens_analysis: 2000
  temperature: 0
```

### 2. Оновлено Pydantic моделі (`config/settings.py`):

Додано нові класи:
- `MaxTokensConfig` - конфігурація max_tokens для кожного провайдера
- `GenerationConfig` - загальні налаштування генерації

### 3. Експортовано нові змінні в `config/__init__.py`:

- `MAX_TOKENS_CONFIG` - словник з max_tokens для кожного провайдера
- `MAX_TOKENS_ANALYSIS` - max_tokens для аналізу (2000)
- `GENERATION_TEMPERATURE` - температура генерації (0.0)

### 4. Оновлено `main.py`:

Всі жорстко закодовані значення замінено на використання конфігурації:

**Було:**
```python
max_tokens=8192  # жорстко закодовано
temperature=0    # жорстко закодовано
```

**Стало:**
```python
max_tokens=MAX_TOKENS_CONFIG["anthropic"]  # з конфігурації
temperature=GENERATION_TEMPERATURE          # з конфігурації
```

## Переваги

✅ **Централізоване управління** - всі налаштування в одному місці (YAML)
✅ **Легке налаштування** - зміна параметрів без редагування коду
✅ **Уніфікація** - однакові значення для всіх провайдерів (можна змінювати окремо)
✅ **Типобезпека** - валідація через Pydantic
✅ **Backward compatibility** - старий код продовжує працювати

## Як змінити max_tokens

### Варіант 1: Через YAML (рекомендовано)

Відредагуйте `config/environments/default.yaml`:

```yaml
generation:
  max_tokens:
    anthropic: 16384  # збільшити для Claude
    openai: 4096      # зменшити для OpenAI
```

### Варіант 2: Через environment-specific конфігурацію

Створіть `config/environments/production.yaml` з override значеннями:

```yaml
generation:
  max_tokens:
    anthropic: 32000
```

## Тестування

Запустіть тестовий скрипт для перевірки конфігурації:

```bash
python test_max_tokens_config.py
```

Очікуваний вивід:
```
📊 MAX_TOKENS_CONFIG:
  - openai: 8192
  - anthropic: 8192
  - gemini: 8192
  - deepseek: 8192

📊 MAX_TOKENS_ANALYSIS: 2000
📊 GENERATION_TEMPERATURE: 0.0
```

## Оновлені файли

1. `config/environments/default.yaml` - додано секцію generation
2. `config/settings.py` - додано MaxTokensConfig, GenerationConfig
3. `config/__init__.py` - експортовано нові змінні
4. `main.py` - використання конфігурації замість жорстко закодованих значень
5. `test_max_tokens_config.py` - тестовий скрипт

## Рекомендації для моделі Claude Sonnet 4.5

Для оптимальної роботи з Claude Sonnet 4.5 рекомендується:

```yaml
generation:
  max_tokens:
    anthropic: 16384  # або більше для довгих текстів
  temperature: 0.0    # для детермінованих результатів
```

Модель підтримує до 200k токенів на вихід, тому можна встановити більше значення при потребі.
