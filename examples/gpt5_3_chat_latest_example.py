"""
Приклад та тест використання GPT-5.3-chat-latest в проєкті Legal Position AI Analyzer

Параметри моделі:
- reasoning_effort: "low", "medium", "high"
- verbosity: "low", "medium", "high"
- store: False (не зберігати в історії OpenAI)
"""

import os
import sys
from openai import OpenAI

# Ініціалізація клієнта OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-5.3-chat-latest"


def test_basic_connection():
    """Простий тест підключення до моделі."""
    print(f"Тест підключення до {MODEL_NAME}...")

    # NOTE: gpt-5.3-chat-latest supports only reasoning_effort="medium"
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "developer", "content": "Ти - правовий асистент."},
            {"role": "user", "content": "Дай коротке визначення правової позиції суду (1-2 речення)."}
        ],
        reasoning_effort="medium",
        verbosity="medium",
        store=False,
        max_completion_tokens=256
    )

    content = response.choices[0].message.content
    print(f"Відповідь: {content}")
    print(f"Використано токенів: {response.usage.total_tokens}")
    return content


def generate_legal_position(
    court_decision_text: str,
    reasoning_effort: str = "medium",
    verbosity: str = "medium"
):
    """
    Генерація правової позиції з використанням GPT-5.3-chat-latest

    Args:
        court_decision_text: Текст судового рішення
        reasoning_effort: Рівень reasoning ("low", "medium", "high")
        verbosity: Рівень деталізації відповіді ("low", "medium", "high")

    Returns:
        Згенерована правова позиція у форматі JSON
    """

    system_prompt = """Ти - експерт-правознавець, який аналізує судові рішення
    та формує правові позиції Верховного Суду України."""

    user_prompt = f"""
    Проаналізуй наступне судове рішення та сформуй правову позицію:

    <court_decision>
    {court_decision_text}
    </court_decision>

    Поверни результат у форматі JSON з полями:
    - title: заголовок правової позиції
    - text: текст правової позиції
    - proceeding: тип судочинства
    - category: категорія справи
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        reasoning_effort=reasoning_effort,
        verbosity=verbosity,
        store=False,
        max_completion_tokens=2048
    )

    return response.choices[0].message.content


def analyze_relevance(
    legal_position: dict,
    existing_positions: list,
    reasoning_effort: str = "medium"
):
    """
    Аналіз релевантності існуючих правових позицій з використанням GPT-5.3-chat-latest

    Args:
        legal_position: Згенерована правова позиція
        existing_positions: Список існуючих правових позицій
        reasoning_effort: Рівень reasoning ("low", "medium", "high")

    Returns:
        Аналіз релевантності у форматі JSON
    """

    system_prompt = """Ти - експерт-аналітик правових позицій Верховного Суду України."""

    positions_text = "\n\n".join([
        f"[{i+1}] {pos['title']}: {pos['text']}"
        for i, pos in enumerate(existing_positions)
    ])

    user_prompt = f"""
    Проаналізуй релевантність існуючих правових позицій до нової позиції:

    Нова позиція:
    {legal_position['title']}: {legal_position['text']}

    Існуючі позиції:
    {positions_text}

    Поверни аналіз у форматі JSON з полями:
    - relevant_positions: список релевантних позицій з обґрунтуванням
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        reasoning_effort=reasoning_effort,
        verbosity="medium",
        store=False,
        max_completion_tokens=4000
    )

    return response.choices[0].message.content


# Запуск тестів
if __name__ == "__main__":
    import json

    if not os.getenv("OPENAI_API_KEY"):
        print("ПОМИЛКА: Змінна OPENAI_API_KEY не встановлена.")
        sys.exit(1)

    # Тест 1: базове підключення
    print("=" * 60)
    print(f"ТЕСТ: {MODEL_NAME}")
    print("=" * 60)

    try:
        test_basic_connection()
        print("ТЕСТ 1 (підключення): OK\n")
    except Exception as e:
        print(f"ТЕСТ 1 (підключення): ПОМИЛКА - {e}\n")
        sys.exit(1)

    # Тест 2: генерація правової позиції
    test_decision = """
    ПОСТАНОВА ІМЕНЕМ УКРАЇНИ

    Верховний Суд у складі колегії суддів Касаційного цивільного суду
    розглянув у порядку письмового провадження справу за позовом фізичної особи
    до банку про захист прав споживача.

    Суд встановив, що банк нараховував комісію за обслуговування кредиту,
    яка не була передбачена кредитним договором, що є порушенням прав споживача
    відповідно до Закону України "Про захист прав споживачів".
    """

    # NOTE: gpt-5.3-chat-latest підтримує лише reasoning_effort="medium"
    print("Тест 2: Генерація правової позиції (reasoning_effort=medium)...")
    try:
        result = generate_legal_position(
            court_decision_text=test_decision,
            reasoning_effort="medium",
            verbosity="medium"
        )
        parsed = json.loads(result)
        print(f"Title: {parsed.get('title', 'N/A')}")
        print(f"Category: {parsed.get('category', 'N/A')}")
        print("ТЕСТ 2 (генерація): OK\n")
    except Exception as e:
        print(f"ТЕСТ 2 (генерація): ПОМИЛКА - {e}\n")
        sys.exit(1)

    # Тест 3: аналіз релевантності
    print("Тест 3: Аналіз релевантності...")
    existing = [
        {
            "title": "Про нарахування незаконних комісій банком",
            "text": "Банк не має права нараховувати комісії, не передбачені договором."
        }
    ]
    try:
        analysis = analyze_relevance(
            legal_position=parsed,
            existing_positions=existing,
            reasoning_effort="medium"
        )
        print(f"Аналіз: {analysis[:200]}...")
        print("ТЕСТ 3 (аналіз): OK\n")
    except Exception as e:
        print(f"ТЕСТ 3 (аналіз): ПОМИЛКА - {e}\n")
        sys.exit(1)

    print("=" * 60)
    print("Всі тести пройшли успішно!")
