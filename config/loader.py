"""
Configuration loader for YAML files.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from config.settings import Settings


class ConfigLoader:
    """Loads and merges YAML configuration files."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Path to configuration directory. Defaults to config/environments/
        """
        if config_dir is None:
            # Get the directory where this file is located
            current_dir = Path(__file__).parent
            config_dir = current_dir / "environments"
        
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Configuration directory not found: {self.config_dir}")
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        Load a YAML file and return its contents.
        
        Args:
            filename: Name of the YAML file to load
            
        Returns:
            Dictionary containing the YAML contents
        """
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Replace environment variables in the format ${VAR_NAME}
            content = self._replace_env_vars(content)
            return yaml.safe_load(content)
    
    def _replace_env_vars(self, content: str) -> str:
        """
        Replace environment variables in the format ${VAR_NAME} or ${VAR_NAME:default}.
        
        Args:
            content: String content with potential environment variables
            
        Returns:
            Content with environment variables replaced
        """
        import re
        
        def replace_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                return os.getenv(var_expr.strip(), match.group(0))
        
        # Pattern to match ${VAR_NAME} or ${VAR_NAME:default}
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_var, content)
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries.
        
        Args:
            base_config: Base configuration dictionary
            override_config: Configuration to override base with
            
        Returns:
            Merged configuration dictionary
        """
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def load_config(self, environment: Optional[str] = None, validate_api_keys: bool = True) -> Settings:
        """
        Load configuration for the specified environment.
        
        Args:
            environment: Environment name (development, production, etc.)
                        If None, uses ENVIRONMENT env var or defaults to production
            validate_api_keys: Whether to validate API keys during loading
            
        Returns:
            Settings object with loaded configuration
        """
        # Determine environment
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'production')
        
        # Load default configuration
        default_config = self.load_yaml('default.yaml')
        
        # Load environment-specific configuration if it exists
        env_file = f'{environment}.yaml'
        env_config = {}
        
        env_filepath = self.config_dir / env_file
        if env_filepath.exists():
            env_config = self.load_yaml(env_file)
        else:
            print(f"Warning: Environment config file not found: {env_filepath}")
            print(f"Using default configuration only")
        
        # Merge configurations
        merged_config = self.merge_configs(default_config, env_config)
        
        # Create and validate Settings object
        try:
            settings = Settings(**merged_config)
            
            # Optionally validate API keys
            if validate_api_keys:
                self.validate_config(settings)
            
            return settings
        except Exception as e:
            raise ValueError(f"Failed to validate configuration: {str(e)}")
    
    def validate_config(self, settings: Settings) -> bool:
        """
        Validate the loaded configuration.
        
        Args:
            settings: Settings object to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required environment variables for API keys
        required_env_vars = []
        
        if 'openai' in settings.models.providers:
            required_env_vars.append('OPENAI_API_KEY')
        
        if 'anthropic' in settings.models.providers:
            required_env_vars.append('ANTHROPIC_API_KEY')
        
        if 'gemini' in settings.models.providers:
            required_env_vars.append('GEMINI_API_KEY')
        
        if 'deepseek' in settings.models.providers:
            required_env_vars.append('DEEPSEEK_API_KEY')
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        
        # Validate local directory exists or can be created
        local_dir = Path(settings.aws.local_dir)
        if not local_dir.exists():
            try:
                local_dir.mkdir(parents=True, exist_ok=True)
                print(f"Created local directory: {local_dir}")
            except Exception as e:
                raise ValueError(f"Cannot create local directory {local_dir}: {str(e)}")
        
        # Validate logging directory
        if settings.logging.file:
            log_dir = Path(settings.logging.file).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                    print(f"Created log directory: {log_dir}")
                except Exception as e:
                    raise ValueError(f"Cannot create log directory {log_dir}: {str(e)}")
        
        return True


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None
_settings: Optional[Settings] = None


def get_config_loader() -> ConfigLoader:
    """Get or create the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_settings(environment: Optional[str] = None, reload: bool = False, validate_api_keys: bool = True) -> Settings:
    """
    Get the application settings.
    
    Args:
        environment: Environment name (development, production, etc.)
        reload: Force reload of configuration
        validate_api_keys: Whether to validate API keys
        
    Returns:
        Settings object
    """
    global _settings
    
    if _settings is None or reload:
        loader = get_config_loader()
        _settings = loader.load_config(environment, validate_api_keys=validate_api_keys)
    
    return _settings
