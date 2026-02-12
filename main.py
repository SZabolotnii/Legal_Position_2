import os
import sys
import json
import time
import boto3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from anthropic import Anthropic
import openai
from openai import OpenAI
from google import genai
from google.genai import types
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.workflow import Event, Context, Workflow, StartEvent, StopEvent, step
from llama_index.core.schema import NodeWithScore

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    BUCKET_NAME,
    PREFIX_RETRIEVER,
    LOCAL_DIR,
    SETTINGS,
    MAX_TOKENS_CONFIG,
    MAX_TOKENS_ANALYSIS,
    GENERATION_TEMPERATURE,
    LEGAL_POSITION_SCHEMA,
    REQUIRED_FILES,
    ModelProvider,
    AnalysisModelName,
    DEEPSEEK_API_KEY,
    validate_environment
)
from prompts import SYSTEM_PROMPT, LEGAL_POSITION_PROMPT, PRECEDENT_ANALYSIS_TEMPLATE
from utils import (
    clean_text,
    extract_court_decision_text,
    get_links_html,
    get_links_html_lp,
    extract_json_from_text
)
from embeddings import GeminiEmbedding

# Initialize embedding model and settings BEFORE importing components
# Priority: OpenAI > Gemini > None
embed_model = None
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if OPENAI_API_KEY:
    embed_model = OpenAIEmbedding(model_name="text-embedding-3-small")
    print("OpenAI embedding model initialized successfully")
elif GEMINI_API_KEY:
    embed_model = GeminiEmbedding(api_key=GEMINI_API_KEY, model_name="gemini-embedding-001")
    print("Gemini embedding model initialized successfully (alternative to OpenAI)")
else:
    print("Warning: No embedding API key found (OpenAI or Gemini). Search functionality will be disabled.")

if embed_model:
    Settings.embed_model = embed_model

# Set basic LlamaIndex Settings before setting LLM
Settings.chunk_size = SETTINGS["chunk_size"]
Settings.similarity_top_k = SETTINGS["similarity_top_k"]

# Set a default LLM to prevent QueryFusionRetriever from trying to load OpenAI
# Use a mock LLM with minimal initialization to avoid validation issues
# We use DeepSeek but with a gpt-4o-mini model name to pass validation
if DEEPSEEK_API_KEY:
    Settings.llm = LlamaOpenAI(
        api_key=DEEPSEEK_API_KEY,
        api_base="https://api.deepseek.com",
        model="gpt-4o-mini"  # Use a known model name for validation
    )
    print("DeepSeek LLM set as default for LlamaIndex (using gpt-4o-mini model name for compatibility)")
elif OPENAI_API_KEY:
    Settings.llm = LlamaOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
    print("OpenAI LLM set as default for LlamaIndex")

# Now we can safely set context_window
Settings.context_window = SETTINGS["context_window"]

# Import components AFTER setting all Settings
from components import search_components

# Initialize S3 client (optional, only if AWS credentials are provided)
s3_client = None
if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name="eu-north-1"
        )
        print("AWS S3 client initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize AWS S3 client: {str(e)}")
        s3_client = None
else:
    print("AWS credentials not provided. Will use local files only.")


def download_s3_file(bucket_name: str, s3_key: str, local_path: str) -> None:
    """Download a single file from S3."""
    if not s3_client:
        raise ValueError("S3 client not initialized. Please provide AWS credentials or use local files.")
    try:
        s3_client.download_file(bucket_name, s3_key, str(local_path))
        print(f"Downloaded: {s3_key} -> {local_path}")
    except Exception as e:
        print(f"Error downloading file {s3_key}: {str(e)}", file=sys.stderr)
        raise


def download_s3_folder(bucket_name: str, prefix: str, local_dir: Path) -> None:
    """Download all files from an S3 folder."""
    if not s3_client:
        raise ValueError("S3 client not initialized. Please provide AWS credentials or use local files.")
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' not in response:
            raise ValueError(f"No files found in S3 bucket {bucket_name} with prefix {prefix}")

        for obj in response['Contents']:
            s3_key = obj['Key']
            if s3_key.endswith('/'):
                continue
            local_file_path = local_dir / Path(s3_key).relative_to(prefix)
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            s3_client.download_file(bucket_name, s3_key, str(local_file_path))
            print(f"Downloaded: {s3_key} -> {local_file_path}")
    except Exception as e:
        print(f"Error downloading folder {prefix}: {str(e)}", file=sys.stderr)
        raise


