"""
Приклад використання GPT-5.2 в проєкті Legal Position AI Analyzer

Цей файл демонструє, як використовувати нову модель GPT-5.2 з параметрами:
- reasoning_effort: "low", "medium", "high"
- verbosity: "low", "medium", "high"
- store: False (не зберігати в історії OpenAI)
"""

import os
from openai import OpenAI

# Ініціалізація клієнта OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_with_gpt5_2(
    court_decision_text: str,
    reasoning_effort: str = "medium",
    verbosity: str = "medium"
):
    """
    Генерація правової позиції з використанням GPT-5.2
    
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
        model="gpt-5.2",
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


def analyze_with_gpt5_2(
    legal_position: dict,
    existing_positions: list,
    reasoning_effort: str = "medium"
):
    """
    Аналіз релевантності існуючих правових позицій з використанням GPT-5.2
    
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
        model="gpt-5.2",
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


# Приклад використання
if __name__ == "__main__":
    # Тестовий текст судового рішення
    test_decision = """
    ПОСТАНОВА
    ІМЕНЕМ УКРАЇНИ
    
    Верховний Суд у складі колегії суддів...
    
    [Тут має бути повний текст судового рішення]
    """
    
    # Генерація правової позиції з високим рівнем reasoning
    print("Генерація правової позиції з GPT-5.2...")
    legal_position = generate_with_gpt5_2(
        court_decision_text=test_decision,
        reasoning_effort="high",
        verbosity="high"
    )
    print(f"Результат: {legal_position}\n")
    
    # Аналіз релевантності
    print("Аналіз релевантності з GPT-5.2...")
    existing = [
        {
            "title": "Про застосування норм ЦПК",
            "text": "Верховний Суд вважає..."
        }
    ]
    
    import json
    analysis = analyze_with_gpt5_2(
        legal_position=json.loads(legal_position),
        existing_positions=existing,
        reasoning_effort="medium"
    )
    print(f"Аналіз: {analysis}")
