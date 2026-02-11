"""
Configuration module for Legal Position AI Analyzer.
Provides centralized configuration management with YAML support.
"""

from .settings import Settings
from .loader import ConfigLoader
from .validator import ConfigValidator

# Global settings instance
_settings = None

def get_settings(validate_api_keys: bool = True) -> Settings:
    """
    Get application settings.

    Args:
        validate_api_keys: Whether to validate API keys (default: True)

    Returns:
        Settings: Application configuration
    """
    global _settings

    if _settings is None:
        loader = ConfigLoader()

        # Load configuration from YAML
        _settings = loader.load_config(validate_api_keys=validate_api_keys)

    return _settings

# Backward compatibility - expose common settings as module-level variables
# All non-sensitive configuration is loaded from YAML (single source of truth)
# API keys are loaded from environment variables (.env file)
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# API Keys - always from environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize Gemini client if API key is available
genai_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except ImportError:
        pass

# Helper function to get settings values for backward compatibility
def _get_settings_attr(attr_path: str, default=None):
    """
    Get a nested attribute from settings.
    
    Args:
        attr_path: Dot-separated path like 'aws.bucket_name' or 'llama_index'
        default: Default value if not found
    
    Returns:
        The attribute value or default
    """
    try:
        settings = get_settings(validate_api_keys=False)
        parts = attr_path.split('.')
        value = settings
        for part in parts:
            value = getattr(value, part, None)
            if value is None:
                return default
        return value
    except Exception:
        return default

# AWS Configuration - from YAML
BUCKET_NAME = _get_settings_attr('aws.bucket_name', 'legal-position')
PREFIX_RETRIEVER = _get_settings_attr('aws.prefix_retriever', 'Save_Index_Ivan/')
_local_dir_value = _get_settings_attr('aws.local_dir', 'Save_Index_Ivan')
LOCAL_DIR = Path(_local_dir_value) if isinstance(_local_dir_value, str) else _local_dir_value

# LlamaIndex Settings - from YAML
_llama_config = _get_settings_attr('llama_index')
if _llama_config:
    SETTINGS = {
        "context_window": _llama_config.context_window,
        "chunk_size": _llama_config.chunk_size,
        "similarity_top_k": _llama_config.similarity_top_k,
    }
else:
    SETTINGS = {
        "context_window": 20000,
        "chunk_size": 2048,
        "similarity_top_k": 20
    }

# Generation Settings - from YAML
_generation_config = _get_settings_attr('generation')
if _generation_config:
    MAX_TOKENS_CONFIG = {
        "openai": _generation_config.max_tokens.openai,
        "anthropic": _generation_config.max_tokens.anthropic,
        "gemini": _generation_config.max_tokens.gemini,
        "deepseek": _generation_config.max_tokens.deepseek,
    }
    MAX_TOKENS_ANALYSIS = _generation_config.max_tokens_analysis
    GENERATION_TEMPERATURE = _generation_config.temperature
else:
    # Fallback values
    MAX_TOKENS_CONFIG = {
        "openai": 8192,
        "anthropic": 8192,
        "gemini": 8192,
        "deepseek": 8192,
    }
    MAX_TOKENS_ANALYSIS = 2000
    GENERATION_TEMPERATURE = 0.0

# Schema constants - from YAML
_schema_config = _get_settings_attr('schemas.legal_position')
if _schema_config:
    LEGAL_POSITION_SCHEMA = {
        "type": _schema_config.type,
        "json_schema": {
            "name": "lp_schema",
            "schema": _schema_config.schema_definition,
            "strict": True
        }
    }
else:
    # Fallback if YAML not available
    LEGAL_POSITION_SCHEMA = {
        "type": "json_schema",
        "json_schema": {
            "name": "lp_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the legal position"},
                    "text": {"type": "string", "description": "Text of the legal position"},
                    "proceeding": {"type": "string", "description": "Type of court proceedings"},
                    "category": {"type": "string", "description": "Category of the legal position"},
                },
                "required": ["title", "text", "proceeding", "category"],
                "additionalProperties": False
            },
            "strict": True
        }
    }

# Required files - from YAML
REQUIRED_FILES = _get_settings_attr('required_files', [
    'docstore_es_filter.json',
    'bm25_retriever_short',
    'bm25_retriever'
])

# Import model enums from new models module (dynamically generated from YAML)
from .models import (
    GenerationModelName,
    AnalysisModelName,
    DEFAULT_GENERATION_MODEL,
    DEFAULT_ANALYSIS_MODEL,
    get_generation_models_by_provider,
    get_analysis_models_by_provider,
)

# Import ModelProvider from root config.py for backward compatibility
import sys
from pathlib import Path

_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("root_config", _parent_dir / "config.py")
    if spec and spec.loader:
        root_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(root_config)
        ModelProvider = root_config.ModelProvider
        validate_environment = root_config.validate_environment
    else:
        raise ImportError("Could not load root config.py")
except Exception as e:
    print(f"Warning: Could not import ModelProvider from root config.py: {e}")
    from enum import Enum
    
    class ModelProvider(str, Enum):
        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        GEMINI = "gemini"
        DEEPSEEK = "deepseek"
    
    def validate_environment():
        import os
        required_vars = [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

__all__ = [
    # Main functions
    'get_settings',

    # Backward compatibility
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
    'DEEPSEEK_API_KEY',
    'GEMINI_API_KEY',
    'BUCKET_NAME',
    'PREFIX_RETRIEVER',
    'LOCAL_DIR',
    'SETTINGS',
    'MAX_TOKENS_CONFIG',
    'MAX_TOKENS_ANALYSIS',
    'GENERATION_TEMPERATURE',
    'LEGAL_POSITION_SCHEMA',
    'REQUIRED_FILES',
    'ModelProvider',
    'GenerationModelName',
    'AnalysisModelName',
    'DEFAULT_GENERATION_MODEL',
    'DEFAULT_ANALYSIS_MODEL',
    'validate_environment',
    'get_generation_models_by_provider',
    'get_analysis_models_by_provider',
]
