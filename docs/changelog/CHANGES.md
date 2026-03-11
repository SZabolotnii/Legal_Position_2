<!--
NOTE: This changelog file is preserved for historical reference. The canonical changelog and release notes live under docs/README.md -> 'Changelog' section and docs/changelog/. Please prefer linking to docs/README.md in user-facing docs.
-->

# Changelog - Anthropic Prompt Caching

## Дата: 2026-02-25

## Зміни

### ⚡ Оптимізація: Anthropic Prompt Caching

#### Проблема
Кожен запит до Anthropic API повністю перераховував токени системного промпту та інструктажу, хоча ця частина є статичною між запитами.

#### Рішення

**1. Увімкнення автоматичного кешування (`main.py`)**

Додано параметр `cache_control={"type": "ephemeral"}` на верхній рівень обох Anthropic-викликів:
- `LLMAnalyzer._analyze_with_anthropic()` — для аналізу прецедентів
- `generate_legal_position()` — для генерації правових позицій

API автоматично визначає найдовший відповідний префікс, переміщує точку кешу до останнього кешованого блоку та повторно використовує її на кожному наступному кроці.

**2. Реструктуризація промпту (`prompts.py`)**

Змінні частини промпту (`<court_decision>`, `<comment>`) переміщено в кінець `LEGAL_POSITION_PROMPT`:

```
До:                          Після:
<task>          статичний    <task>          статичний
<court_decision> ЗМІННИЙ     <strategy>      статичний
<comment>        ЗМІННИЙ     <rules_do>      статичний  ← кешується
<strategy>      статичний    <rules_dont>    статичний
<rules_do>      статичний    <output_format> статичний
<rules_dont>      статичний    ─── точка кешу ───────────
<output_format> статичний    <court_decision> ЗМІННИЙ
                             <comment>        ЗМІННИЙ
```

Тепер весь статичний інструктаж (~1500 токенів) кешується між запитами. Повторне обчислення лише змінних блоків наприкінці.

### 📝 Змінені файли

#### `main.py`
- `LLMAnalyzer._analyze_with_anthropic()` — додано `cache_control={"type": "ephemeral"}`
- `generate_legal_position()` (Anthropic branch) — додано `cache_control={"type": "ephemeral"}` в `message_params`

#### `prompts.py`
- `LEGAL_POSITION_PROMPT` — переміщено `<court_decision>` та `<comment>` в кінець промпту після `</output_format>`

**3. OpenAI Prompt Caching (`main.py`)**

OpenAI кешує автоматично для запитів ≥ 1024 токенів — жодних параметрів API вмикати не потрібно. Реструктуризація промпту (п. 2) вже забезпечує максимальний prefix для cache hit.

Додано логування cache hits через `usage.prompt_tokens_details.cached_tokens`:
- `LLMAnalyzer._analyze_with_openai()` — `[CACHE] OpenAI analysis: X/Y input tokens from cache`
- `generate_legal_position()` (OpenAI branch) — `[CACHE] OpenAI generation: X/Y input tokens from cache`

### 💰 Очікуваний ефект
| Провайдер | Механізм | Зниження вартості | Зниження latency |
|-----------|----------|-------------------|-----------------|
| Anthropic | `cache_control` (ephemeral) + змінні блоки в кінці | до 90% | до 85% |
| OpenAI    | автоматичне (≥1024 токенів) + змінні блоки в кінці | до 50% | до 80% |

---

# Changelog - Додано редагування промптів з ізоляцією сесій

## Дата: 2025-12-28

## Зміни

(rest of file preserved)