def initialize_components() -> bool:
    """Initialize all necessary components for the application."""
    try:
        # Create local directory if it doesn't exist
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)

        # Download index files from S3 only if S3 client is available and local files don't exist
        missing_files = [f for f in REQUIRED_FILES if not (LOCAL_DIR / f).exists()]
        
        if missing_files:
            if s3_client:
                print("Some required files are missing locally. Attempting to download from S3...")
                download_s3_folder(BUCKET_NAME, PREFIX_RETRIEVER, LOCAL_DIR)
            else:
                print(f"Warning: Missing required files and no S3 client available: {', '.join(missing_files)}")
                print(f"Checking if files exist in {LOCAL_DIR}...")
        else:
            print(f"All required files found locally in {LOCAL_DIR}")

        if not LOCAL_DIR.exists():
            raise FileNotFoundError(f"Directory not found: {LOCAL_DIR}")

        # Check for required files again
        missing_files = [f for f in REQUIRED_FILES if not (LOCAL_DIR / f).exists()]
        if missing_files:
            raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

        # Initialize search components if any embedding model is available
        if embed_model:
            success = search_components.initialize_components(LOCAL_DIR)
            if not success:
                raise RuntimeError("Failed to initialize search components")
            print("Search components initialized successfully")
        else:
            print("Skipping search components initialization (no embedding API key available)")

        return True

    except Exception as e:
        print(f"Error initializing components: {str(e)}", file=sys.stderr)
        return False


def deduplicate_nodes(nodes: list[NodeWithScore], key="doc_id"):
    """Видаляє дублікати з результатів пошуку на основі метаданих."""
    seen = set()
    unique_nodes = []

    for node in nodes:
        value = node.node.metadata.get(key)
        if value and value not in seen:
            seen.add(value)
            unique_nodes.append(node)

    return unique_nodes


def get_text_length_without_spaces(text: str) -> int:
    """Підраховує довжину тексту без пробілів."""
    return len(''.join(text.split()))


def get_available_providers() -> Dict[str, bool]:
    """Get status of all AI providers."""
    return {
        "openai": bool(OPENAI_API_KEY),
        "anthropic": bool(ANTHROPIC_API_KEY),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "deepseek": bool(DEEPSEEK_API_KEY)
    }


def check_provider_available(provider: str) -> Tuple[bool, str]:
    """
    Check if a provider is available.

    Returns:
        Tuple of (is_available, error_message)
    """
    providers = get_available_providers()
    provider_key = provider.lower()

    if provider_key not in providers:
        return False, f"Unknown provider: {provider}"

    if not providers[provider_key]:
        available = [k.upper() for k, v in providers.items() if v]
        if not available:
            return False, "No AI provider API keys configured. Please set at least one API key."
        return False, f"{provider.upper()} API key not configured. Available providers: {', '.join(available)}"

    return True, ""


class RetrieverEvent(Event):
    """Event class for retriever operations."""
    nodes: list[NodeWithScore]


