import logging
import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Keys
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Конфігурація Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    from google import genai
    # New google.genai package - client-based approach
    genai_client = genai.Client(api_key=GEMINI_API_KEY)


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"


# NOTE: All configuration values (AWS, LlamaIndex, Schemas, Models, etc.) are now 
# defined in config/environments/default.yaml to avoid duplication.
# This file only contains:
#   1. API key loading from environment variables
#   2. ModelProvider enum (Python-specific type)
#   3. Gemini client initialization
#   4. Environment validation function
#
# To access configuration: from config import get_settings
# To access models: from config import GenerationModelName, AnalysisModelName, DEFAULT_GENERATION_MODEL
# For backward compatibility, you can still: from config import BUCKET_NAME, LOCAL_DIR, etc.


# Check if required environment variables are set
def validate_environment(require_ai_provider: bool = True, require_aws: bool = False):
    """
    Validate environment variables.

    Args:
        require_ai_provider: If True, requires at least one AI provider API key
        require_aws: If True, requires AWS credentials

    Returns:
        dict: Status of each provider (available/missing)
    """
    status = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "deepseek": bool(os.getenv("DEEPSEEK_API_KEY")),
        "aws": bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
    }

    # Check if at least one AI provider is available
    if require_ai_provider:
        if not any([status["openai"], status["anthropic"], status["gemini"], status["deepseek"]]):
            raise ValueError(
                "At least one AI provider API key is required. Please set one of: "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY"
            )

    # Check if AWS is required
    if require_aws and not status["aws"]:
        raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are required")

    return status