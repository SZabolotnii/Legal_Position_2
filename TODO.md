# TODO: Refactoring Legal Position AI Analyzer

## Status: Phase 2 COMPLETED ✅ + Prompt Editing Feature ✅

**Останнє оновлення:** 2025-12-28

---

## ✨ НОВЕ: Prompt Editing Feature (COMPLETED ✅)

### Реалізовано 2025-12-28:

- [x] Розширено UserSessionState з полем custom_prompts
- [x] Додано методи get_prompt(), set_prompt(), reset_prompts()
- [x] Оновлено серіалізацію (to_dict/from_dict)
- [x] Інтегровано Session Manager з Gradio інтерфейсом
- [x] Додано вкладку "⚙️ Налаштування" з редакторами промптів
- [x] Реалізовано save_custom_prompts() для збереження
- [x] Реалізовано reset_prompts_to_default() для скидання
- [x] Реалізовано load_session_prompts() для завантаження
- [x] Оновлено generate_legal_position() для підтримки кастомних промптів
- [x] Оновлено всі AI провайдери (OpenAI, Anthropic, Gemini, DeepSeek)
- [x] Написано повну документацію (PROMPT_EDITING.md)
- [x] Написано швидкий старт (QUICK_START_PROMPTS.md)
- [x] Створено архітектурну схему (ARCHITECTURE.md)
- [x] Оновлено README.md з детальною інформацією
- [x] Створено CHANGES.md з повним changelog

### Можливі покращення в майбутньому:

- [ ] Експорт/імпорт промптів у JSON/YAML формат
- [ ] Бібліотека готових шаблонів промптів
- [ ] Версіонування промптів (історія змін)
- [ ] A/B тестування різних промптів з метриками
- [ ] Адміністративна панель для глобальних промптів
- [ ] Можливість шерингу промптів між користувачами
- [ ] Автоматичне збереження вдалих промптів
- [ ] Рекомендації по покращенню промптів на основі AI

---

## Phase 1: YAML Configuration (HIGH PRIORITY)

### 1.1 Create configuration structure
- [x] Create config/ directory
- [x] Create config/__init__.py
- [x] Create config/environments/ directory
- [x] Create config/environments/default.yaml
- [x] Create config/environments/development.yaml
- [x] Create config/environments/production.yaml

### 1.2 Pydantic models
- [x] Create config/settings.py with Pydantic models
- [x] AppConfig - general app settings
- [x] AWSConfig - AWS/S3 settings
- [x] LlamaIndexConfig - LlamaIndex settings
- [x] ModelConfig - models configuration
- [x] SessionConfig - session settings
- [x] LoggingConfig - logging settings
- [x] Settings - main configuration class

### 1.3 Configuration loader
- [ ] Create config/loader.py
- [ ] ConfigLoader class with load_yaml() method
- [ ] merge_configs() method (default + environment)
- [ ] validate_config() method
- [ ] Support environment variables in YAML

### 1.4 Validator
- [x] Create config/validator.py
- [x] Validate required fields
- [x] Validate API keys
- [x] Validate file paths
- [x] Validate models

### 1.5 Refactor config.py
- [ ] Remove hardcoded values
- [ ] Keep only Enum classes
- [ ] Add get_settings() function
- [ ] Update validate_environment()
- [ ] Update imports in other files

---

## Phase 2: Session Management (HIGH PRIORITY)

### 2.1 Create session structure
- [ ] Create src/ directory
- [ ] Create src/session/ directory
- [ ] Create src/session/__init__.py

### 2.2 Session manager
- [x] Create src/session/manager.py
- [x] SessionManager class with get_session() method
- [x] cleanup_session() method
- [x] cleanup_expired_sessions() background task
- [x] Thread-safe operations with asyncio.Lock

### 2.3 Session state
- [ ] Create src/session/state.py
- [ ] UserSessionState dataclass
- [ ] Fields: session_id, legal_position_json, search_nodes
- [ ] Timestamps: created_at, last_activity
- [ ] update_activity() method

### 2.4 Session storage
- [x] Create src/session/storage.py
- [x] BaseStorage abstract class
- [x] MemoryStorage implementation
- [x] RedisStorage implementation (optional)
- [x] Storage factory

### 2.5 Update interface.py
- [ ] Add SessionManager initialization
- [ ] Add session_id State for each user
- [ ] Update all handlers to use session-based state
- [ ] Remove global state variables
- [ ] Add session cleanup on disconnect

---

## Phase 3: Refactor main.py

