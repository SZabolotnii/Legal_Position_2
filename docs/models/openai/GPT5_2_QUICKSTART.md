# GPT-5.2 Швидкий Старт

## Встановлення

```bash
# Оновіть OpenAI SDK до версії з підтримкою GPT-5.2
pip install --upgrade openai>=1.58.0
```

## Налаштування

Переконайтеся, що у вас є API ключ OpenAI з доступом до GPT-5.2:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Базове використання

### 1. Через інтерфейс додатку

```bash
python main.py
```

1. Відкрийте http://localhost:7860
2. Оберіть провайдер: **OpenAI**
3. Оберіть модель: **GPT-5.2**
4. Увімкніть **Thinking Mode**
5. Введіть текст судового рішення

### 2. Програмно

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "developer", "content": "Ти експерт-правознавець"},
        {"role": "user", "content": "Проаналізуй судове рішення..."}
    ],
    response_format={"type": "json_object"},
    reasoning_effort="medium",  # low, medium, high
    verbosity="medium",         # low, medium, high
    store=False                 # не зберігати в історії
)

print(response.choices[0].message.content)
```

## Параметри

| Параметр | Значення | Опис |
|----------|----------|------|
| `reasoning_effort` | low/medium/high | Рівень міркування |
| `verbosity` | low/medium/high | Деталізація відповіді |
| `store` | true/false | Зберігати в історії OpenAI |

## Рекомендовані налаштування

**Для правових позицій:**
- reasoning_effort: `high`
- verbosity: `medium`
- store: `false`

**Для аналізу:**
- reasoning_effort: `medium`
- verbosity: `medium`
- store: `false`

## Приклад

```python
# Генерація правової позиції
from main import generate_legal_position

result = generate_legal_position(
    input_text="Текст судового рішення...",
    input_type="text",
    comment_input="",
    provider="openai",
    model_name="gpt-5.2",
    thinking_enabled=True,
    thinking_level="HIGH"
)

print(f"Заголовок: {result['title']}")
print(f"Текст: {result['text']}")
print(f"Тип судочинства: {result['proceeding']}")
print(f"Категорія: {result['category']}")
```

## Детальна документація

Дивіться [GPT5_2_INTEGRATION.md](GPT5_2_INTEGRATION.md) для повної документації.

## Приклади коду

Дивіться [examples/gpt5_2_example.py](examples/gpt5_2_example.py) для робочих прикладів.
