"""Configuration management for AI Short Factory."""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Global configuration for AI Short Factory."""

    # Project root directory
    ROOT_DIR = Path(__file__).parent.parent.parent

    # Engine paths (Windows GPU)
    ENGINE_DIR = ROOT_DIR / "engine"
    LLAMA_CPP_PATH = ENGINE_DIR / "llama.cpp" / "build" / "bin" / "Release" / "llama-cli.exe"
    LLAMA_SERVER_PATH = ENGINE_DIR / "llama.cpp" / "build" / "bin" / "Release" / "llama-server.exe"

    # Model paths
    MODEL_DIR = ROOT_DIR / "models"
    LLAMA_MODEL_PATH = MODEL_DIR / "solar-10.7b"

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

    # llama-server 최적화 파라미터 (GPU 지원)
    LLAMA_CTX_SIZE = int(os.getenv("LLAMA_CTX_SIZE", "4096"))  # GPU 환경: 더 큰 컨텍스트 가능
    LLAMA_BATCH_SIZE = int(os.getenv("LLAMA_BATCH_SIZE", "2048"))  # GPU 환경: 큰 배치 크기
    LLAMA_N_PARALLEL = int(os.getenv("LLAMA_N_PARALLEL", "1"))  # GPU: 더 많은 동시 요청 처리
    LLAMA_N_GPU_LAYERS = int(os.getenv("LLAMA_N_GPU_LAYERS", "-1"))  # -1 = 모든 레이어를 GPU에 로드

    # LLM parameters (클라이언트 요청 시 사용)
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))  # GPU: 더 긴 출력 가능
    LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
    LLM_THREADS = int(os.getenv("LLM_THREADS", "4"))  # GPU 환경: CPU 스레드는 적게 사용

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