class LLMAnalyzer:
    """Class for handling different LLM providers."""

    def __init__(self, provider: "ModelProvider", model_name: "AnalysisModelName"):
        self.provider = provider
        self.model_name = model_name

        if provider == ModelProvider.OPENAI:
            if not OPENAI_API_KEY:
                raise ValueError(f"OpenAI API key not configured. Please set OPENAI_API_KEY environment variable to use {provider.value} provider.")
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        elif provider == ModelProvider.DEEPSEEK:
            if not DEEPSEEK_API_KEY:
                raise ValueError(f"DeepSeek API key not configured. Please set DEEPSEEK_API_KEY environment variable to use {provider.value} provider.")
            self.client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        elif provider == ModelProvider.ANTHROPIC:
            if not ANTHROPIC_API_KEY:
                raise ValueError(f"Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable to use {provider.value} provider.")
            self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        elif provider == ModelProvider.GEMINI:
            if not os.environ.get("GEMINI_API_KEY"):
                raise ValueError(f"Gemini API key not configured. Please set GEMINI_API_KEY environment variable to use {provider.value} provider.")
            # Initialize Gemini client with new API
            self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def analyze(self, prompt: str, response_schema: dict) -> str:
        """Analyze text using selected LLM provider."""
        if self.provider == ModelProvider.OPENAI:
            return await self._analyze_with_openai(prompt, response_schema)
        elif self.provider == ModelProvider.DEEPSEEK:
            return await self._analyze_with_deepseek(prompt)
        elif self.provider == ModelProvider.ANTHROPIC:
            return await self._analyze_with_anthropic(prompt, response_schema)
        else:
            return await self._analyze_with_gemini(prompt, response_schema)

    async def _analyze_with_openai(self, prompt: str, response_schema: dict) -> str:
        """Analyze text using OpenAI."""
        # Determine model name and if it's a reasoning model
        model_val = self.model_name.value if hasattr(self.model_name, "value") else str(self.model_name)
        is_reasoning_model = any(m in model_val.lower() for m in ["gpt-4.1", "gpt-4.5", "o1", "o3"])
        
        # Use developer role for newer models
        role = "developer" if is_reasoning_model else "system"
        
        messages = [
            ChatMessage(role=role, content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt)
        ]

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "relevant_positions_schema",
                "schema": response_schema
            }
        }

        try:
            completion_params = {
                "model": model_val,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "response_format": response_format,
            }
            
            # Reasoning models usually require temperature=1.0 or none
            if not is_reasoning_model:
                completion_params["temperature"] = 0

            response = self.client.chat.completions.create(**completion_params)
            response_text = response.choices[0].message.content
            
            # Verify it's valid JSON
            json_data = extract_json_from_text(response_text)
            return json.dumps(json_data, ensure_ascii=False) if json_data else response_text
        except Exception as e:
            raise RuntimeError(f"Error in OpenAI analysis ({model_val}): {str(e)}")

    async def _analyze_with_deepseek(self, prompt: str) -> str:
        """Analyze text using DeepSeek."""
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt)
        ]

        response_format = {
            'type': 'json_object'
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                response_format=response_format,
                temperature=0
            )
            response_text = response.choices[0].message.content
            
            # Verify and clean JSON
            json_data = extract_json_from_text(response_text)
            return json.dumps(json_data, ensure_ascii=False) if json_data else response_text
        except Exception as e:
            raise RuntimeError(f"Error in DeepSeek analysis: {str(e)}")

    async def _analyze_with_anthropic(self, prompt: str, response_schema: dict) -> str:
        """Analyze text using Anthropic."""
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=MAX_TOKENS_ANALYSIS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text
            
            # Extract JSON from potential markdown blocks
            json_data = extract_json_from_text(response_text)
            if json_data:
                return json.dumps(json_data, ensure_ascii=False)
            return response_text
        except Exception as e:
            raise RuntimeError(f"Error in Anthropic analysis: {str(e)}")

    async def _analyze_with_gemini(self, prompt: str, response_schema: dict) -> str:
        """Analyze text using Gemini with new API."""
        try:
            # Форматуємо промпт для отримання відповіді у форматі JSON
            json_instruction = """
            Твоя відповідь повинна бути в форматі JSON:
            {
                "relevant_positions": [
                    {
                        "lp_id": "ID позиції",
                        "source_index": "Порядковий номер позиції у списку",
                        "description": "Детальне обґрунтування релевантності"
                    }
                ]
            }
            """

            formatted_prompt = f"{prompt}\n\n{json_instruction}"

            # Use new google.genai API
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=formatted_prompt),
                    ],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=GENERATION_TEMPERATURE,
                max_output_tokens=MAX_TOKENS_ANALYSIS,
                system_instruction=[
                    types.Part.from_text(text=SYSTEM_PROMPT),
                ],
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generate_content_config,
            )
            response_text = response.text

            if not response_text:
                raise RuntimeError("Empty response from Gemini")

            # Витягуємо JSON з відповіді за допомогою універсальної функції
            json_data = extract_json_from_text(response_text)
            
            if json_data:
                if "relevant_positions" not in json_data:
                    json_data = {
                        "relevant_positions": [
                            {
                                "lp_id": "unknown",
                                "source_index": "1",
                                "description": json.dumps(json_data, ensure_ascii=False)
                            }
                        ]
                    }
                return json.dumps(json_data, ensure_ascii=False)
            else:
                # Якщо JSON не знайдено, створюємо структурований JSON з тексту
                return json.dumps({
                    "relevant_positions": [
                        {
                            "lp_id": "unknown",
                            "source_index": "1",
                            "description": response_text
                        }
                    ]
                }, ensure_ascii=False)

        except Exception as e:
            # Спроба отримати більш детальну інформацію про помилку
            error_details = str(e)
            if hasattr(e, 'response'):
                error_details += f"\nResponse: {e.response}"
            raise RuntimeError(f"Error in Gemini analysis: {error_details}")


