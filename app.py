#!/usr/bin/env python3
"""
Hugging Face Spaces entry point for Legal Position AI Analyzer
"""
import os
import sys
from pathlib import Path

# Set environment for Hugging Face Spaces
os.environ['GRADIO_SERVER_NAME'] = '0.0.0.0'
os.environ['GRADIO_SERVER_PORT'] = '7860'
# Avoid uvloop shutdown warnings on HF Spaces
os.environ.setdefault('UVICORN_LOOP', 'asyncio')

# Apply nest_asyncio only if needed (some Python versions have conflicts)
# try:
#     import nest_asyncio
#     nest_asyncio.apply()
# except Exception as e:
#     print(f"[WARNING] Could not apply nest_asyncio: {e}")

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ============ Network Diagnostics ============
def run_network_diagnostics():
    """Check outbound network connectivity from HF Spaces container."""
    import urllib.request
    import socket
    
    print("=" * 50)
    print("🔍 NETWORK DIAGNOSTICS")
    print("=" * 50)
    
    # Check proxy env vars
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy', 'ALL_PROXY']
    print("\n📡 Proxy environment variables:")
    for var in proxy_vars:
        val = os.environ.get(var)
        if val:
            print(f"  {var} = {val}")
    if not any(os.environ.get(v) for v in proxy_vars):
        print("  (none set)")
    
    # Check DNS resolution
    hosts = ['api.anthropic.com', 'api.openai.com', 'generativelanguage.googleapis.com']
    print("\n🌐 DNS resolution:")
    for host in hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"  ✅ {host} -> {ip}")
        except socket.gaierror as e:
            print(f"  ❌ {host} -> DNS FAILED: {e}")
    
    # Check actual HTTP(S) connectivity
    print("\n🔌 HTTPS connectivity:")
    test_urls = [
        ('https://api.anthropic.com', 'Anthropic API'),
        ('https://api.openai.com', 'OpenAI API'),
        ('https://httpbin.org/get', 'httpbin (general internet)'),
    ]
    for url, name in test_urls:
        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'connectivity-test/1.0')
            resp = urllib.request.urlopen(req, timeout=10)
            print(f"  ✅ {name} ({url}) -> HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            # HTTP error means we CAN connect (just got an error response)
            print(f"  ✅ {name} ({url}) -> HTTP {e.code} (connection OK, auth expected)")
        except Exception as e:
            print(f"  ❌ {name} ({url}) -> {type(e).__name__}: {e}")
    
    # Check httpx (used by anthropic SDK)
    print("\n🔧 httpx connectivity test:")
    try:
        import httpx
        print(f"  httpx version: {httpx.__version__}")
        with httpx.Client(timeout=10) as client:
            resp = client.get("https://api.anthropic.com")
            print(f"  ✅ httpx -> HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ httpx -> {type(e).__name__}: {e}")
    
    print("=" * 50)

# ============ End Diagnostics ============

# Import and launch interface
from interface import create_gradio_interface

# Create Gradio interface (at module level for HF Spaces)
demo = create_gradio_interface()

if __name__ == "__main__":
    # Run diagnostics only when executed directly
    run_network_diagnostics()
    
    print("🚀 Starting Legal Position AI Analyzer...")
    
    # Detect if running on HF Spaces or locally
    is_hf_space = os.environ.get('SPACE_ID') is not None
    
    # Must call launch() explicitly — Gradio 6 does not auto-launch.
    # ssr_mode=False avoids the "shareable link" error on HF Spaces containers.
    if is_hf_space:
        # On HF Spaces, use fixed port 7860
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            ssr_mode=False,
        )
    else:
        # Locally, let Gradio find an available port
        demo.launch(
            share=False,
            show_error=True,
        )
