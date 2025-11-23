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
    LLAMA_SERVER_PATH = ENGINE_DIR / "llama.cpp" / "build" / "bin" / "llama-server"

    # Model paths
    MODEL_DIR = ROOT_DIR / "models"
    LLAMA_MODEL_PATH = MODEL_DIR / "llama-3.1-8b"

    # Output paths
    OUTPUT_DIR = ROOT_DIR / "output"
    CLIPS_DIR = OUTPUT_DIR / "clips"
    IMAGES_DIR = OUTPUT_DIR / "images"
    LOGS_DIR = OUTPUT_DIR / "logs"
    PROMPTS_DIR = OUTPUT_DIR / "prompts"

    # llama-server configuration
    LLAMA_SERVER_HOST = os.getenv("LLAMA_SERVER_HOST", "127.0.0.1")
    LLAMA_SERVER_PORT = int(os.getenv("LLAMA_SERVER_PORT", "8080"))
    LLAMA_SERVER_URL = f"http://{LLAMA_SERVER_HOST}:{LLAMA_SERVER_PORT}"

    # llama-server 최적화 파라미터 (CPU 전용 환경)
    LLAMA_CTX_SIZE = int(os.getenv("LLAMA_CTX_SIZE", "1024"))  # 4096 → 1024 (메모리 절감)
    LLAMA_BATCH_SIZE = int(os.getenv("LLAMA_BATCH_SIZE", "512"))
    LLAMA_N_PARALLEL = int(os.getenv("LLAMA_N_PARALLEL", "4"))  # 동시 요청 수

    # LLM parameters (클라이언트 요청 시 사용)
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))  # 2048 → 1024 (짧은 스토리에 충분)
    LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
    LLM_THREADS = int(os.getenv("LLM_THREADS", "8"))  # 4 → 8 (CPU 활용도 향상)

    # HTTP 요청 타임아웃 (초)
    LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "120"))  # 2분
    LLM_CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", "10"))  # 10초

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