class PrecedentAnalysisWorkflow(Workflow):
    """Workflow for analyzing legal precedents."""

    def __init__(self, provider: ModelProvider = ModelProvider.OPENAI,
                 model_name: AnalysisModelName = AnalysisModelName.GPT4o_MINI):
        super().__init__()
        self.analyzer = LLMAnalyzer(provider, model_name)

    @step
    async def analyze(self, ctx: Context, ev: StartEvent) -> StopEvent:
        """Analyze legal precedents."""
        try:
            query = ev.get("query", "")
            question = ev.get("question", "")
            nodes = ev.get("nodes", [])

            if not query:
                return StopEvent(result="Error: No text provided (query)")
            if not nodes:
                return StopEvent(result="Error: No legal positions provided for analysis (nodes)")

            context_parts = []
            for i, node in enumerate(nodes, 1):
                node_text = node.node.text if hasattr(node, 'node') else node.text
                metadata = node.node.metadata if hasattr(node, 'node') else node.metadata
                lp_id = metadata.get('lp_id', f'unknown_{i}')
                context_parts.append(f"Source {i} (ID: {lp_id}):\n{node_text}")

            context_str = "\n\n".join(context_parts)

            response_schema = {
                "type": "object",
                "properties": {
                    "relevant_positions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "lp_id": {"type": "string"},
                                "source_index": {"type": "string"},
                                "description": {"type": "string"}
                            },
                            "required": ["lp_id", "source_index", "description"]
                        }
                    }
                }
            }

            prompt = PRECEDENT_ANALYSIS_TEMPLATE.format(
                query=query,
                question=question if question else "Загальний аналіз релевантності",
                context_str=context_str
            )

            response_content = await self.analyzer.analyze(prompt, response_schema)

            try:
                # Спроба розпарсити JSON
                parsed_response = json.loads(response_content)

                if "relevant_positions" in parsed_response:
                    response_lines = []
                    for position in parsed_response["relevant_positions"]:
                        position_text = f"* [{position['source_index']}] {position['description']}  "
                        response_lines.append(position_text)

                    response_text = "\n".join(response_lines)
                    return StopEvent(result=response_text)
                else:
                    # Якщо немає relevant_positions, повертаємо весь текст
                    return StopEvent(result=f"* [1] {response_content}")

            except json.JSONDecodeError as e:
                # Якщо не вдалося розпарсити JSON, повертаємо текст як є
                return StopEvent(result=f"* [1] {response_content}")

        except Exception as e:
            return StopEvent(result=f"Error during analysis: {str(e)}")


