#!/usr/bin/env python3
"""
Test script to verify API connections for OpenAI and DeepSeek
"""
import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_openai():
    """Test OpenAI API connection"""
    print("\n" + "="*60)
    print("Testing OpenAI API Connection")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✓ API Key found (length: {len(api_key)})")
    
    try:
        # Test with HTTP/2 enabled (default)
        print("\n[Test 1] Using default settings (HTTP/2 enabled)...")
        client = OpenAI(api_key=api_key, timeout=30.0)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'connection test passed'"}],
            max_tokens=10
        )
        print(f"✅ Success with HTTP/2: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed with HTTP/2: {type(e).__name__}: {str(e)}")
    
    try:
        # Test with HTTP/2 disabled
        print("\n[Test 2] Using HTTP/1.1 (HTTP/2 disabled)...")
        client = OpenAI(
            api_key=api_key, 
            timeout=30.0,
            http_client=httpx.Client(http2=False, timeout=30.0)
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'connection test passed'"}],
            max_tokens=10
        )
        print(f"✅ Success with HTTP/1.1: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Failed with HTTP/1.1: {type(e).__name__}: {str(e)}")
        return False


def test_deepseek():
    """Test DeepSeek API connection"""
    print("\n" + "="*60)
    print("Testing DeepSeek API Connection")
    print("="*60)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in environment")
        return False
    
    print(f"✓ API Key found (length: {len(api_key)})")
    
    try:
        # Test with HTTP/2 enabled (default)
        print("\n[Test 1] Using default settings (HTTP/2 enabled)...")
        client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com",
            timeout=30.0
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Say 'connection test passed'"}],
            max_tokens=10
        )
        print(f"✅ Success with HTTP/2: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed with HTTP/2: {type(e).__name__}: {str(e)}")
    
    try:
        # Test with HTTP/2 disabled
        print("\n[Test 2] Using HTTP/1.1 (HTTP/2 disabled)...")
        client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com",
            timeout=30.0,
            http_client=httpx.Client(http2=False, timeout=30.0)
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Say 'connection test passed'"}],
            max_tokens=10
        )
        print(f"✅ Success with HTTP/1.1: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Failed with HTTP/1.1: {type(e).__name__}: {str(e)}")
        return False


def test_network_connectivity():
    """Test basic network connectivity"""
    print("\n" + "="*60)
    print("Testing Network Connectivity")
    print("="*60)
    
    urls = [
        "https://api.openai.com",
        "https://api.deepseek.com",
        "https://api.anthropic.com",
        "https://generativelanguage.googleapis.com"
    ]
    
    for url in urls:
        try:
            client = httpx.Client(timeout=10.0)
            response = client.get(url)
            print(f"✅ {url}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    print("\n🔍 API Connection Test Suite")
    print("="*60)
    
    # Test network connectivity first
    test_network_connectivity()
    
    # Test OpenAI
    openai_ok = test_openai()
    
    # Test DeepSeek
    deepseek_ok = test_deepseek()
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"OpenAI:  {'✅ OK' if openai_ok else '❌ FAILED'}")
    print(f"DeepSeek: {'✅ OK' if deepseek_ok else '❌ FAILED'}")
    print("="*60)
