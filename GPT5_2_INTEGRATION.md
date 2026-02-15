# Інтеграція GPT-5.2 в Legal Position AI Analyzer

## Огляд

GPT-5.2 - це нова модель OpenAI з покращеними можливостями reasoning (міркування). Модель підтримує спеціальні параметри для контролю процесу міркування та деталізації відповідей.

## Нові можливості GPT-5.2

### 1. Reasoning Effort (Зусилля міркування)
Контролює, скільки часу модель витрачає на обдумування відповіді:
- `low` - швидка відповідь, мінімальне міркування
- `medium` - збалансований підхід (рекомендовано)
- `high` - глибоке міркування, повільніша відповідь

### 2. Verbosity (Деталізація)
Контролює рівень деталізації в поясненнях:
- `low` - стисла відповідь
- `medium` - збалансована деталізація (рекомендовано)
- `high` - максимально детальна відповідь

### 3. Store (Зберігання)
- `false` - не зберігати запит в історії OpenAI (рекомендовано для конфіденційних даних)
- `true` - зберігати для покращення моделі

## Конфігурація

### 1. Додано до YAML конфігурації

Модель GPT-5.2 додано до `config/environments/default.yaml`:

```yaml
models:
  generation:
    openai:
      - name: "gpt-5.2"
        display_name: "GPT-5.2"
      # ... інші моделі

  analysis:
    openai:
      - name: "gpt-5.2"
        display_name: "GPT-5.2"
      # ... інші моделі
```

### 2. Оновлено enum ключі

У `config/models.py` додано підтримку GPT-5.2:

```python
if model_name == 'gpt-5.2':
    return 'GPT5_2'
```

### 3. Оновлено логіку генерації

У `main.py` додано підтримку нових параметрів:

```python
# Визначення reasoning моделей
is_reasoning_model = any(m in model_name.lower() for m in ["gpt-4.1", "gpt-4.5", "gpt-5", "o1", "o3"])

# Додавання параметрів для GPT-5.2
if "gpt-5" in model_name.lower():
    completion_params["reasoning_effort"] = thinking_level.lower()
    completion_params["verbosity"] = "medium"
    completion_params["store"] = False
```

## Використання

### Через Gradio інтерфейс

1. Відкрийте додаток
2. Перейдіть до вкладки "💡 Генерація"
3. Оберіть провайдер: **OpenAI**
4. Оберіть модель: **GPT-5.2**
5. Увімкніть "Thinking Mode" для використання reasoning
6. Оберіть рівень Thinking: Low/Medium/High

### Програмно

```python
from main import generate_legal_position

result = generate_legal_position(
    input_text="Текст судового рішення...",
    input_type="text",
    comment_input="Додатковий коментар",
    provider="openai",
    model_name="gpt-5.2",
    thinking_enabled=True,
    thinking_level="MEDIUM"
)

print(result)
# {
#     "title": "...",
#     "text": "...",
#     "proceeding": "...",
#     "category": "..."
# }
```

### Прямий виклик OpenAI API

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "developer", "content": "Системний промпт"},
        {"role": "user", "content": "Запит користувача"}
    ],
    response_format={"type": "json_object"},
    reasoning_effort="medium",
    verbosity="medium",
    store=False,
    max_completion_tokens=2048
)
```

## Приклади

Дивіться `examples/gpt5_2_example.py` для детальних прикладів:

1. **Генерація правової позиції** з різними рівнями reasoning
2. **Аналіз релевантності** існуючих позицій
3. **Налаштування параметрів** для різних сценаріїв

## Рекомендації

### Для генерації правових позицій
```python
reasoning_effort="high"    # Глибоке міркування для точності
verbosity="medium"         # Збалансована деталізація
store=False               # Конфіденційність даних
```

### Для аналізу релевантності
```python
reasoning_effort="medium"  # Збалансований підхід
verbosity="medium"         # Достатня деталізація
store=False               # Конфіденційність даних
```

### Для швидких запитів
```python
reasoning_effort="low"     # Швидка відповідь
verbosity="low"           # Стисла відповідь
store=False               # Конфіденційність даних
```

## Порівняння з іншими моделями

| Модель | Reasoning | Швидкість | Точність | Вартість |
|--------|-----------|-----------|----------|----------|
| GPT-5.2 | ✅ Так | Середня | Висока | Висока |
| GPT-4.1 | ✅ Так | Середня | Висока | Середня |
| GPT-4o | ❌ Ні | Швидка | Висока | Середня |
| GPT-4o-mini | ❌ Ні | Дуже швидка | Середня | Низька |

## Обмеження

1. **Вартість**: GPT-5.2 дорожча за попередні моделі
2. **Швидкість**: Reasoning займає додатковий час
3. **API ключ**: Потрібен доступ до GPT-5.2 (може бути обмежений)

## Налагодження

Для відстеження роботи GPT-5.2 увімкнено детальне логування:

```python
print(f"[DEBUG] OpenAI Generation - Model: {model_name}")
print(f"[DEBUG] Reasoning enabled: {thinking_enabled}")
print(f"[DEBUG] Reasoning effort: {thinking_level}")
```

## Troubleshooting

### Помилка: "Model not found"
- Переконайтеся, що ваш API ключ має доступ до GPT-5.2
- Перевірте правильність назви моделі: `gpt-5.2`

### Помилка: "Invalid parameter"
- Переконайтеся, що використовуєте `developer` role замість `system`
- Перевірте, що `reasoning_effort` має значення: low/medium/high

### Повільна відповідь
- Зменшіть `reasoning_effort` до "low" або "medium"
- Зменшіть `verbosity` до "low"

## Додаткові ресурси

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [GPT-5.2 Release Notes](https://openai.com/blog/gpt-5-2)
- [Reasoning Models Guide](https://platform.openai.com/docs/guides/reasoning)

## Підтримка

Якщо у вас виникли питання або проблеми з інтеграцією GPT-5.2:

1. Перевірте логи додатку
2. Переконайтеся, що API ключ налаштовано правильно
3. Перегляньте приклади у `examples/gpt5_2_example.py`
4. Створіть issue на GitHub

---

**Версія документації**: 1.0  
**Дата оновлення**: 2026-02-15  
**Автор**: AI Assistant (Kiro)
