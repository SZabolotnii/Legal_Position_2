"""
Test script for configuration system.
"""
import os
from config import get_settings, validate_configuration


def test_configuration():
    """Test configuration loading and validation."""
    print("=" * 60)
    print("Testing Configuration System")
    print("=" * 60)
    
    # Test loading default configuration (without API key validation for testing)
    print("\n1. Loading default configuration...")
    try:
        settings = get_settings(validate_api_keys=False)
        print(f"✅ Configuration loaded successfully!")
        print(f"   Environment: {settings.app.environment}")
        print(f"   Debug mode: {settings.app.debug}")
        print(f"   Local directory: {settings.aws.local_dir}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {str(e)}")
        return False
    
    # Test validation
    print("\n2. Validating configuration...")
    is_valid = validate_configuration(settings, print_report=True)
    
    if not is_valid:
        print("\n❌ Configuration validation failed!")
        return False
    
    # Test environment-specific loading
    print("\n3. Testing environment-specific configuration...")
    
    # Test development environment
    print("\n   a) Development environment:")
    try:
        dev_settings = get_settings(environment='development', reload=True, validate_api_keys=False)
        print(f"   ✅ Loaded development config")
        print(f"      Debug mode: {dev_settings.app.debug}")
        print(f"      Environment: {dev_settings.app.environment}")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
    
    # Test production environment
    print("\n   b) Production environment:")
    try:
        prod_settings = get_settings(environment='production', reload=True, validate_api_keys=False)
        print(f"   ✅ Loaded production config")
        print(f"      Debug mode: {prod_settings.app.debug}")
        print(f"      Environment: {prod_settings.app.environment}")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
    
    # Test configuration values
    print("\n4. Testing configuration values...")
    settings = get_settings(reload=True, validate_api_keys=False)
    
    print(f"   LlamaIndex settings:")
    print(f"      Context window: {settings.llama_index.context_window}")
    print(f"      Chunk size: {settings.llama_index.chunk_size}")
    print(f"      Similarity top k: {settings.llama_index.similarity_top_k}")
    
    print(f"\n   Session settings:")
    print(f"      Timeout: {settings.session.timeout_minutes} minutes")
    print(f"      Max sessions: {settings.session.max_sessions}")
    print(f"      Storage type: {settings.session.storage_type}")
    
    print(f"\n   Model providers: {', '.join(settings.models.providers)}")
    
    # Test model configurations
    print(f"\n   Generation models:")
    for provider in settings.models.providers:
        models = getattr(settings.models.generation, provider, [])
        if models:
            default_model = next((m for m in models if m.default), models[0])
            print(f"      {provider}: {default_model.display_name}")
    
    print(f"\n   Analysis models:")
    for provider in settings.models.providers:
        models = getattr(settings.models.analysis, provider, [])
        if models:
            default_model = next((m for m in models if m.default), models[0])
            print(f"      {provider}: {default_model.display_name}")
    
    print("\n" + "=" * 60)
    print("✅ All configuration tests passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    # Set test environment variables if not present
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set. Some validations may fail.")
    
    success = test_configuration()
    exit(0 if success else 1)
