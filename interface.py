import gradio as gr
import asyncio
import json
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from config import (
    ModelProvider, GenerationModelName, AnalysisModelName, get_settings,
    DEFAULT_GENERATION_MODEL, DEFAULT_ANALYSIS_MODEL,
    get_generation_models_by_provider, get_analysis_models_by_provider,
)
from utils import clean_text
from main import (
    generate_legal_position,
    search_with_ai_action,
    analyze_action,
    search_with_raw_text,
    get_available_providers
)
from prompts import SYSTEM_PROMPT, LEGAL_POSITION_PROMPT, PRECEDENT_ANALYSIS_TEMPLATE
from src.session.manager import get_session_manager
from src.session.state import generate_session_id


# Load help content from HELP.md
def load_help_content() -> str:
    """Load help content from HELP.md file."""
    try:
        help_file = Path(__file__).parent / "HELP.md"
        with open(help_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Помилка завантаження довідки: {str(e)}"


def get_available_provider_choices() -> list:
    """Get list of available AI providers based on API key availability."""
    available = get_available_providers()
    return [p.value for p in ModelProvider if available.get(p.value, False)]


def update_generation_model_choices(provider: str) -> gr.Dropdown:
    """Update generation model choices based on provider selection."""
    if provider == ModelProvider.OPENAI.value:
        return gr.Dropdown(
            choices=[m.value for m in GenerationModelName if m.value.startswith("ft:") or m.value.startswith("gpt")],
            value=GenerationModelName.GPT5_2.value,
            label="Модель генерації"
        )
    if provider == ModelProvider.DEEPSEEK.value:
        return gr.Dropdown(
            choices=[m.value for m in GenerationModelName if m.value.startswith("deepseek")],
            value=GenerationModelName.DEEPSEEK_CHAT.value,
            label="Модель генерації"
        )
    elif provider == ModelProvider.ANTHROPIC.value:
        return gr.Dropdown(
            choices=[m.value for m in GenerationModelName if m.value.startswith("claude")],
            value=GenerationModelName.CLAUDE_SONNET_4_6.value,
            label="Модель генерації"
        )
    else:  # GEMINI
        return gr.Dropdown(
            choices=[m.value for m in GenerationModelName if m.value.startswith("gemini")],
            value=GenerationModelName.GEMINI_3_FLASH.value,
            label="Модель генерації"
        )

def update_thinking_visibility(provider: str) -> gr.update:
    """Show/hide thinking controls based on provider."""
    return gr.update(visible=(provider in [ModelProvider.GEMINI.value, ModelProvider.ANTHROPIC.value, ModelProvider.OPENAI.value]))

def update_thinking_level_interactive(thinking_enabled: bool) -> tuple:
    """Enable/disable thinking controls based on checkbox."""
    return (
        gr.Dropdown(interactive=thinking_enabled),
        gr.Dropdown(interactive=thinking_enabled),
        gr.Slider(interactive=thinking_enabled)
    )


# Session and prompt management functions
async def save_custom_prompts(
    session_id: str,
    system_prompt: str,
    lp_prompt: str,
    analysis_prompt: str
) -> Tuple[str, str]:
    """Save custom prompts to user session."""
    try:
        manager = get_session_manager()
        session = await manager.get_session(session_id)

        # Validate prompt lengths
        max_length = 50000
        if len(system_prompt) > max_length or len(lp_prompt) > max_length or len(analysis_prompt) > max_length:
            return "❌ Помилка: Промпт занадто довгий (максимум 50000 символів)", session_id

        # Save prompts
        session.set_prompt('system', system_prompt)
        session.set_prompt('legal_position', lp_prompt)
        session.set_prompt('analysis', analysis_prompt)

        await manager.update_session(session)

        return "✅ Промпти успішно збережено для вашої сесії", session_id
    except Exception as e:
        return f"❌ Помилка при збереженні промптів: {str(e)}", session_id


async def reset_prompts_to_default(session_id: str) -> Tuple[str, str, str, str, str]:
    """Reset prompts to default values."""
    try:
        manager = get_session_manager()
        session = await manager.get_session(session_id)

        session.reset_prompts()
        await manager.update_session(session)

        return (
            SYSTEM_PROMPT,
            LEGAL_POSITION_PROMPT,
            str(PRECEDENT_ANALYSIS_TEMPLATE.template),
            "✅ Промпти скинуто до стандартних значень",
            session_id
        )
    except Exception as e:
        return (
            SYSTEM_PROMPT,
            LEGAL_POSITION_PROMPT,
            str(PRECEDENT_ANALYSIS_TEMPLATE.template),
            f"❌ Помилка: {str(e)}",
            session_id
        )


async def load_session_prompts(session_id: str) -> Tuple[str, str, str]:
    """Load prompts from user session."""
    try:
        manager = get_session_manager()
        session = await manager.get_session(session_id)

        system = session.get_prompt('system', SYSTEM_PROMPT)
        legal_position = session.get_prompt('legal_position', LEGAL_POSITION_PROMPT)
        analysis = session.get_prompt('analysis', str(PRECEDENT_ANALYSIS_TEMPLATE.template))

        return system, legal_position, analysis
    except Exception as e:
        print(f"Error loading prompts: {e}")
        return SYSTEM_PROMPT, LEGAL_POSITION_PROMPT, str(PRECEDENT_ANALYSIS_TEMPLATE.template)

def update_analysis_model_choices(provider: str) -> gr.Dropdown:
    """Update analysis model choices based on provider selection."""
    if provider == ModelProvider.OPENAI.value:
        return gr.Dropdown(
            choices=[m.value for m in AnalysisModelName if m.value.startswith("gpt")],
            value=AnalysisModelName.GPT5_2.value,
            label="Модель аналізу"
        )
    elif provider == ModelProvider.DEEPSEEK.value:
        return gr.Dropdown(
            choices=[m.value for m in AnalysisModelName if m.value.startswith("deepseek")],
            value=AnalysisModelName.DEEPSEEK_CHAT.value,
            label="Модель аналізу"
        )
    elif provider == ModelProvider.ANTHROPIC.value:
        return gr.Dropdown(
            choices=[m.value for m in AnalysisModelName if m.value.startswith("claude")],
            value=AnalysisModelName.CLAUDE_SONNET_4_6.value,
            label="Модель аналізу"
        )
    else:  # GEMINI
        return gr.Dropdown(
            choices=[m.value for m in AnalysisModelName if m.value.startswith("gemini")],
            value=AnalysisModelName.GEMINI_3_FLASH.value,
            label="Модель аналізу"
        )


async def process_input(
        text_input: str,
        url_input: str,
        file_input: gr.File,
        comment_input: str,
        input_method: str,
        provider: str,
        model_name: str,
        thinking_enabled: bool = False,
        thinking_type: str = "Adaptive",
        thinking_level: str = "MEDIUM",
        openai_verbosity: str = "medium",
        thinking_budget: int = 10000,
        temperature: float = 0.5,
        max_tokens: int = 4000,
        session_id: str = None
) -> Tuple[str, Optional[Dict[str, Any]], str]:
    """Process input and generate legal position."""
    try:
        input_type = "text"
        input_text = ""

        # Determine which input source has actual content
        if input_method == "Завантаження файлу":
            if not file_input:
                return "❌ Помилка: Будь ласка, завантажте файл", None, session_id
            try:
                with open(file_input.name, 'r', encoding='utf-8') as file:
                    input_text = file.read()
            except UnicodeDecodeError:
                with open(file_input.name, 'r', encoding='cp1251') as file:
                    input_text = file.read()
        elif input_method == "URL посилання":
            input_type = "url"
            input_text = url_input
        else:
            # Default to text input, but check if URL is provided instead
            if url_input and url_input.strip():
                input_type = "url"
                input_text = url_input
            else:
                input_text = text_input

        # Check if input is empty and provide specific error message
        if not input_text or not input_text.strip():
            if input_method == "URL посилання" or (url_input and url_input.strip()):
                return "❌ Помилка: Будь ласка, введіть URL посилання на судове рішення", None, session_id
            elif input_method == "Текстовий ввід":
                return "❌ Помилка: Будь ласка, введіть текст судового рішення", None, session_id
            else:
                return "❌ Помилка: Текст не може бути порожнім", None, session_id

        # Get custom prompts from session
        manager = get_session_manager()
        session = await manager.get_session(session_id)

        custom_system_prompt = session.get_prompt('system', SYSTEM_PROMPT)
        custom_lp_prompt = session.get_prompt('legal_position', LEGAL_POSITION_PROMPT)

        # Don't clean here - let generate_legal_position handle it to avoid double cleaning
        # input_text = clean_text(input_text)
        # comment_input = clean_text(comment_input) if comment_input else ""

        legal_position_json = generate_legal_position(
            input_text,
            input_type,
            comment_input if comment_input else "",
            provider,
            model_name,
            thinking_enabled,
            thinking_type,
            thinking_level,
            openai_verbosity,
            thinking_budget,
            temperature,
            max_tokens,
            custom_system_prompt,
            custom_lp_prompt
        )

        if isinstance(legal_position_json, dict) and all(
                key in legal_position_json for key in ["title", "text", "proceeding", "category"]):
            position_output_content = (
                f"**Проект правової позиції суду (модель: {model_name}):**\n"
                f"*{clean_text(legal_position_json['title'])}*\n\n"
                f"{clean_text(legal_position_json['text'])}\n\n"
                f"**Категорія:**\n"
                f"{clean_text(legal_position_json['category'])} ({clean_text(legal_position_json['proceeding'])})\n\n"
            )

            # Store in session
            session.legal_position_json = legal_position_json
            await manager.update_session(session)

            return position_output_content, legal_position_json, session_id
        else:
            return f"Помилка: Неправильний формат відповіді від моделі", None, session_id

    except Exception as e:
        return f"Помилка при генерації позиції: {str(e)}", None, session_id


async def process_raw_text_search(text, url, file, method, state_lp_json):
    """Process raw text search and update necessary states."""
    try:
        input_text = ""
        # Determine which input source has actual content
        if method == "Завантаження файлу":
            if not file:
                return "❌ Помилка: Будь ласка, завантажте файл", None, state_lp_json
            try:
                with open(file.name, 'r', encoding='utf-8') as f:
                    input_text = f.read()
            except UnicodeDecodeError:
                with open(file.name, 'r', encoding='cp1251') as f:
                    input_text = f.read()
        elif method == "URL посилання":
            input_text = url
        else:
            # Default to text input, but check if URL is provided instead
            if url and url.strip():
                input_text = url
            else:
                input_text = text

        # Check if input is empty and provide specific error message
        if not input_text or not input_text.strip():
            if method == "URL посилання" or (url and url.strip()):
                return "❌ Помилка: Будь ласка, введіть URL посилання на судове рішення", None, state_lp_json
            elif method == "Текстовий ввід":
                return "❌ Помилка: Будь ласка, введіть текст судового рішення", None, state_lp_json
            else:
                return "❌ Помилка: Порожній текст", None, state_lp_json

        input_text = clean_text(input_text)

        search_result, nodes = await search_with_raw_text(input_text)

        if not state_lp_json:
            state_lp_json = {
                "title": "Пошук за текстом",
                "text": input_text[:500] + "..." if len(input_text) > 500 else input_text,
                "proceeding": "Не визначено",
                "category": "Пошук за текстом"
            }

        if nodes is None:
            return "Помилка: Не знайдено результатів", None, state_lp_json

        return search_result, nodes, state_lp_json

    except Exception as e:
        return f"Помилка при пошуку: {str(e)}", None, state_lp_json


# Batch testing functions
async def load_data_file(file) -> Tuple[str, Optional[pd.DataFrame]]:
    """Load CSV or Excel file and validate it has a 'text' column."""
    try:
        if file is None:
            return "Помилка: Файл не вибрано", None

        file_path = Path(file.name)
        file_ext = file_path.suffix.lower()

        if file_ext in ['.xlsx', '.xls']:
            try:
                # Read Excel
                df = pd.read_excel(file.name)
            except Exception as e:
                return f"Помилка читання Excel: {str(e)}", None
        else:
            # Try to read CSV with different encodings and automatic separator detection
            encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin1']
            df = None
            last_error = ""

            for enc in encodings:
                try:
                    # Use sep=None, engine='python' for automatic separator detection
                    # Use on_bad_lines='warn' to skip problematic lines if they occur
                    df = pd.read_csv(file.name, sep=None, engine='python', encoding=enc, on_bad_lines='warn')
                    break
                except Exception as e:
                    last_error = str(e)
                    continue

            if df is None:
                return f"Помилка читання CSV: {last_error}", None

        # Validate 'text' column exists
        if 'text' not in df.columns:
            return f"Помилка: Файл повинен містити колонку 'text'. Знайдені колонки: {', '.join(df.columns)}", None

        # Show preview
        rows_count = len(df)
        preview_msg = f"✅ Файл {file_path.name} завантажено успішно!\n\n**Кількість рядків:** {rows_count}\n\n**Колонки:** {', '.join(df.columns)}\n\n**Перші 3 рядки (текст):**\n"
        for idx, row in df.head(3).iterrows():
            text_preview = str(row['text'])[:100] + "..." if len(str(row['text'])) > 100 else str(row['text'])
            preview_msg += f"\n{idx + 1}. {text_preview}\n"

        return preview_msg, df

    except Exception as e:
        return f"Помилка при завантаженні файлу: {str(e)}", None


async def process_batch_testing(
    df: pd.DataFrame,
    provider: str,
    model_name: str,
    delay_seconds: float = 1.0,
    thinking_enabled: bool = False,
    thinking_type: str = "Adaptive",
    thinking_level: str = "medium",
    openai_verbosity: str = "medium",
    thinking_budget: int = 10000,
    temperature: float = 0.5,
    max_tokens: int = 4000,
    progress=gr.Progress()
) -> Tuple[str, Optional[str]]:
    """Process batch testing of legal position generation."""
    try:
        if df is None:
            return "Помилка: Спочатку завантажте CSV файл", None

        total_rows = len(df)
        results = []

        # Create column name based on model
        result_column_name = model_name

        progress(0, desc="Початок пакетної генерації...")

        for idx, row in df.iterrows():
            # Update progress
            current_progress = (idx + 1) / total_rows
            progress(current_progress, desc=f"Обробка рядка {idx + 1} з {total_rows}")

            court_decision_text = str(row['text'])

            # Skip rows where cell values match column names — these are duplicate header rows
            col_values = {str(col): str(row[col]) for col in row.index}
            header_matches = sum(1 for col, val in col_values.items() if val == col)
            if header_matches >= max(1, len(col_values) // 2):
                results.append("ПРОПУЩЕНО: рядок містить назви колонок (дублікат заголовка)")
                continue

            # Generate legal position
            try:
                legal_position_json = generate_legal_position(
                    input_text=court_decision_text,
                    input_type="text",
                    comment_input="",
                    provider=provider,
                    model_name=model_name,
                    thinking_enabled=thinking_enabled,
                    thinking_type=thinking_type,
                    thinking_level=thinking_level,
                    openai_verbosity=openai_verbosity,
                    thinking_budget=thinking_budget,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Store full JSON result
                if isinstance(legal_position_json, dict):
                    # Convert dict to JSON string for CSV storage
                    result_text = json.dumps(legal_position_json, ensure_ascii=False)
                else:
                    result_text = f"Помилка: {str(legal_position_json)}"

            except Exception as e:
                result_text = f"Помилка генерації: {str(e)}"

            results.append(result_text)

            # Add delay between requests (except for the last one)
            if idx < total_rows - 1 and delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

        # Add results to dataframe
        df[result_column_name] = results

        # Save to temporary file
        output_dir = Path("test_results")
        output_dir.mkdir(exist_ok=True)

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        thinking_tag = "_thinking" if thinking_enabled else ""
        output_filename = f"batch_test_results_{model_name}{thinking_tag}_{timestamp}.csv"
        output_path = output_dir / output_filename

        df.to_csv(output_path, index=False, encoding='utf-8')

        success_msg = f"✅ **Пакетне тестування завершено!**\n\n"
        success_msg += f"**Оброблено рядків:** {total_rows}\n"
        success_msg += f"**Модель:** {model_name}\n"
        success_msg += f"**Температура:** {temperature} | **Max Tokens:** {max_tokens}\n"
        success_msg += f"**Результати збережено в:** {output_path}\n\n"
        success_msg += f"**Нова колонка:** {result_column_name}\n"

        return success_msg, str(output_path)

    except Exception as e:
        return f"Помилка при пакетному тестуванні: {str(e)}", None


def create_gradio_interface() -> gr.Blocks:
    """Create and configure the Gradio interface."""
    
    # Load theme and CSS from YAML config
    try:
        settings = get_settings(validate_api_keys=False)
        gradio_cfg = settings.gradio
        
        # Build theme from config
        theme_map = {
            "Soft": gr.themes.Soft,
            "Default": gr.themes.Default,
            "Glass": gr.themes.Glass,
            "Monochrome": gr.themes.Monochrome,
            "Base": gr.themes.Base,
        }
        theme_cls = theme_map.get(gradio_cfg.theme.base, gr.themes.Soft)
        theme = theme_cls(
            primary_hue=gradio_cfg.theme.primary_hue,
            secondary_hue=gradio_cfg.theme.secondary_hue,
        )
        custom_css = gradio_cfg.css or ""
    except Exception as e:
        print(f"[WARNING] Could not load Gradio config from YAML: {e}, using defaults")
        theme = gr.themes.Soft(primary_hue="blue", secondary_hue="indigo")
        custom_css = """
            .contain { display: flex; flex-direction: column; }
            .tab-content { padding: 16px; border-radius: 8px; background: white; }
            .header { margin-bottom: 24px; text-align: center; }
            .tab-header { font-size: 1.2em; margin-bottom: 16px; color: #2563eb; }
        """
    
    # Resolve default provider and models from YAML config
    try:
        _settings = get_settings(validate_api_keys=False)
        _default_provider = _settings.models.default_provider  # e.g. "anthropic"
    except Exception:
        _default_provider = "anthropic"
    
    # Get available providers based on API key availability
    _available_providers = get_available_provider_choices()
    
    # If default provider is not available, use first available one
    if _default_provider not in _available_providers:
        if _available_providers:
            _default_provider = _available_providers[0]
            print(f"[WARNING] Default provider not available, using: {_default_provider}")
        else:
            print("[ERROR] No AI providers available! Please set at least one API key.")
            _default_provider = "anthropic"  # Fallback for UI rendering
    
    # Get default generation model for the provider
    _gen_models = get_generation_models_by_provider(_default_provider)
    if DEFAULT_GENERATION_MODEL and DEFAULT_GENERATION_MODEL.value in _gen_models:
        _default_gen_model = DEFAULT_GENERATION_MODEL.value
    elif _gen_models:
        _default_gen_model = _gen_models[0]
    else:
        _default_gen_model = None
    
    # Get default analysis model for the provider
    _ana_models = get_analysis_models_by_provider(_default_provider)
    if DEFAULT_ANALYSIS_MODEL and DEFAULT_ANALYSIS_MODEL.value in _ana_models:
        _default_ana_model = DEFAULT_ANALYSIS_MODEL.value
    elif _ana_models:
        _default_ana_model = _ana_models[0]
    else:
        _default_ana_model = None
    
    print(f"[CONFIG] Default provider: {_default_provider}")
    print(f"[CONFIG] Default generation model: {_default_gen_model}")
    print(f"[CONFIG] Default analysis model: {_default_ana_model}")
    
    with gr.Blocks(
            title="AI Асистент LP 2.0",
    ) as app:
        # Apply theme and css directly to the Blocks object
        app.theme = theme
        app.css = custom_css or """
            .contain { display: flex; flex-direction: column; }
            .tab-content { padding: 16px; border-radius: 8px; background: white; border: 1px solid #e5e7eb; }
            .header-container { 
                text-align: center; 
                margin-bottom: 2rem; 
                padding: 1rem;
                background: linear-gradient(to right, #f8fafc, #ffffff, #f8fafc);
                border-bottom: 1px solid #e2e8f0;
            }
            .header-title { 
                font-size: 2.5rem; 
                font-weight: 700; 
                color: #1e293b;
                margin-bottom: 0.5rem;
            }
            .header-subtitle { 
                font-size: 1.25rem; 
                color: #475569;
                font-weight: 400;
            }
            .tab-header { 
                font-size: 1.5rem; 
                font-weight: 600; 
                margin-bottom: 1rem; 
                color: #334155; 
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 0.5rem;
            }
            .custom-btn-primary {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                border: none;
                color: white;
            }
        """
        
        # New Header Design
        gr.HTML(
            """
            <div class="header-container">
                <div class="header-title">⚖️ Legal Position AI</div>
                <div class="header-subtitle">Інтелектуальний AI-Асистент для аналізу судової практики Верховного Суду</div>
            </div>
            """
        )
        
        # Show provider availability status
        _all_providers = {p.value for p in ModelProvider}
        _unavailable = _all_providers - set(_available_providers)
        if _unavailable:
            unavailable_list = ", ".join(sorted(_unavailable))
            gr.Info(
                f"⚠️ Недоступні провайдери (відсутні API ключі): {unavailable_list}\n"
                f"Додайте відповідні API ключі в налаштуваннях HF Space для активації.",
                title="Інформація про провайдери",
                duration=10
            )

        # Session state - generates unique ID for each browser session
        session_id_state = gr.State(value=generate_session_id)
        
        # Tracks current input method ("Текстовий ввід", "URL посилання", "Завантаження файлу")
        # Initialize with "URL посилання" as it's the most common use case maybe? Or stick to input.
        # Let's default to "URL посилання" as requested in similar contexts, or keep "Текстовий ввід". 
        # User screen showed "URL посилання", let's make that default if we want user friendly.
        # But for now I'll stick to logic below.
        input_method_state = gr.State(value="Текстовий ввід")

        # Legacy states
        state_lp_json = gr.State()
        state_nodes = gr.State()

        with gr.Tabs(selected=0) as tabs:
            # Вкладка Генерація
            with gr.Tab("💡 Генерація", id=0):
                
                with gr.Row():
                    # Configuration Column
                    with gr.Column(scale=3, variant="panel"):
                        gr.Markdown("### 🤖 Налаштування моделі")
                        with gr.Row():
                            generation_provider_dropdown = gr.Dropdown(
                                choices=_available_providers,
                                value=_default_provider,
                                label="Провайдер AI",
                                container=False,
                                scale=1
                            )
                            generation_model_dropdown = gr.Dropdown(
                                choices=_gen_models,
                                value=_default_gen_model,
                                label="Модель генерації",
                                container=False,
                                scale=2
                            )
                        
                        # Advanced Settings in Accordion to save space
                        with gr.Accordion("⚙️ Додаткові параметри", open=False) as thinking_accordion:
                            with gr.Row():
                                generation_temp_slider = gr.Slider(
                                    minimum=0.0,
                                    maximum=2.0,
                                    value=0.5,
                                    step=0.1,
                                    label="Температура генерації (креативність)"
                                )
                                generation_max_tokens_slider = gr.Slider(
                                    minimum=512,
                                    maximum=32768,
                                    value=4000,
                                    step=512,
                                    label="Max Tokens (ліміт відповіді)"
                                )
                            thinking_enabled_checkbox = gr.Checkbox(
                                label="Увімкнути режим Thinking (глибокий аналіз)",
                                value=False,
                                info="Активує розширений ланцюг міркувань (Gemini 3+, Claude 4.5/4.6)"
                            )
                            with gr.Row():
                                thinking_type_dropdown = gr.Dropdown(
                                    choices=["Adaptive", "Enabled"],
                                    value="Adaptive",
                                    label="Тип Thinking (Claude)",
                                    interactive=False
                                )
                                thinking_level_dropdown = gr.Dropdown(
                                    choices=["none", "low", "medium", "high", "xhigh"],
                                    value="medium",
                                    label="Рівень Thinking (OpenAI/Gemini)",
                                    interactive=False
                                )
                                openai_verbosity_dropdown = gr.Dropdown(
                                    choices=["low", "medium", "high"],
                                    value="medium",
                                    label="Verbosity (OpenAI GPT-5)",
                                    interactive=True
                                )
                                thinking_budget_slider = gr.Slider(
                                    minimum=1024,
                                    maximum=32000,
                                    value=10000,
                                    step=1024,
                                    label="Бюджет токенів (Claude 4.5)",
                                    interactive=False
                                )
                    
                gr.Markdown("### 📄 Вхідні дані")
                
                # New Tabs-based Input Selection
                with gr.Tabs() as input_tabs:
                    with gr.TabItem("📝 Текст рішення", id="text_tab"):
                        text_input = gr.Textbox(
                            show_label=False,
                            placeholder="Вставте повний текст судового рішення сюди...",
                            lines=12,
                            max_lines=30
                        )
                    
                    with gr.TabItem("🔗 URL посилання", id="url_tab"):
                        url_input = gr.Textbox(
                            show_label=False,
                            placeholder="https://reyestr.court.gov.ua/Review/...",
                            info="Підтримуються посилання на Єдиний державний реєстр судових рішень"
                        )
                        
                    with gr.TabItem("📂 Завантаження файлу", id="file_tab"):
                        file_input = gr.File(
                            label="Перетягніть TXT-файл або натисніть для вибору",
                            file_types=[".txt"],
                            file_count="single"
                        )
                
                # Hidden grouping for thinking visibility
                thinking_settings_group = gr.Group(visible=True) # Initially visible, visibility controlled by provider
                with thinking_settings_group:
                     # This empty context is just to register the variable if I use it later,
                     # but actually thinking controls are ALREADY inside Accordion.
                     # The Accordion itself should be the thing I toggle? 
                     # Or the Row with checkbox.
                     pass 

                with gr.Column(variant="panel"):
                    comment_input = gr.Textbox(
                        label="Коментар до генерації (опціонально)",
                        placeholder="Наприклад: 'Зробити акцент на процесуальних строках'...",
                        lines=2
                    )
                    
                    generate_position_button = gr.Button(
                        "📝 Згенерувати правову позицію",
                        variant="primary",
                        size="lg"
                    )

                position_output = gr.Markdown(
                    label="Результат",
                    elem_classes=["tab-content"]
                )

            # Вкладка Пошук
            with gr.Tab("🔍 Пошук", id=1):
                gr.Markdown("### Пошук схожих правових позицій", elem_classes=["tab-header"])

                with gr.Row():
                    search_with_ai_button = gr.Button(
                        "🔎 Пошук на основі правової позиції",
                        variant="primary",
                        interactive=False
                    )
                    search_with_text_button = gr.Button(
                        "🔎 Пошук на основі вхідного тексту",
                        variant="primary",
                        interactive=True
                    )

                search_output = gr.Markdown(
                    label="Результати пошуку",
                    elem_classes=["tab-content"]
                )

            # Вкладка Аналіз
            with gr.Tab("⚖️ Аналіз", id=2):
                gr.Markdown("### Порівняльний аналіз нової правової позиції із знайденими в результаті пошуку", elem_classes=["tab-header"])

                with gr.Row():
                    analysis_provider_dropdown = gr.Dropdown(
                        choices=_available_providers,
                        value=_default_provider,
                        label="Провайдер AI",
                        scale=1
                    )
                    analysis_model_dropdown = gr.Dropdown(
                        choices=_ana_models,
                        value=_default_ana_model,
                        label="Модель аналізу",
                        scale=1
                    )
                with gr.Accordion("⚙️ Налаштування аналізу", open=False):
                    with gr.Row():
                        analysis_temp_slider = gr.Slider(
                            minimum=0.0,
                            maximum=2.0,
                            value=0.5,
                            step=0.1,
                            label="Температура аналізу"
                        )
                        analysis_max_tokens_slider = gr.Slider(
                            minimum=512,
                            maximum=32768,
                            value=4000,
                            step=512,
                            label="Max Tokens (ліміт відповіді)"
                        )

                question_input = gr.Textbox(
                    label="Уточнююче питання для аналізу",
                    placeholder="Введіть питання для уточнення аналізу...",
                    lines=2
                )

                analyze_button = gr.Button(
                    "⚖️ Аналіз результатів пошуку",
                    variant="primary",
                    interactive=False
                )

                analysis_output = gr.Markdown(
                    label="Результати аналізу",
                    elem_classes=["tab-content"]
                )

            # Вкладка Налаштування (Settings)
            with gr.Tab("⚙️ Налаштування", id=3):
                gr.Markdown("### Редагування промптів", elem_classes=["tab-header"])

                gr.Markdown("""
                **Увага!** Налаштування промптів зберігаються тільки для вашої поточної сесії.
                Кожен користувач має свої власні налаштування, які не впливають на інших користувачів.
                """)

                with gr.Column():
                    system_prompt_editor = gr.Textbox(
                        label="📋 Системний промпт",
                        value=SYSTEM_PROMPT,
                        lines=5,
                        max_lines=10,
                        placeholder="Введіть системний промпт...",
                        info="Визначає роль та базові інструкції для AI"
                    )

                    lp_prompt_editor = gr.Textbox(
                        label="⚖️ Промпт генерації правової позиції",
                        value=LEGAL_POSITION_PROMPT,
                        lines=15,
                        max_lines=30,
                        placeholder="Введіть промпт для генерації правової позиції...",
                        info="Шаблон для генерації правової позиції з судового рішення"
                    )

                    analysis_prompt_editor = gr.Textbox(
                        label="🔍 Промпт аналізу прецедентів",
                        value=str(PRECEDENT_ANALYSIS_TEMPLATE.template),
                        lines=15,
                        max_lines=30,
                        placeholder="Введіть промпт для аналізу прецедентів...",
                        info="Шаблон для порівняльного аналізу правових позицій"
                    )

                with gr.Row():
                    save_prompts_button = gr.Button(
                        "💾 Зберегти промпти",
                        variant="primary",
                        scale=1,
                        interactive=False
                    )
                    reset_prompts_button = gr.Button(
                        "🔄 Скинути до стандартних",
                        variant="secondary",
                        scale=1
                    )

                prompts_status = gr.Markdown(
                    "",
                    elem_classes=["tab-content"]
                )

            # Вкладка Пакетне тестування (Batch Testing)
            with gr.Tab("📊 Пакетне тестування", id=4):
                gr.Markdown("### Пакетна генерація правових позицій з CSV/Excel файлу", elem_classes=["tab-header"])

                gr.Markdown("""
                **Інструкція:**
                1. Виберіть провайдера AI та модель для генерації
                2. Завантажте CSV або Excel (.xlsx, .xls) файл, що містить колонку `text` з текстами судових рішень
                3. Запустіть пакетне тестування
                4. Завантажте результати у форматі CSV (результати завжди зберігаються як CSV для сумісності)

                **Вимоги до файлу:**
                - Обов'язково повинна бути колонка `text` з текстами рішень
                """)

                with gr.Row():
                    batch_provider_dropdown = gr.Dropdown(
                        choices=_available_providers,
                        value=_default_provider,
                        label="Провайдер AI",
                        container=False,
                        scale=1
                    )
                    batch_model_dropdown = gr.Dropdown(
                        choices=_gen_models,
                        value=_default_gen_model,
                        label="Модель генерації",
                        container=False,
                        scale=2
                    )

                # Advanced Settings Accordion (mirrors Generation tab)
                with gr.Accordion("⚙️ Додаткові параметри", open=False) as batch_thinking_accordion:
                    with gr.Row():
                        batch_temp_slider = gr.Slider(
                            minimum=0.0,
                            maximum=2.0,
                            value=0.5,
                            step=0.1,
                            label="Температура генерації (креативність)"
                        )
                        batch_max_tokens_slider = gr.Slider(
                            minimum=512,
                            maximum=32768,
                            value=4000,
                            step=512,
                            label="Max Tokens (ліміт відповіді)"
                        )
                    batch_thinking_enabled_checkbox = gr.Checkbox(
                        label="Увімкнути режим Thinking (глибокий аналіз)",
                        value=False,
                        info="Активує розширений ланцюг міркувань (Gemini 3+, Claude 4.5/4.6)"
                    )
                    with gr.Row():
                        batch_thinking_type_dropdown = gr.Dropdown(
                            choices=["Adaptive", "Enabled"],
                            value="Adaptive",
                            label="Тип Thinking (Claude)",
                            interactive=False
                        )
                        batch_thinking_level_dropdown = gr.Dropdown(
                            choices=["none", "low", "medium", "high", "xhigh"],
                            value="medium",
                            label="Рівень Thinking (OpenAI/Gemini)",
                            interactive=False
                        )
                        batch_openai_verbosity_dropdown = gr.Dropdown(
                            choices=["low", "medium", "high"],
                            value="medium",
                            label="Verbosity (OpenAI GPT-5)",
                            interactive=True
                        )
                        batch_thinking_budget_slider = gr.Slider(
                            minimum=1024,
                            maximum=32000,
                            value=10000,
                            step=1024,
                            label="Бюджет токенів (Claude 4.5)",
                            interactive=False
                        )

                delay_slider = gr.Slider(
                    minimum=0,
                    maximum=10,
                    value=1,
                    step=0.5,
                    label="⏱️ Пауза між запитами (секунди)",
                    info="Затримка між обробкою кожного рядка для уникнення перевантаження API"
                )

                csv_file_input = gr.File(
                    label="📁 Завантажте CSV або Excel файл з тестовими даними",
                    file_types=[".csv", ".xlsx", ".xls"],
                    type="filepath"
                )

                csv_preview_output = gr.Markdown(
                    label="Попередній перегляд файлу",
                    elem_classes=["tab-content"]
                )

                # State to store loaded dataframe
                batch_df_state = gr.State()

                load_csv_button = gr.Button(
                    "📂 Завантажити CSV/XLSX файл",
                    variant="secondary",
                    scale=1
                )

                start_batch_button = gr.Button(
                    "▶️ Запустити пакетне тестування",
                    variant="primary",
                    scale=1,
                    interactive=False
                )

                batch_output = gr.Markdown(
                    label="Результати пакетного тестування",
                    elem_classes=["tab-content"]
                )

                download_results_file = gr.File(
                    label="📥 Завантажити результати (CSV)",
                    visible=False,
                    interactive=False
                )

                download_results_btn = gr.DownloadButton(
                    label="⬇️ Вигрузити результати",
                    variant="secondary",
                    visible=False
                )

            # Вкладка Допомога (Help)
            with gr.Tab("📖 Допомога", id=5):
                gr.Markdown("### Довідка по використанню AI Асистента", elem_classes=["tab-header"])

                help_content = load_help_content()

                gr.Markdown(
                    help_content,
                    elem_classes=["tab-content"]
                )

        # Event handlers
        def update_input_state(evt: gr.SelectData):
            # Map tab IDs to input method strings used by process_input
            mapping = {
                "text_tab": "Текстовий ввід",
                "url_tab": "URL посилання",
                "file_tab": "Завантаження файлу"
            }
            return mapping.get(evt.value, "Текстовий ввід")
            
        def update_analyze_button_status(tab_id):
            return gr.update(interactive=state_nodes is not None)

        # Update input method state when tab changes
        input_tabs.select(
            fn=update_input_state,
            inputs=None,
            outputs=[input_method_state]
        )

        # provider dropdown changes
        generation_provider_dropdown.change(
            fn=update_generation_model_choices,
            inputs=[generation_provider_dropdown],
            outputs=[generation_model_dropdown]
        )
        
        analysis_provider_dropdown.change(
            fn=update_analysis_model_choices,
            inputs=[analysis_provider_dropdown],
            outputs=[analysis_model_dropdown]
        )

        batch_provider_dropdown.change(
            fn=update_generation_model_choices,
            inputs=[batch_provider_dropdown],
            outputs=[batch_model_dropdown]
        )

        # thinking mode settings — Generation tab
        generation_provider_dropdown.change(
            fn=update_thinking_visibility,
            inputs=[generation_provider_dropdown],
            outputs=[thinking_accordion]
        )
        
        thinking_enabled_checkbox.change(
            fn=update_thinking_level_interactive,
            inputs=[thinking_enabled_checkbox],
            outputs=[thinking_type_dropdown, thinking_level_dropdown, thinking_budget_slider]
        )

        # thinking mode settings — Batch Testing tab
        batch_provider_dropdown.change(
            fn=update_thinking_visibility,
            inputs=[batch_provider_dropdown],
            outputs=[batch_thinking_accordion]
        )

        batch_thinking_enabled_checkbox.change(
            fn=update_thinking_level_interactive,
            inputs=[batch_thinking_enabled_checkbox],
            outputs=[batch_thinking_type_dropdown, batch_thinking_level_dropdown, batch_thinking_budget_slider]
        )

        # generation and analysis
        generate_position_button.click(
            fn=lambda: (
                gr.update(value="⏳ **Генерація правової позиції...**\n\nЗапит відправлено до AI. Зачекайте, це може зайняти кілька секунд."),
                gr.update(interactive=False)
            ),
            inputs=None,
            outputs=[position_output, generate_position_button]
        ).then(
            fn=process_input,
            inputs=[
                text_input,
                url_input,
                file_input,
                comment_input,
                input_method_state,
                generation_provider_dropdown,
                generation_model_dropdown,
                thinking_enabled_checkbox,
                thinking_type_dropdown,
                thinking_level_dropdown,
                openai_verbosity_dropdown,
                thinking_budget_slider,
                generation_temp_slider,
                generation_max_tokens_slider,
                session_id_state
            ],
            outputs=[position_output, state_lp_json, session_id_state]
        ).then(
            fn=lambda: (gr.update(interactive=True), gr.update(interactive=True)),
            inputs=None,
            outputs=[generate_position_button, search_with_ai_button]
        )

        search_with_ai_button.click(
            fn=search_with_ai_action,
            inputs=[state_lp_json],
            outputs=[search_output, state_nodes]
        ).then(
            fn=lambda nodes: gr.update(interactive=nodes is not None),
            inputs=[state_nodes],
            outputs=analyze_button
        )

        search_with_text_button.click(
            fn=process_raw_text_search,
            inputs=[text_input, url_input, file_input, input_method_state, state_lp_json],
            outputs=[search_output, state_nodes, state_lp_json]
        ).then(
            fn=lambda nodes: gr.update(interactive=nodes is not None),
            inputs=[state_nodes],
            outputs=analyze_button
        )

        analyze_button.click(
            fn=analyze_action,
            inputs=[
                state_lp_json,
                question_input,
                state_nodes,
                analysis_provider_dropdown,
                analysis_model_dropdown,
                analysis_temp_slider,
                analysis_max_tokens_slider
            ],
            outputs=analysis_output
        )

        # Settings tab event handlers

        # Enable save button when any prompt is changed
        for editor in [system_prompt_editor, lp_prompt_editor, analysis_prompt_editor]:
            editor.change(
                fn=lambda: gr.update(interactive=True),
                inputs=None,
                outputs=[save_prompts_button]
            )

        save_prompts_button.click(
            fn=save_custom_prompts,
            inputs=[
                session_id_state,
                system_prompt_editor,
                lp_prompt_editor,
                analysis_prompt_editor
            ],
            outputs=[prompts_status, session_id_state]
        ).then(
            fn=lambda: gr.update(interactive=False),
            inputs=None,
            outputs=[save_prompts_button]
        )

        reset_prompts_button.click(
            fn=reset_prompts_to_default,
            inputs=[session_id_state],
            outputs=[
                system_prompt_editor,
                lp_prompt_editor,
                analysis_prompt_editor,
                prompts_status,
                session_id_state
            ]
        ).then(
            fn=lambda: gr.update(interactive=False),
            inputs=None,
            outputs=[save_prompts_button]
        )

        # Batch testing tab event handlers
        load_csv_button.click(
            fn=load_data_file,
            inputs=[csv_file_input],
            outputs=[csv_preview_output, batch_df_state]
        ).then(
            fn=lambda df: gr.update(interactive=df is not None),
            inputs=[batch_df_state],
            outputs=[start_batch_button]
        )

        # Internal state to keep the output file path
        batch_result_path_state = gr.State()

        start_batch_button.click(
            fn=lambda: (
                gr.update(value="⏳ **Пакетне тестування запущено...**\n\nОбробка рядків. Зачекайте, будь ласка."),
                gr.update(interactive=False),
                gr.update(visible=False),
                gr.update(visible=False)
            ),
            inputs=None,
            outputs=[batch_output, start_batch_button, download_results_file, download_results_btn]
        ).then(
            fn=process_batch_testing,
            inputs=[
                batch_df_state,
                batch_provider_dropdown,
                batch_model_dropdown,
                delay_slider,
                batch_thinking_enabled_checkbox,
                batch_thinking_type_dropdown,
                batch_thinking_level_dropdown,
                batch_openai_verbosity_dropdown,
                batch_thinking_budget_slider,
                batch_temp_slider,
                batch_max_tokens_slider
            ],
            outputs=[batch_output, batch_result_path_state]
        ).then(
            fn=lambda output_path: (
                gr.update(interactive=True),
                gr.update(visible=output_path is not None, value=output_path),
                gr.update(visible=output_path is not None, value=output_path)
            ),
            inputs=[batch_result_path_state],
            outputs=[start_batch_button, download_results_file, download_results_btn]
        )

        # Removed app.load call to avoid startup race condition with session state
        # Prompts are already initialized with default values in the UI components
        # and session is fresh on every reload anyway.

        return app