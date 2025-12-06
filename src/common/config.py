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
    LLAMA_MODEL_PATH = MODEL_DIR / "llm" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M"
    SDXL_BASE_MODEL = "sd_xl_base_1.0.safetensors"
    SDXL_REFINER_MODEL = "sd_xl_refiner_1.0.safetensors"

    # Output paths
    OUTPUT_DIR = ROOT_DIR / "output"
    # Project-scoped roots
    ONESHOT_DIR = OUTPUT_DIR / "oneshot"
    SERIES_DIR = OUTPUT_DIR / "series"
    MEME_DIR = OUTPUT_DIR / "meme"

    # Legacy paths (kept for backward compatibility where needed)
    CLIPS_DIR = OUTPUT_DIR / "clips"
    IMAGES_DIR = OUTPUT_DIR / "images"
    VIDEO_SEGMENTS_DIR = OUTPUT_DIR / "video_segments"
    FINAL_DIR = OUTPUT_DIR / "final"
    LOGS_DIR = OUTPUT_DIR / "logs"
    PROMPTS_DIR = OUTPUT_DIR / "prompts"

    # ComfyUI configuration
    COMFYUI_HOST = os.getenv("COMFYUI_HOST", "127.0.0.1")
    COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", "8188"))
    COMFYUI_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"
    WAN22_WORKFLOW_TEMPLATE = (
        ROOT_DIR
        / "engine"
        / "comfyui"
        / "venv"
        / "Lib"
        / "site-packages"
        / "comfyui_workflow_templates_media_video"
        / "templates"
        / "video_wan2_2_14B_i2v.json"
    )

    # ComfyUI VRAM optimization settings
    COMFYUI_LOW_VRAM = os.getenv("COMFYUI_LOW_VRAM", "true").lower() == "true"
    COMFYUI_USE_REFINER = os.getenv("COMFYUI_USE_REFINER", "false").lower() == "true"  # Refiner는 기본적으로 비활성화
    COMFYUI_RESOLUTION_MODE = os.getenv("COMFYUI_RESOLUTION_MODE", "low")  # "low" (768px) or "high" (1080px)
    COMFYUI_TIMEOUT = int(os.getenv("COMFYUI_TIMEOUT", "0"))  # 0 = 무제한 (타임아웃 없음)
    COMFYUI_MAX_RETRIES = int(os.getenv("COMFYUI_MAX_RETRIES", "2"))  # 최대 재시도 횟수

    # Video generation optimization settings
    VIDEO_USE_UPSCALE = os.getenv("VIDEO_USE_UPSCALE", "true").lower() == "true"  # 저해상도 + 업스케일 전략
    VIDEO_BASE_WIDTH = int(os.getenv("VIDEO_BASE_WIDTH", "512"))  # 기본 생성 해상도 (낮은 해상도로 빠른 생성)
    VIDEO_BASE_HEIGHT = int(os.getenv("VIDEO_BASE_HEIGHT", "288"))  # 16:9 비율 유지
    VIDEO_TARGET_WIDTH = int(os.getenv("VIDEO_TARGET_WIDTH", "1024"))  # 최종 타겟 해상도
    VIDEO_TARGET_HEIGHT = int(os.getenv("VIDEO_TARGET_HEIGHT", "576"))  # 16:9 비율 유지

    # Image generation parameters (optimized for stability)
    IMAGE_STEPS_MIN = int(os.getenv("IMAGE_STEPS_MIN", "28"))
    IMAGE_STEPS_MAX = int(os.getenv("IMAGE_STEPS_MAX", "32"))
    IMAGE_CFG_MIN = float(os.getenv("IMAGE_CFG_MIN", "5.5"))
    IMAGE_CFG_MAX = float(os.getenv("IMAGE_CFG_MAX", "6.2"))
    IMAGE_REFINER_STEPS = int(os.getenv("IMAGE_REFINER_STEPS", "15"))  # Refiner 사용 시

    # Resolution settings
    IMAGE_WIDTH_LOW = int(os.getenv("IMAGE_WIDTH_LOW", "768"))
    IMAGE_HEIGHT_LOW = int(os.getenv("IMAGE_HEIGHT_LOW", "1365"))  # 16:9 비율 유지
    IMAGE_WIDTH_HIGH = int(os.getenv("IMAGE_WIDTH_HIGH", "1080"))
    IMAGE_HEIGHT_HIGH = int(os.getenv("IMAGE_HEIGHT_HIGH", "1920"))

    # llama-server configuration
    LLAMA_SERVER_HOST = os.getenv("LLAMA_SERVER_HOST", "127.0.0.1")
    LLAMA_SERVER_PORT = int(os.getenv("LLAMA_SERVER_PORT", "8080"))
    LLAMA_SERVER_URL = f"http://{LLAMA_SERVER_HOST}:{LLAMA_SERVER_PORT}"

    # llama-server 최적화 파라미터 (단일 사용자 로컬 환경)
    LLAMA_CTX_SIZE = int(os.getenv("LLAMA_CTX_SIZE", "8192"))  # 단일 요청 전체 컨텍스트 (increased for long prompts)
    LLAMA_BATCH_SIZE = int(os.getenv("LLAMA_BATCH_SIZE", "512"))  # 단일 요청 최적화 (메모리 효율)
    LLAMA_N_PARALLEL = 1  # 단일 슬롯 강제 (환경변수 무시)
    LLAMA_N_GPU_LAYERS = int(os.getenv("LLAMA_N_GPU_LAYERS", "-1"))  # -1 = 모든 레이어를 GPU에 로드

    # LLM parameters (클라이언트 요청 시 사용)
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))  # 단일 요청 최대 토큰
    LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
    LLM_THREADS = int(os.getenv("LLM_THREADS", "4"))  # CPU 보조 스레드 (GPU 메인)

    # HTTP 요청 타임아웃 (초)
    LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "120"))  # 2분
    LLM_CONNECT_TIMEOUT = int(os.getenv("LLM_CONNECT_TIMEOUT", "10"))  # 10초

    @classmethod
    def ensure_output_dirs(cls) -> None:
        """Create output directories if they don't exist."""
        for dir_path in [
            cls.ONESHOT_DIR,
            cls.SERIES_DIR,
            cls.MEME_DIR,
            cls.LOGS_DIR,
            cls.PROMPTS_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # ensure standard sub-structure for new projects
        for base in (cls.ONESHOT_DIR, cls.SERIES_DIR, cls.MEME_DIR):
            for child in ("story", "prompts", "images", "video", "audio"):
                (base / child).mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_model_file(cls, model_name: Optional[str] = None) -> Path:
        """Get the path to the GGUF model file."""
        model_dir = cls.LLAMA_MODEL_PATH if model_name is None else cls.MODEL_DIR / model_name

        # Find .gguf file in the model directory
        gguf_files = list(model_dir.glob("*.gguf"))
        if not gguf_files:
            raise FileNotFoundError(f"No .gguf file found in {model_dir}")

        return gguf_files[0]
