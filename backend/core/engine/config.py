# backend/core/engine/config.py
from pathlib import Path
import torch

# =====================================
# 프로젝트 경로 (Adjusted for backend/core/engine depth)
# =====================================
# From backend/core/engine/config.py -> backend/core -> backend -> root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# =====================================
# 디바이스 설정
# =====================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =====================================
# 이미지 생성 설정 (Z-Image-Turbo)
# =====================================
# 로컬 모델 경로
IMAGE_MODEL_ROOT = BASE_DIR / "models" / "image" / "Z-Image-Turbo"
# HuggingFace Repo ID (로컬 없을 때 사용)
IMAGE_MODEL_REPO = "Tongyi-MAI/Z-Image-Turbo"

# 기본 생성 파라미터 (1:1 정사각형)
DEFAULT_WIDTH = 576
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 9
DEFAULT_GUIDANCE_SCALE = 0.0

# =====================================
# 비디오 생성 설정 (SVD img2vid-xt)
# =====================================
# 로컬 모델 경로
VIDEO_MODEL_ROOT = BASE_DIR / "models" / "video" / "stable-video-diffusion-img2vid-xt"
# HuggingFace Repo ID
VIDEO_MODEL_REPO = "stabilityai/stable-video-diffusion-img2vid-xt"

# 기본 생성 파라미터 (9:16 세로 영상)
SVD_DEFAULT_WIDTH = 576
SVD_DEFAULT_HEIGHT = 1024
SVD_NUM_FRAMES = 24
SVD_FPS = 6
SVD_DECODE_CHUNK_SIZE = 2
SVD_MOTION_BUCKET_ID = 112
SVD_NOISE_AUG_STRENGTH = 0.015

# =====================================
# 업스케일 & 후처리 설정 (FFmpeg)
# =====================================
# 최종 목표 해상도 (쇼츠 9:16)
UPSCALE_TARGET_WIDTH = 1080
UPSCALE_TARGET_HEIGHT = 1920

# FFmpeg 품질 설정
FFMPEG_CRF = 18            # 낮을수록 고화질 (18-23 권장)
FFMPEG_PRESET = "slow"     # 인코딩 속도 vs 압축률 (slow가 화질/용량 이득)
SHARPEN_AMOUNT = 1.0       # unsharp 필터 강도

# =====================================
# 출력 디렉토리
# =====================================
OUTPUT_DIR = BASE_DIR / "output"
