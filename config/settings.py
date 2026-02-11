"""
Pydantic models for application configuration.
"""
from typing import List, Dict, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from enum import Enum


class AppConfig(BaseModel):
    """General application settings."""
    name: str
    version: str
    debug: bool
    environment: str


class AWSConfig(BaseModel):
    """AWS S3 configuration."""
    bucket_name: str
    region: str
    prefix_retriever: str
    local_dir: str

    @validator('local_dir')
    def validate_local_dir(cls, v):
        """Ensure local_dir is a valid path string."""
        return str(Path(v))


class LlamaIndexConfig(BaseModel):
    """LlamaIndex settings."""
    context_window: int
    chunk_size: int
    similarity_top_k: int
    embed_model: str

    @validator('context_window', 'chunk_size', 'similarity_top_k')
    def validate_positive(cls, v):
        """Ensure values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class MaxTokensConfig(BaseModel):
    """Max tokens configuration for different providers."""
    openai: int = 8192
    anthropic: int = 8192
    gemini: int = 8192
    deepseek: int = 8192


class GenerationConfig(BaseModel):
    """Generation settings."""
    max_tokens: MaxTokensConfig
    max_tokens_analysis: int = 2000
    temperature: float = 0.0

    @validator('max_tokens_analysis')
    def validate_max_tokens_analysis(cls, v):
        """Ensure max_tokens_analysis is positive."""
        if v <= 0:
            raise ValueError("max_tokens_analysis must be positive")
        return v


class ModelInfo(BaseModel):
    """Information about a specific model."""
    name: str
    display_name: str
    default: bool = False


class ModelProviderConfig(BaseModel):
    """Configuration for a model provider."""
    openai: List[ModelInfo] = []
    anthropic: List[ModelInfo] = []
    gemini: List[ModelInfo] = []
    deepseek: List[ModelInfo] = []


class ModelsConfig(BaseModel):
    """Models configuration."""
    default_provider: str
    providers: List[str]
    generation: ModelProviderConfig
    analysis: ModelProviderConfig


class SchemaProperty(BaseModel):
    """JSON schema property definition."""
    type: str
    description: Optional[str] = None


class LegalPositionSchema(BaseModel):
    """Legal position schema configuration."""
    type: str
    required_fields: List[str]
    schema_definition: Dict[str, Any] = Field(alias="schema")

    class Config:
        populate_by_name = True


class SchemasConfig(BaseModel):
    """Schemas configuration."""
    legal_position: LegalPositionSchema


class SessionConfig(BaseModel):
    """Session management configuration."""
    timeout_minutes: int
    cleanup_interval_minutes: int
    max_sessions: int
    storage_type: str

    @validator('storage_type')
    def validate_storage_type(cls, v):
        """Validate storage type."""
        allowed = ["memory", "redis"]
        if v not in allowed:
            raise ValueError(f"storage_type must be one of {allowed}")
        return v


class RedisConfig(BaseModel):
    """Redis configuration."""
    host: str
    port: int
    db: int
    password: Optional[str] = None
    ssl: bool


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str
    format: str
    file: Optional[str]
    max_bytes: int
    backup_count: int
    console: bool

    @validator('level')
    def validate_level(cls, v):
        """Validate logging level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v_upper


class ThemeConfig(BaseModel):
    """Gradio theme configuration."""
    base: str = "Soft"
    primary_hue: str = "blue"
    secondary_hue: str = "indigo"


class GradioConfig(BaseModel):
    """Gradio interface configuration."""
    server_name: str
    server_port: int
    share: bool
    show_error: bool
    ssr_mode: bool = True
    theme: ThemeConfig = ThemeConfig()
    css: Optional[str] = None


class Settings(BaseModel):
    """Main application settings."""
    app: AppConfig
    aws: AWSConfig
    llama_index: LlamaIndexConfig
    generation: GenerationConfig
    models: ModelsConfig
    schemas: SchemasConfig
    required_files: List[str]
    session: SessionConfig
    redis: RedisConfig
    logging: LoggingConfig
    gradio: GradioConfig

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        arbitrary_types_allowed = True
