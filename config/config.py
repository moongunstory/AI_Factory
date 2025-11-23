"""
AI Shorts Factory - 설정 모듈

프로젝트 경로, 모델 경로, LLM 서버 설정 등 관리
"""

import os
from pathlib import Path
from typing import Final

# ============================================================================
# 프로젝트 경로
# ============================================================================

# 프로젝트 루트 디렉토리 (이 파일 기준)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 모델 디렉토리 (사용자의 Llama 모델 위치)
MODELS_DIR = PROJECT_ROOT / "models"
LLAMA_MODEL_PATH = MODELS_DIR / "llama-3.1-8b-instruct" / "Llama3.1-8B-Instruct"

# 데이터 디렉토리
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
IMAGES_DIR = DATA_DIR / "images"
VIDEOS_DIR = DATA_DIR / "videos"

# 디렉토리 자동 생성
for directory in [DATA_DIR, OUTPUT_DIR, IMAGES_DIR, VIDEOS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# LLM 서버 설정
# ============================================================================

# 로컬 LLM 서버 베이스 URL
# llama.cpp, vLLM, Text Generation WebUI 등에서 제공하는 OpenAI 호환 API
LOCAL_LLM_BASE_URL: str = os.environ.get(
    "LOCAL_LLM_BASE_URL",
    "http://localhost:8000/v1"
)

# 기본 모델 이름 (로컬 서버에서 사용하는 식별자)
DEFAULT_MODEL_NAME: Final[str] = os.environ.get(
    "LLM_MODEL_NAME",
    "local-llama-3.1-8b-instruct"
)

# LLM 생성 기본값
DEFAULT_TEMPERATURE: Final[float] = 0.7
DEFAULT_MAX_TOKENS: Final[int] = 4096

# HTTP 요청 타임아웃 (초)
REQUEST_TIMEOUT: Final[int] = 180  # 3분 (긴 생성 고려)

# ============================================================================
# 이미지 생성 설정
# ============================================================================

# Stable Diffusion / ComfyUI 서버 URL
IMAGE_GEN_API_URL: str = os.environ.get(
    "IMAGE_GEN_API_URL",
    "http://localhost:7860"  # Automatic1111 WebUI 기본 포트
)

# 기본 이미지 해상도 (9:16 세로형)
DEFAULT_IMAGE_WIDTH: Final[int] = 720
DEFAULT_IMAGE_HEIGHT: Final[int] = 1280

# 기본 생성 파라미터
DEFAULT_IMAGE_STEPS: Final[int] = 30
DEFAULT_CFG_SCALE: Final[float] = 7.5
DEFAULT_SAMPLER: Final[str] = "DPM++ 2M Karras"

# ============================================================================
# 비디오 생성 설정
# ============================================================================

# FFmpeg 설정
FFMPEG_PATH: str = os.environ.get("FFMPEG_PATH", "ffmpeg")

# 기본 비디오 설정
DEFAULT_VIDEO_FPS: Final[int] = 24
DEFAULT_VIDEO_CODEC: Final[str] = "libx264"
DEFAULT_AUDIO_CODEC: Final[str] = "aac"
DEFAULT_VIDEO_BITRATE: Final[str] = "5M"

# ============================================================================
# 로깅 설정
# ============================================================================

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# 유틸리티 함수
# ============================================================================

def get_model_info() -> dict:
    """모델 정보 반환"""
    return {
        "model_path": str(LLAMA_MODEL_PATH),
        "exists": LLAMA_MODEL_PATH.exists(),
        "server_url": LOCAL_LLM_BASE_URL,
        "model_name": DEFAULT_MODEL_NAME,
    }


def get_paths_info() -> dict:
    """프로젝트 경로 정보 반환"""
    return {
        "project_root": str(PROJECT_ROOT),
        "models_dir": str(MODELS_DIR),
        "data_dir": str(DATA_DIR),
        "output_dir": str(OUTPUT_DIR),
        "images_dir": str(IMAGES_DIR),
        "videos_dir": str(VIDEOS_DIR),
    }


if __name__ == "__main__":
    # 설정 확인용
    print("=== AI Shorts Factory Configuration ===")
    print("\n[Model Info]")
    for key, value in get_model_info().items():
        print(f"  {key}: {value}")

    print("\n[Paths]")
    for key, value in get_paths_info().items():
        print(f"  {key}: {value}")

    print("\n[LLM Settings]")
    print(f"  Temperature: {DEFAULT_TEMPERATURE}")
    print(f"  Max Tokens: {DEFAULT_MAX_TOKENS}")

    print("\n[Image Generation]")
    print(f"  API URL: {IMAGE_GEN_API_URL}")
    print(f"  Resolution: {DEFAULT_IMAGE_WIDTH}x{DEFAULT_IMAGE_HEIGHT}")
