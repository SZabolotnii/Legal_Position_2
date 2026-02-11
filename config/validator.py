"""
Configuration validator.
"""
import os
from pathlib import Path
from typing import List, Optional
from config.settings import Settings


class ConfigValidator:
    """Validates application configuration."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the validator.
        
        Args:
            settings: Settings object to validate
        """
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all validations pass, False otherwise
        """
        self.errors = []
        self.warnings = []
        
        self.validate_api_keys()
        self.validate_paths()
        self.validate_models()
        self.validate_session_config()
        self.validate_redis_config()
        
        return len(self.errors) == 0
    
    def validate_api_keys(self) -> None:
        """Validate that required API keys are present."""
        required_keys = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'gemini': 'GEMINI_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY'
        }
        
        for provider in self.settings.models.providers:
            key_name = required_keys.get(provider)
            if key_name and not os.getenv(key_name):
                self.errors.append(
                    f"Missing API key for provider '{provider}': {key_name} not found in environment"
                )
        
        # AWS credentials are optional
        if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
            self.warnings.append(
                "AWS credentials not found. S3 functionality will be disabled. "
                "Will use local files only."
            )
    
    def validate_paths(self) -> None:
        """Validate file paths and directories."""
        # Validate local directory
        local_dir = Path(self.settings.aws.local_dir)
        if not local_dir.exists():
            self.warnings.append(
                f"Local directory does not exist: {local_dir}. "
                f"It will be created on initialization."
            )
        
        # Validate required files
        for filename in self.settings.required_files:
            filepath = local_dir / filename
            if not filepath.exists():
                self.warnings.append(
                    f"Required file not found: {filepath}. "
                    f"Will attempt to download from S3 if available."
                )
        
        # Validate logging directory
        if self.settings.logging.file:
            log_file = Path(self.settings.logging.file)
            log_dir = log_file.parent
            if not log_dir.exists():
                self.warnings.append(
                    f"Log directory does not exist: {log_dir}. "
                    f"It will be created on initialization."
                )
    
    def validate_models(self) -> None:
        """Validate model configurations."""
        # Check that each provider has at least one model
        for provider in self.settings.models.providers:
            gen_models = getattr(self.settings.models.generation, provider, [])
            analysis_models = getattr(self.settings.models.analysis, provider, [])
            
            if not gen_models:
                self.warnings.append(
                    f"No generation models configured for provider '{provider}'"
                )
            
            if not analysis_models:
                self.warnings.append(
                    f"No analysis models configured for provider '{provider}'"
                )
            
            # Check that at least one model is marked as default
            if gen_models and not any(m.default for m in gen_models):
                self.warnings.append(
                    f"No default generation model set for provider '{provider}'"
                )
            
            if analysis_models and not any(m.default for m in analysis_models):
                self.warnings.append(
                    f"No default analysis model set for provider '{provider}'"
                )
    
    def validate_session_config(self) -> None:
        """Validate session configuration."""
        if self.settings.session.timeout_minutes <= 0:
            self.errors.append("Session timeout must be positive")
        
        if self.settings.session.cleanup_interval_minutes <= 0:
            self.errors.append("Session cleanup interval must be positive")
        
        if self.settings.session.max_sessions <= 0:
            self.errors.append("Max sessions must be positive")
        
        if self.settings.session.cleanup_interval_minutes >= self.settings.session.timeout_minutes:
            self.warnings.append(
                "Session cleanup interval should be less than timeout for efficiency"
            )
    
    def validate_redis_config(self) -> None:
        """Validate Redis configuration if Redis storage is used."""
        if self.settings.session.storage_type == "redis":
            if not self.settings.redis.host:
                self.errors.append("Redis host is required when using Redis storage")
            
            if self.settings.redis.port <= 0 or self.settings.redis.port > 65535:
                self.errors.append("Redis port must be between 1 and 65535")
            
            if self.settings.redis.db < 0:
                self.errors.append("Redis database number must be non-negative")
    
    def get_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Get list of validation warnings."""
        return self.warnings
    
    def print_report(self) -> None:
        """Print validation report."""
        if self.errors:
            print("\n❌ Configuration Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  Configuration Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ Configuration is valid!")


def validate_configuration(settings: Settings, print_report: bool = True) -> bool:
    """
    Validate configuration settings.
    
    Args:
        settings: Settings object to validate
        print_report: Whether to print validation report
        
    Returns:
        True if configuration is valid, False otherwise
    """
    validator = ConfigValidator(settings)
    is_valid = validator.validate_all()
    
    if print_report:
        validator.print_report()
    
    return is_valid