def generate_legal_position(
        input_text: str,
        input_type: str,
        comment_input: str,
        provider: str,
        model_name: str,
        thinking_enabled: bool = False,
        thinking_level: str = "MEDIUM",
        thinking_budget: int = 10000,
        custom_system_prompt: Optional[str] = None,
        custom_lp_prompt: Optional[str] = None
) -> Dict:
    """Generate legal position from input text using specified provider and model."""
    try:
        # Check if provider is available
        is_available, error_msg = check_provider_available(provider)
        if not is_available:
            return {
                "title": "Помилка конфігурації",
                "text": error_msg,
                "proceeding": "N/A",
                "category": "Error"
            }

        # Use custom prompts if provided, otherwise use defaults
        system_prompt = custom_system_prompt if custom_system_prompt else SYSTEM_PROMPT
        lp_prompt = custom_lp_prompt if custom_lp_prompt else LEGAL_POSITION_PROMPT

        print(f"[DEBUG] RAW input_text length: {len(input_text) if input_text else 0}")
        print(f"[DEBUG] RAW input_text preview: {input_text[:300] if input_text else 'Empty'}")
        print(f"[DEBUG] Using custom prompts: system={custom_system_prompt is not None}, lp={custom_lp_prompt is not None}")

        input_text = clean_text(input_text)

        print(f"[DEBUG] AFTER CLEAN input_text length: {len(input_text) if input_text else 0}")
        print(f"[DEBUG] AFTER CLEAN input_text preview: {input_text[:300] if input_text else 'Empty'}")

        comment_input = clean_text(comment_input)

        if input_type == "url":
            try:
                extracted = extract_court_decision_text(input_text)
                print(f"[DEBUG] EXTRACTED text length: {len(extracted) if extracted else 0}")
                print(f"[DEBUG] EXTRACTED text preview: {extracted[:300] if extracted else 'Empty'}")

                court_decision_text = clean_text(extracted)

                print(f"[DEBUG] AFTER CLEAN extracted length: {len(court_decision_text) if court_decision_text else 0}")
                print(f"[DEBUG] AFTER CLEAN extracted preview: {court_decision_text[:300] if court_decision_text else 'Empty'}")
            except Exception as e:
                raise Exception(f"Помилка при отриманні тексту за URL: {str(e)}")
        else:
            court_decision_text = input_text

        # Debug: Check what we have before formatting
        print(f"[DEBUG] FINAL court_decision_text length: {len(court_decision_text)}")
        print(f"[DEBUG] FINAL court_decision_text preview: {court_decision_text[:300]}")
        print(f"[DEBUG] comment_input: {comment_input[:100] if comment_input else 'Empty'}")

        # Check if placeholders exist in the prompt, if not - append them to the end
        if "{court_decision_text}" not in lp_prompt:
            print("[WARNING] {court_decision_text} placeholder missing in prompt! Appending to the end.")
            lp_prompt += "\n\n<court_decision>\n{court_decision_text}\n</court_decision>"
        
        if "{comment}" not in lp_prompt:
            lp_prompt += "\n\n<comment>\n{comment}\n</comment>"

        content = lp_prompt.format(
            court_decision_text=court_decision_text,
            comment=comment_input if comment_input else "Коментар відсутній"
        )

        # Debug: Check formatted content
        print(f"[DEBUG] ===== UNIFIED PROMPT FOR ALL PROVIDERS =====")
        print(f"[DEBUG] Formatted content length: {len(content)}")
        print(f"[DEBUG] Content preview (first 500 chars): {content[:500]}")
        print(f"[DEBUG] Provider: {provider}, Model: {model_name}")
        print(f"[DEBUG] ==============================================")

        # Validation check - ensure court_decision_text is not empty
        if not court_decision_text or len(court_decision_text.strip()) < 50:
            print(f"[WARNING] court_decision_text is too short or empty! Length: {len(court_decision_text) if court_decision_text else 0}")
            raise Exception(f"Текст судового рішення занадто короткий або відсутній (довжина: {len(court_decision_text) if court_decision_text else 0} символів). Будь ласка, перевірте вхідні дані.")

        if provider == ModelProvider.OPENAI.value:
            client = OpenAI(api_key=OPENAI_API_KEY)
            try:
                print(f"[DEBUG] OpenAI Generation - Model: {model_name}")
                
                # Check for reasoning models (gpt-4.1, o1, etc.)
                is_reasoning_model = any(m in model_name.lower() for m in ["gpt-4.1", "gpt-4.5", "o1", "o3"])
                
                # Use developer role for newer models, system for others
                role = "developer" if is_reasoning_model else "system"
                
                messages = [
                    {"role": role, "content": system_prompt},
                    {"role": "user", "content": content},
                ]
                
                # Parameters for chat completion
                completion_params = {
                    "model": model_name,
                    "messages": messages,
                }
                
                # Set tokens based on model capabilities
                if is_reasoning_model:
                    completion_params["max_completion_tokens"] = MAX_TOKENS_CONFIG["openai"]
                else:
                    completion_params["max_tokens"] = MAX_TOKENS_CONFIG["openai"]
                
                # Handle thinking/reasoning
                if thinking_enabled and is_reasoning_model:
                    completion_params["reasoning_effort"] = thinking_level.lower()
                    # Reasoning models usually don't support temperature or it must be 1.0
                else:
                    completion_params["temperature"] = GENERATION_TEMPERATURE

                response = client.chat.completions.create(**completion_params)
                response_text = response.choices[0].message.content
                print(f"[DEBUG] OpenAI response length: {len(response_text) if response_text else 0}")
                
                json_response = extract_json_from_text(response_text)
                if json_response and all(key in json_response for key in ["title", "text", "proceeding", "category"]):
                    return json_response
                else:
                    print(f"[WARNING] Invalid JSON structure from OpenAI. Text: {response_text[:300] if response_text else 'None'}...")
                    raise ValueError("Invalid JSON structure")
            except Exception as e:
                print(f"[ERROR] OpenAI generation/parsing failed: {e}")
                return {
                    "title": "Автоматично сформований заголовок (OpenAI)",
                    "text": response_text.strip() if 'response_text' in locals() and response_text else f"Помилка при отриманні відповіді: {str(e)}",
                    "proceeding": "Не визначено",
                    "category": "Помилка парсингу"
                }

        if provider == ModelProvider.DEEPSEEK.value:
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            try:
                print(f"[DEBUG] DeepSeek Generation - Model: {model_name}")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ],
                    temperature=GENERATION_TEMPERATURE,
                    max_tokens=MAX_TOKENS_CONFIG["deepseek"],
                )
                response_text = response.choices[0].message.content
                print(f"[DEBUG] DeepSeek response length: {len(response_text)}")
                
                json_response = extract_json_from_text(response_text)
                if json_response and all(key in json_response for key in ["title", "text", "proceeding", "category"]):
                    return json_response
                else:
                    print(f"[WARNING] Invalid JSON structure from DeepSeek. Text: {response_text[:300]}...")
                    raise ValueError("Invalid JSON structure")
            except Exception as e:
                print(f"[ERROR] DeepSeek generation/parsing failed: {e}")
                return {
                    "title": "Автоматично сформований заголовок (DeepSeek)",
                    "text": response_text.strip() if 'response_text' in locals() else "Помилка при отриманні відповіді від DeepSeek",
                    "proceeding": "Не визначено",
                    "category": "Помилка API/Парсингу"
                }

        elif provider == ModelProvider.ANTHROPIC.value:
            client = Anthropic(api_key=ANTHROPIC_API_KEY)

            # Debug: check what we're sending to Anthropic
            print(f"[DEBUG] Sending to Anthropic - content length: {len(content)}")
            print(f"[DEBUG] Content preview: {content[:500]}")
            print(f"[DEBUG] ANTHROPIC_API_KEY set: {bool(ANTHROPIC_API_KEY)}, length: {len(ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else 0}")

            messages = [{
                "role": "user",
                "content": content
            }]

            # Prepare message creation parameters
            message_params = {
                "model": model_name,
                "max_tokens": MAX_TOKENS_CONFIG["anthropic"],
                "system": system_prompt,
                "messages": messages,
                "temperature": GENERATION_TEMPERATURE
            }

            # Add thinking config if enabled (only for Claude 4.5+ models)
            if thinking_enabled and "claude" in model_name.lower() and "-4-5-" in model_name:
                message_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": int(thinking_budget)
                }

            # Retry logic for connection errors
            max_retries = 3
            last_error = None
            for attempt in range(max_retries):
                try:
                    print(f"[DEBUG] Anthropic API call attempt {attempt + 1}/{max_retries}")
                    response = client.messages.create(**message_params)
                    break
                except Exception as api_err:
                    last_error = api_err
                    error_type = type(api_err).__name__
                    print(f"[ERROR] Anthropic API attempt {attempt + 1} failed: {error_type}: {str(api_err)}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 1, 2, 4 seconds
                        print(f"[DEBUG] Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise Exception(f"Помилка з'єднання з Anthropic API після {max_retries} спроб: {error_type}: {str(api_err)}")

            try:
                # Extract text from response, handling different content block types
                response_text = ""
                thinking_text = ""
                
                for block in response.content:
                    if hasattr(block, 'type'):
                        if block.type == 'thinking':
                            # Separate thinking blocks (if any)
                            thinking_text += getattr(block, 'thinking', '')
                        elif block.type == 'text':
                            response_text += getattr(block, 'text', '')
                    elif hasattr(block, 'text'):
                        # Fallback for simpler response format
                        response_text += block.text
                
                if thinking_text:
                    print(f"[DEBUG] Anthropic thinking block length: {len(thinking_text)}")
                
                print(f"[DEBUG] Anthropic response text length: {len(response_text)}")
                print(f"[DEBUG] Response preview (first 500 chars): {response_text[:500]}")
                
                # Спробуємо розпарсити JSON за допомогою універсальної функції
                json_response = extract_json_from_text(response_text)
                
                if json_response:
                    # Validate required fields
                    required = ["title", "text", "proceeding", "category"]
                    missing = [f for f in required if f not in json_response]
                    if missing:
                        print(f"[WARNING] Missing fields in Anthropic JSON: {missing}")
                        for field in missing:
                            if field not in json_response:
                                json_response[field] = "Не вказано"
                    return json_response
                else:
                    print(f"[ERROR] Could not extract JSON from Anthropic response")
                    # Fallback: create structured response from raw text
                    return {
                        "title": "Автоматично згенерований заголовок",
                        "text": response_text.strip(),
                        "proceeding": "Не визначено",
                        "category": "Помилка парсингу JSON"
                    }
            except Exception as e:
                # Скидання помилки для подальшого аналізу
                error_details = str(e)
                if hasattr(e, 'response'):
                    error_details += f"\nResponse: {e.response}"
                raise RuntimeError(f"Error in Anthropic analysis: {error_details}")

        elif provider == ModelProvider.GEMINI.value:
            if not os.environ.get("GEMINI_API_KEY"):
                raise ValueError("Gemini API key not found in environment variables")

            try:
                # Debug: Log input parameters
                print(f"[DEBUG] Gemini Generation:")
                print(f"[DEBUG] Model: {model_name}")
                print(f"[DEBUG] Input text length: {len(input_text)}")
                print(f"[DEBUG] Court decision text length: {len(court_decision_text)}")
                
                # Use new google.genai API
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
                
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=content),
                        ],
                    ),
                ]
                
                # Build config based on model version
                config_params = {
                    "temperature": GENERATION_TEMPERATURE,
                    "max_output_tokens": MAX_TOKENS_CONFIG["gemini"],
                    "system_instruction": [
                        types.Part.from_text(text=system_prompt),
                    ],
                }
                
                # Add thinking config if enabled (only for Gemini 3+ models)
                if thinking_enabled and model_name.startswith("gemini-3"):
                    config_params["thinking_config"] = types.ThinkingConfig(
                        thinking_level=thinking_level.upper()
                    )
                
                # Only add response_mime_type for models that support it
                # if not model_name.startswith("gemini-3"):
                #     config_params["response_mime_type"] = "application/json"
                
                generate_content_config = types.GenerateContentConfig(**config_params)

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=generate_content_config,
                )
                response_text = response.text

                # Перевіряємо наявність тексту у відповіді
                if not response_text:
                    raise Exception("Пуста відповідь від моделі Gemini")

                print(f"[DEBUG] Gemini response length: {len(response_text)}")
                print(f"[DEBUG] Gemini response preview: {response_text[:300]}...")

                # Спробуємо розпарсити JSON за допомогою універсальної функції
                json_response = extract_json_from_text(response_text)
                
                if json_response:
                    # Перевіряємо наявність всіх необхідних полів
                    required_fields = ["title", "text", "proceeding", "category"]
                    if all(field in json_response for field in required_fields):
                        return json_response
                    else:
                        missing_fields = [field for field in required_fields if field not in json_response]
                        print(f"[WARNING] Gemini response missing fields: {missing_fields}")
                        # Fallback for missing fields
                        for field in required_fields:
                            if field not in json_response:
                                json_response[field] = "Не визначено"
                        return json_response
                else:
                    print(f"[ERROR] Could not extract JSON from Gemini response: {response_text[:300]}...")
                    return {
                        "title": "Автоматично сформований заголовок",
                        "text": response_text.strip(),
                        "proceeding": "Не визначено",
                        "category": "Помилка парсингу"
                    }

            except Exception as e:
                print(f"Error in Gemini generation: {str(e)}")
                return {
                    "title": "Error in Gemini generation",
                    "text": str(e),
                    "proceeding": "Error",
                    "category": "Error"
                }

    except Exception as e:
        print(f"Error in generate_legal_position: {str(e)}")
        return {
            "title": "Error",
            "text": str(e),
            "proceeding": "Unknown",
            "category": "Error"
        }