### 3.1 Create LLM providers structure
- [ ] Create src/llm/ directory
- [ ] Create src/llm/__init__.py

### 3.2 Base LLM provider
- [ ] Create src/llm/base.py
- [ ] BaseLLMProvider abstract class
- [ ] analyze() abstract method
- [ ] generate() abstract method
- [ ] Common error handling

### 3.3 Specific providers
- [ ] Create src/llm/openai.py - OpenAIProvider
- [ ] Create src/llm/anthropic.py - AnthropicProvider
- [ ] Create src/llm/gemini.py - GeminiProvider
- [ ] Create src/llm/deepseek.py - DeepSeekProvider

### 3.4 LLM factory
- [ ] Create src/llm/factory.py
- [ ] LLMFactory class
- [ ] create_provider() method
- [ ] Provider registry

### 3.5 Create services
- [ ] Create src/services/ directory
- [ ] Create src/services/__init__.py
- [ ] Create src/services/generation.py - GenerationService
- [ ] Create src/services/search.py - SearchService
- [ ] Create src/services/analysis.py - AnalysisService

### 3.6 Create workflows
- [ ] Create src/workflows/ directory
- [ ] Create src/workflows/__init__.py
- [ ] Move PrecedentAnalysisWorkflow to src/workflows/precedent_analysis.py

### 3.7 Create storage
- [ ] Create src/storage/ directory
- [ ] Create src/storage/__init__.py
- [ ] Create src/storage/s3.py - S3Storage
- [ ] Create src/storage/local.py - LocalStorage

### 3.8 Update main.py
- [ ] Remove LLMAnalyzer class (moved to providers)
- [ ] Remove PrecedentAnalysisWorkflow (moved to workflows)
- [ ] Remove generate_legal_position (moved to services)
- [ ] Remove search functions (moved to services)
- [ ] Remove analyze_action (moved to services)
- [ ] Keep only initialization and app launch

---

## Phase 4: Error Handling and Logging

### 4.1 Custom exceptions
- [ ] Create src/exceptions.py
- [ ] LegalPositionError base exception
- [ ] ConfigurationError
- [ ] LLMProviderError
- [ ] SearchError
- [ ] SessionError

### 4.2 Logging configuration
- [ ] Create src/logging_config.py
- [ ] Setup logging from YAML config
- [ ] Add file and console handlers
- [ ] Add log rotation

### 4.3 Middleware
- [ ] Create src/middleware/ directory
- [ ] Create src/middleware/__init__.py
- [ ] Create src/middleware/error_handler.py
- [ ] Create src/middleware/rate_limiter.py

### 4.4 Update all modules
- [ ] Add logging to all services
- [ ] Add proper error handling
- [ ] Add try-except blocks with custom exceptions

---

## Phase 5: Additional Improvements

### 5.1 Validation
- [ ] Add Pydantic models for input validation
- [ ] Validate user inputs in interface.py
- [ ] Sanitize outputs

### 5.2 Testing
- [ ] Create tests/ directory
- [ ] Add pytest configuration
- [ ] Write unit tests for services
- [ ] Write integration tests
- [ ] Add test coverage reporting

### 5.3 Documentation
- [ ] Update README.md with new structure
- [ ] Add docstrings to all classes and methods
- [ ] Create API documentation
- [ ] Add usage examples

### 5.4 Hugging Face optimization
- [ ] Add health check endpoint
- [ ] Optimize memory usage
- [ ] Add graceful shutdown
- [ ] Add performance monitoring
- [ ] Test on Hugging Face Spaces

### 5.5 CI/CD
- [ ] Create .github/workflows/ directory
- [ ] Add GitHub Actions for testing
- [ ] Add linting (flake8, mypy)
- [ ] Add automatic deployment to Hugging Face

---

## Dependencies to add

- [ ] pyyaml - for YAML configuration
- [ ] pydantic - for configuration validation
- [ ] pydantic-settings - for settings management
- [ ] redis (optional) - for session storage
- [ ] pytest - for testing
- [ ] pytest-asyncio - for async tests
- [ ] pytest-cov - for coverage
- [ ] mypy - for type checking
- [ ] flake8 - for linting

---

## Notes

- Start with Phase 1 (YAML Configuration)
- Then Phase 2 (Session Management) - critical for Hugging Face
- Phase 3 can be done incrementally
- Phases 4-5 are lower priority but important for production

---

## Current Progress

- [x] Project analysis completed
- [x] Refactoring plan created
- [x] Phase 1: YAML Configuration - COMPLETED ✅
