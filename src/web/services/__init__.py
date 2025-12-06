"""AI Short Factory - Backend Services

This package contains service modules for:
- ComfyUI (SDXL image generation)
- Stable Video Diffusion (image-to-video generation)
- Llama-server (story & scene generation with multi-layer pipeline)
- Full pipeline orchestration
"""

from .integrated_story_client import IntegratedStoryClient
from .comfy_client import ComfyUIClient
from .pipeline import generate_short

# Legacy client (deprecated - use IntegratedStoryClient instead)
from .llama_client import LlamaStoryClient

__all__ = [
    'IntegratedStoryClient',
    'ComfyUIClient',
    'generate_short',
    'LlamaStoryClient',  # Deprecated - kept for backward compatibility
]
