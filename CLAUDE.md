# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Legal Position AI Analyzer — a Gradio-based web app for analyzing Ukrainian Supreme Court decisions and generating legal positions using multiple AI providers (OpenAI, Anthropic, Google Gemini, DeepSeek). The primary language of the UI and domain content is **Ukrainian**.

The current delivery focus (MVP) is **generation of legal positions** with model/thinking settings. Search and comparative analysis are optional modules that depend on retrieval indexes.

## Commands

```bash
# Run the app locally (serves on http://localhost:7860)
python app.py

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_config.py -v

# Run tests with stdout visible
pytest tests/ -v -s

# Install dependencies
pip install -r requirements.txt

# Docker
docker build -t legal-position-ai .
docker run -p 7860:7860 --env-file .env legal-position-ai
```

There is no linter or formatter configured in the project.

## Architecture

### Entry Points
- **`app.py`** — HF Spaces entry point. Handles asyncio setup, initializes components, launches Gradio server on port 7860.
- **`main.py`** (~1600 lines) — Core logic: AI provider calls (`generate_legal_position`, `search_with_ai_action`, `analyze_action`), model selection, prompt assembly, batch processing.
- **`interface.py`** (~1300 lines) — Gradio UI definition with tabs: Generation, Search, Analysis, Settings (prompt editing), Batch Testing, Help.

### Key Modules
- **`prompts.py`** — Default system/generation/analysis prompts (Ukrainian legal domain).
- **`components.py`** — `SearchComponents` singleton holding FAISS vector index and BM25 retriever.
- **`index_loader.py`** — Loads retrieval indexes from HuggingFace Hub, S3, or local filesystem.
- **`utils.py`** — Text cleaning, URL extraction (court decision pages via BeautifulSoup).
- **`config.py`** — Re-exports from `config/` package for backward compatibility.

### Configuration System (`config/`)
- YAML-based config in `config/environments/` (default.yaml, development.yaml, production.yaml).
- Pydantic v2 settings models in `config/settings.py` — `AppConfig`, `AWSConfig`, `LlamaIndexConfig`, `GenerationConfig`, `ModelConfig`, `SessionConfig`.
- `config/loader.py` loads and merges YAML configs; `config/validator.py` validates them.

### Session Management (`src/session/`)
- Per-user session isolation via UUID4 session IDs.
- `UserSessionState` dataclass holds generated position JSON, search nodes, and custom prompts.
- `SessionManager` is async-safe (asyncio.Lock), with background cleanup (30-min timeout).
- Storage backends: `MemoryStorage` (dev) and `RedisStorage` (prod, with 24h TTL).

### Data Flow
```
User Input → Gradio UI (interface.py)
  → SessionManager (session isolation, custom prompts)
  → Core Logic (main.py)
    → AI Provider API (OpenAI/Anthropic/Gemini/DeepSeek)
    → RAG retrieval (FAISS + BM25 via LlamaIndex) [optional]
  → Structured JSON response → UI
```

### AI Provider Integration
All providers are called directly via their SDKs (not through LlamaIndex LLMs). Provider-specific features:
- **Anthropic**: Extended Thinking support, prompt caching via cache_control headers.
- **OpenAI**: Reasoning effort control (low/medium/high) for o-series/GPT-5.2+ models.
- **Google Gemini**: Thinking Mode with thinking budget.
- **DeepSeek**: Standard chat completion.

Generation output is structured JSON (legal position schema defined in `config/environments/default.yaml`).

## Environment

Requires at least one AI provider API key in `.env` (see `.env.example`):
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`

Optional: `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (S3 indexes), `REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD` (production sessions).

Python 3.10+. Deployed to Hugging Face Spaces via GitHub Actions (`.github/workflows/update_space.yml`).

## Retrieval Indexes

The app optionally loads pre-built FAISS + BM25 indexes for search/analysis. These come from `DocSA/legal-position-indexes` on HuggingFace Hub (snapshot ~1.5 years old). Without indexes, only the generation tab works.
