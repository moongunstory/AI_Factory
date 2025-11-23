"""Configuration management for AI Short Factory."""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Global configuration for AI Short Factory."""

    # Project root directory
    ROOT_DIR = Path(__file__).parent.parent.parent

    # Engine paths
    ENGINE_DIR = ROOT_DIR / "engine"
    LLAMA_CPP_PATH = ENGINE_DIR / "llama.cpp" / "build" / "bin" / "llama-cli"

    # Model paths
    MODEL_DIR = ROOT_DIR / "models"
    LLAMA_MODEL_PATH = MODEL_DIR / "llama-3.1-8b"

    # Output paths
    OUTPUT_DIR = ROOT_DIR / "output"
    CLIPS_DIR = OUTPUT_DIR / "clips"
    IMAGES_DIR = OUTPUT_DIR / "images"
    LOGS_DIR = OUTPUT_DIR / "logs"
    PROMPTS_DIR = OUTPUT_DIR / "prompts"

    # LLM parameters
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
    LLM_THREADS = int(os.getenv("LLM_THREADS", "4"))

    @classmethod
    def ensure_output_dirs(cls) -> None:
        """Create output directories if they don't exist."""
        for dir_path in [cls.CLIPS_DIR, cls.IMAGES_DIR, cls.LOGS_DIR, cls.PROMPTS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_model_file(cls, model_name: Optional[str] = None) -> Path:
        """Get the path to the GGUF model file."""
        model_dir = cls.LLAMA_MODEL_PATH if model_name is None else cls.MODEL_DIR / model_name

        # Find .gguf file in the model directory
        gguf_files = list(model_dir.glob("*.gguf"))
        if not gguf_files:
            raise FileNotFoundError(f"No .gguf file found in {model_dir}")

        return gguf_files[0]