async def search_with_ai_action(legal_position_json: Dict) -> Tuple[str, Optional[List[NodeWithScore]]]:
    """Search for relevant legal positions based on input."""
    try:
        if not embed_model:
            return "Помилка: пошук недоступний без налаштованого embedding API ключа (OpenAI або Gemini)", None

        retriever = search_components.get_retriever()
        if not retriever:
            return "Помилка: компоненти пошуку не ініціалізовано", None

        query_text = (
            f"{legal_position_json['title']}: "
            f"{legal_position_json['text']}: "
            f"{legal_position_json['proceeding']}: "
            f"{legal_position_json['category']}"
        )

        nodes = await retriever.aretrieve(query_text)

        # Видалення дублікатів
        unique_nodes = deduplicate_nodes(nodes)

        # Обмеження кількості результатів
        top_nodes = unique_nodes[:Settings.similarity_top_k]

        sources_output = "\n **Результати пошуку (наявні правові позиції Верховного Суду):** \n\n"
        for index, node in enumerate(top_nodes, start=1):
            source_title = node.node.metadata.get('title')
            doc_ids = node.node.metadata.get('doc_id')
            lp_ids = node.node.metadata.get('lp_id')
            links = get_links_html(doc_ids)
            links_lp = get_links_html_lp(lp_ids)
            sources_output += f"\n[{index}] *{source_title}* ⚖️ {links_lp} | {links} 👉 Score: {node.score}\n"

        return sources_output, top_nodes

    except Exception as e:
        return f"Помилка при пошуку: {str(e)}", None


