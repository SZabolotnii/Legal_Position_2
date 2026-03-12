#!/usr/bin/env python3
"""
Hugging Face Spaces entry point for Legal Position AI Analyzer
"""
import os
import sys
import warnings
import logging
from pathlib import Path

# Suppress asyncio event loop __del__ warnings (known Python 3.11 issue in threaded envs)
warnings.filterwarnings("ignore", message=".*Invalid file descriptor.*")
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

# Suppress "Exception ignored in: BaseEventLoop.__del__" on HF Spaces shutdown
# warnings.filterwarnings does NOT catch these — they go via sys.unraisablehook
_original_unraisablehook = sys.unraisablehook

def _suppress_asyncio_fd_errors(unraisable):
    if (unraisable.exc_type is ValueError and
            "Invalid file descriptor" in str(unraisable.exc_value)):
        return  # silently ignore
    _original_unraisablehook(unraisable)

sys.unraisablehook = _suppress_asyncio_fd_errors

def configure_runtime_environment() -> None:
    """Apply runtime defaults for Hugging Face Spaces / Gradio deployment."""
    os.environ.setdefault('GRADIO_SERVER_NAME', '0.0.0.0')
    os.environ.setdefault('GRADIO_SERVER_PORT', '7860')
    os.environ.setdefault('UVICORN_LOOP', 'asyncio')


# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
configure_runtime_environment()

# Import and launch interface
from interface import create_gradio_interface
from main import initialize_components

# Initialize search components at module level (required for HF Spaces)
# On HF Spaces, __main__ block never runs, so this must be called here.
print("Initializing search components...")
_init_ok = initialize_components()
if _init_ok:
    print("Search components initialized successfully!")
else:
    print("[WARNING] Search components initialization failed. Search functionality will be limited.")

# Create Gradio interface (at module level for HF Spaces)
demo = create_gradio_interface()

if __name__ == "__main__":
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
