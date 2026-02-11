# Тести

Всі тести знаходяться в цій папці.

## Існуючі тести:

- `test_claude_models.py` - тести для моделей Claude/Anthropic
- `test_config.py` - тести конфігурації
- `test_gemini_api.py` - тести API Gemini
- `test_gemini_generation.py` - тести генерації з Gemini
- `test_session.py` - тести сесій

## Запуск тестів

Запустити всі тести:
```bash
pytest tests/ -v
```

Запустити конкретний файл:
```bash
pytest tests/test_config.py -v
```

Запустити з детальним виводом:
```bash
pytest tests/ -v -s
```