async def search_with_raw_text(input_text: str) -> Tuple[str, Optional[List[NodeWithScore]]]:
    """Пошук на основі вхідного тексту з вибором відповідного ретривера."""
    try:
        if not input_text:
            return "Помилка: Порожній текст для пошуку", None

        if not embed_model:
            return "Помилка: пошук недоступний без налаштованого embedding API ключа (OpenAI або Gemini)", None

        retriever = search_components.get_retriever()
        if not retriever:
            return "Помилка: компоненти пошуку не ініціалізовано", None

        # Вибір ретривера залежно від довжини тексту
        text_length = get_text_length_without_spaces(input_text)
        try:
            if text_length < 1024:
                nodes = await retriever.aretrieve(input_text)
            else:
                # Для довгих текстів використовуємо тільки BM25
                bm25_retriever = search_components.get_component('bm25_retriever')
                if not bm25_retriever:
                    return "Помилка: BM25 ретривер не ініціалізовано", None
                nodes = await bm25_retriever.aretrieve(input_text)

            if not nodes:
                return "Не знайдено відповідних правових позицій", None

            # Видалення дублікатів
            unique_nodes = deduplicate_nodes(nodes)

            # Обмеження кількості результатів
            top_nodes = unique_nodes[:Settings.similarity_top_k]

            if not top_nodes:
                return "Не знайдено унікальних правових позицій після дедуплікації", None

            sources_output = "\n **Результати пошуку (наявні правові позиції Верховного Суду):** \n\n"
            for index, node in enumerate(top_nodes, start=1):
                source_title = node.node.metadata.get('title', 'Невідомий заголовок')
                doc_ids = node.node.metadata.get('doc_id', '')
                lp_ids = node.node.metadata.get('lp_id', '')
                links = get_links_html(doc_ids)
                links_lp = get_links_html_lp(lp_ids)
                sources_output += f"\n[{index}] *{source_title}* ⚖️ {links_lp} | {links} 👉 Score: {node.score}\n"

            return sources_output, top_nodes

        except Exception as e:
            return f"Помилка під час виконання пошуку: {str(e)}", None

    except Exception as e:
        return f"Помилка при пошуку: {str(e)}", None

