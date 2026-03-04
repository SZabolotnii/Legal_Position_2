"""
Dynamic model enums generated from YAML configuration.
This module provides backward compatibility while using YAML as single source of truth.
"""

from enum import Enum
from typing import Dict, List, Optional
from .loader import ConfigLoader


class ModelRegistry:
    """Registry for dynamically generated model enums from YAML."""
    
    _instance = None
    _generation_models: Dict[str, str] = {}
    _analysis_models: Dict[str, str] = {}
    _default_generation_model: Optional[str] = None
    _default_analysis_model: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        """Load models from YAML configuration."""
        loader = ConfigLoader()
        settings = loader.load_config(validate_api_keys=False)
        
        # Load generation models
        generation_config = settings.models.generation
        for provider in ['openai', 'anthropic', 'gemini', 'deepseek']:
            model_list = getattr(generation_config, provider, [])
            for model in model_list:
                model_name = model.name
                # Create enum-friendly key from model name
                enum_key = self._create_enum_key(model_name, provider)
                self._generation_models[enum_key] = model_name
                
                # Track default model
                if model.default:
                    self._default_generation_model = model_name
        
        # Load analysis models
        analysis_config = settings.models.analysis
        for provider in ['openai', 'anthropic', 'gemini', 'deepseek']:
            model_list = getattr(analysis_config, provider, [])
            for model in model_list:
                model_name = model.name
                # Create enum-friendly key from model name
                enum_key = self._create_enum_key(model_name, provider)
                self._analysis_models[enum_key] = model_name
                
                # Track default model
                if model.default:
                    self._default_analysis_model = model_name
    
    @staticmethod
    def _create_enum_key(model_name: str, provider: str) -> str:
        """Create enum-friendly key from model name."""
        # Handle fine-tuned models
        if model_name.startswith('ft:'):
            if 'lp-1700-part-cd-120' in model_name:
                return 'GPT4o_MINI_LP'
            elif 'legal-position-1700' in model_name:
                return 'GPT4o_LP'
            else:
                # Generic fine-tuned model
                return 'GPT4o_FT'
        
        if model_name == 'gpt-5.3-chat-latest':
            return 'GPT5_3_CHAT_LATEST'
        elif model_name == 'gpt-5.2':
            return 'GPT5_2'
        elif model_name == 'gpt-5-mini':
            return 'GPT5_MINI'
        elif model_name == 'gpt-4.1':
            return 'GPT4_1'
        elif model_name == 'gpt-4o':
            return 'GPT4o'
        elif model_name == 'gpt-4o-mini':
            return 'GPT4o_MINI'
        elif model_name == 'claude-opus-4-6':
            return 'CLAUDE_OPUS_4_6'
        elif model_name == 'claude-sonnet-4-6':
            return 'CLAUDE_SONNET_4_6'
        elif model_name == 'claude-haiku-4-5-20251001':
            return 'CLAUDE_HAIKU_4_5'
        elif model_name == 'gemini-3-flash-preview':
            return 'GEMINI_3_FLASH'
        elif model_name == 'gemini-3-pro-preview':
            return 'GEMINI_3_PRO'
        elif model_name == 'deepseek-chat':
            return 'DEEPSEEK_CHAT'
        elif model_name == 'deepseek-reasoner':
            return 'DEEPSEEK_REASONER'
        else:
            # Fallback: convert to uppercase and replace hyphens
            return model_name.upper().replace('-', '_').replace('.', '_')
    
    def get_generation_models(self) -> Dict[str, str]:
        """Get all generation models."""
        return self._generation_models.copy()
    
    def get_analysis_models(self) -> Dict[str, str]:
        """Get all analysis models."""
        return self._analysis_models.copy()
    
    def get_default_generation_model(self) -> Optional[str]:
        """Get default generation model."""
        return self._default_generation_model
    
    def get_default_analysis_model(self) -> Optional[str]:
        """Get default analysis model."""
        return self._default_analysis_model
    
    def get_models_by_provider(self, provider: str, model_type: str = 'generation') -> List[str]:
        """Get models for a specific provider."""
        loader = ConfigLoader()
        settings = loader.load_config(validate_api_keys=False)
        
        if model_type == 'generation':
            provider_models = getattr(settings.models.generation, provider, [])
        else:
            provider_models = getattr(settings.models.analysis, provider, [])
        
        return [model.name for model in provider_models]


# Create singleton instance
_registry = ModelRegistry()

# Dynamically create GenerationModelName enum
GenerationModelName = Enum(
    'GenerationModelName',
    _registry.get_generation_models(),
    type=str
)

# Dynamically create AnalysisModelName enum
AnalysisModelName = Enum(
    'AnalysisModelName',
    _registry.get_analysis_models(),
    type=str
)

# Default models
DEFAULT_GENERATION_MODEL = None
DEFAULT_ANALYSIS_MODEL = None

# Set defaults after enum creation
_default_gen = _registry.get_default_generation_model()
_default_ana = _registry.get_default_analysis_model()

if _default_gen:
    for member in GenerationModelName:
        if member.value == _default_gen:
            DEFAULT_GENERATION_MODEL = member
            break

if _default_ana:
    for member in AnalysisModelName:
        if member.value == _default_ana:
            DEFAULT_ANALYSIS_MODEL = member
            break


# Helper functions for backward compatibility
def get_generation_models_by_provider(provider: str) -> List[str]:
    """Get generation models for a specific provider."""
    return _registry.get_models_by_provider(provider, 'generation')


def get_analysis_models_by_provider(provider: str) -> List[str]:
    """Get analysis models for a specific provider."""
    return _registry.get_models_by_provider(provider, 'analysis')


__all__ = [
    'GenerationModelName',
    'AnalysisModelName',
    'DEFAULT_GENERATION_MODEL',
    'DEFAULT_ANALYSIS_MODEL',
    'ModelRegistry',
    'get_generation_models_by_provider',
    'get_analysis_models_by_provider',
]
