"""
Configuration module for the Shorts LLM pipeline.

Manages environment variables and default settings for the local LLM server.
"""

import os
from typing import Final

# Local LLM server configuration
LOCAL_LLM_BASE_URL: str = os.environ.get(
    "LOCAL_LLM_BASE_URL", "http://localhost:8000/v1"
)

# Default model identifier for the local Llama instance
DEFAULT_MODEL_NAME: Final[str] = "local-llama-3.1-8b-instruct"

# LLM generation defaults
DEFAULT_TEMPERATURE: Final[float] = 0.7
DEFAULT_MAX_TOKENS: Final[int] = 4096

# HTTP request timeout (seconds)
REQUEST_TIMEOUT: Final[int] = 120

# Logging configuration
LOG_LEVEL: str = os.environ.get("SHORTS_LLM_LOG_LEVEL", "INFO")