async def analyze_action(
        legal_position_json: Dict,
        question: str,
        nodes: List[NodeWithScore],
        provider: str,
        model_name: str
) -> str:
    """Analyze search results using AI."""
    try:
        workflow = PrecedentAnalysisWorkflow(
            provider=ModelProvider(provider),
            model_name=AnalysisModelName(model_name)
        )

        query = (
            f"{legal_position_json['title']}: "
            f"{legal_position_json['text']}: "
            f"{legal_position_json['proceeding']}: "
            f"{legal_position_json['category']}"
        )

        response_text = await workflow.run(
            query=query,
            question=question,
            nodes=nodes
        )

        output = f"**Аналіз ШІ (модель: {model_name}):**\n{response_text}\n\n"
        output += "**Наявні в базі правові позицій Верховного Суду:**\n\n"

        analysis_lines = response_text.split('\n')
        for line in analysis_lines:
            if line.startswith('* ['):
                index = line[3:line.index(']')]
                node = nodes[int(index) - 1]
                source_node = node.node

                source_title = source_node.metadata.get('title', 'Невідомий заголовок')
                source_text_lp = node.text
                doc_ids = source_node.metadata.get('doc_id')
                lp_id = source_node.metadata.get('lp_id')

                links = get_links_html(doc_ids)
                links_lp = get_links_html_lp(lp_id)

                output += f"[{index}]: *{clean_text(source_title)}* | {clean_text(source_text_lp)} | {links_lp} | {links}\n\n"

        return output

    except Exception as e:
        return f"Помилка при аналізі: {str(e)}"


if __name__ == "__main__":
    try:
        # Check which providers are available
        available_providers = []
        if OPENAI_API_KEY:
            available_providers.append("OpenAI")
        if ANTHROPIC_API_KEY:
            available_providers.append("Anthropic")
        if os.getenv("GEMINI_API_KEY"):
            available_providers.append("Gemini")
        if DEEPSEEK_API_KEY:
            available_providers.append("DeepSeek")

        if not available_providers:
            print("Error: No AI provider API keys configured. Please set at least one of:",
                  file=sys.stderr)
            print("  - OPENAI_API_KEY", file=sys.stderr)
            print("  - ANTHROPIC_API_KEY", file=sys.stderr)
            print("  - GEMINI_API_KEY", file=sys.stderr)
            print("  - DEEPSEEK_API_KEY", file=sys.stderr)
            sys.exit(1)

        print(f"Available AI providers: {', '.join(available_providers)}")

        # Check embedding availability for search
        if not embed_model:
            print("Warning: No embedding model configured. Search functionality will be disabled.")
            print("  To enable search, set either OPENAI_API_KEY or GEMINI_API_KEY")
        elif GEMINI_API_KEY and not OPENAI_API_KEY:
            print("Info: Using Gemini embeddings for search (OpenAI not configured)")

        if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
            print("Warning: AWS credentials not configured. Will use local files only.")

        # Initialize components
        if initialize_components():
            print("Components initialized successfully!")

            # Import create_gradio_interface here to avoid circular import
            from interface import create_gradio_interface

            # Create and launch the interface
            app = create_gradio_interface()
            app.launch(
                server_name="0.0.0.0",
                server_port=7860,
                share=True
            )
        else:
            print("Failed to initialize components. Please check the logs for details.",
                  file=sys.stderr)
            sys.exit(1)
    except ImportError as e:
        print(f"Error importing required modules: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {str(e)}", file=sys.stderr)
        sys.exit(1)