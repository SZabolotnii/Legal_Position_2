#!/usr/bin/env python3
"""
Test script to check available AI providers
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_available_providers():
    """Get status of all AI providers."""
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "deepseek": bool(os.getenv("DEEPSEEK_API_KEY"))
    }

if __name__ == "__main__":
    providers = get_available_providers()
    
    print("=" * 50)
    print("🔑 API Keys Status")
    print("=" * 50)
    
    for provider, available in providers.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"{provider.upper():12} : {status}")
    
    print("=" * 50)
    
    available_list = [p for p, avail in providers.items() if avail]
    unavailable_list = [p for p, avail in providers.items() if not avail]
    
    print(f"\n✅ Available providers: {', '.join(available_list) if available_list else 'None'}")
    print(f"❌ Unavailable providers: {', '.join(unavailable_list) if unavailable_list else 'None'}")
    
    if not available_list:
        print("\n⚠️ WARNING: No AI providers available!")
        print("Please set at least one API key in your .env file:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GEMINI_API_KEY")
        print("  - DEEPSEEK_API_KEY")
