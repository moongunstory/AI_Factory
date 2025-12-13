# backend/core/engine/utils.py
from __future__ import annotations
from pathlib import Path
import re
import torch
from datetime import datetime
from typing import Union
from .config import (
    BASE_DIR, 
    IMAGE_MODEL_ROOT, 
    IMAGE_MODEL_REPO,
    VIDEO_MODEL_ROOT,
    VIDEO_MODEL_REPO,
    DEVICE
)


# =====================================
# 기존 유틸 함수들
# =====================================

def ensure_dir(path: Union[str, Path]) -> Path:
    """폴더가 없으면 생성하고 Path 반환."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def slugify(text: str, max_len: int = 50) -> str:
    """
    프롬프트를 파일명에 쓸 수 있게 정리.
    한글/영문/숫자/공백 정도만 남기고 나머지 날림.
    """
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"[^0-9a-zA-Z가-힣_]+", "", text)
    return text[:max_len] if len(text) > max_len else text


def default_output_path(prompt: str) -> Path:
    """
    프롬프트 기반 기본 출력 경로 생성.
    예: output/zimage_20251210_193000_벚꽃공원.png
    """
    out_dir = ensure_dir(BASE_DIR / "output")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = slugify(prompt, max_len=30)
    filename = f"zimage_{ts}_{name or 'image'}.png"
    return out_dir / filename


# =====================================
# 모델 경로 해결 함수들
# =====================================

def resolve_image_model() -> tuple[str, str | None]:
    """
    이미지 모델(Z-Image-Turbo) 경로 찾기
    
    Returns:
        tuple: (model_id, cache_dir)
            - 로컬에 있으면: (로컬 경로, None)
            - 없으면: (HuggingFace repo ID, 캐시 경로)
    """
    root = IMAGE_MODEL_ROOT
    
    # 직접 model_index.json이 있는지 확인
    direct_index = root / "model_index.json"
    if direct_index.exists():
        print(f"✓ 로컬 이미지 모델 발견: {root}")
        return str(root.resolve()), None
    
    # snapshots 폴더 안에 있는지 확인
    snapshots_dir = root / "snapshots"
    if snapshots_dir.exists():
        for sub in snapshots_dir.iterdir():
            if sub.is_dir() and (sub / "model_index.json").exists():
                print(f"✓ 로컬 이미지 모델 발견: {sub}")
                return str(sub.resolve()), None
    
    # 로컬에 없으면 HuggingFace에서 다운로드 (캐시 경로 지정)
    # 3. HF Cache 구조 확인 (models--org--repo)
    safe_repo_id = IMAGE_MODEL_REPO.replace("/", "--")
    hf_cache_dir = root / f"models--{safe_repo_id}"
    if hf_cache_dir.exists():
         print(f"✓ 로컬 이미지 모델 발견 (HF Cache): {hf_cache_dir}")
         return IMAGE_MODEL_REPO, str(root.resolve())

    print(f"⚠ 로컬 이미지 모델 없음. HuggingFace에서 다운로드 시작...")
    print(f"  다운로드 위치: {root}")
    ensure_dir(root)  # 폴더 생성
    return IMAGE_MODEL_REPO, str(root.resolve())


def resolve_video_model() -> tuple[str, str | None]:
    """
    비디오 모델(SVD) 경로 찾기
    
    Returns:
        tuple: (model_id, cache_dir)
            - 로컬에 있으면: (로컬 경로, None)
            - 없으면: (HuggingFace repo ID, 캐시 경로)
    """
    root = VIDEO_MODEL_ROOT
    
    # 직접 model_index.json이 있는지 확인
    direct_index = root / "model_index.json"
    if direct_index.exists():
        print(f"✓ 로컬 비디오 모델 발견: {root}")
        return str(root.resolve()), None
    
    # snapshots 폴더 안에 있는지 확인
    snapshots_dir = root / "snapshots"
    if snapshots_dir.exists():
        for sub in snapshots_dir.iterdir():
            if sub.is_dir() and (sub / "model_index.json").exists():
                print(f"✓ 로컬 비디오 모델 발견: {sub}")
                return str(sub.resolve()), None
    
    # 로컬에 없으면 HuggingFace에서 다운로드 (캐시 경로 지정)
    # 3. HF Cache 구조 확인 (models--org--repo)
    # 예: models--stabilityai--stable-video-diffusion-img2vid-xt
    safe_repo_id = VIDEO_MODEL_REPO.replace("/", "--")
    hf_cache_dir = root / f"models--{safe_repo_id}"
    if hf_cache_dir.exists():
         print(f"✓ 로컬 비디오 모델 발견 (HF Cache): {hf_cache_dir}")
         # HF Cache가 있으면 그대로 Repo ID와 Cache Dir 반환하면 from_pretrained가 알아서 함
         return VIDEO_MODEL_REPO, str(root.resolve())

    print(f"⚠ 로컬 비디오 모델 없음. HuggingFace에서 다운로드 시작...")
    print(f"  다운로드 위치: {root}")
    ensure_dir(root)  # 폴더 생성
    return VIDEO_MODEL_REPO, str(root.resolve())


def get_optimal_dtype() -> torch.dtype:
    """
    GPU 성능에 따라 최적 데이터 타입 선택
    
    Returns:
        torch.dtype: bfloat16 (SM 8.0+), float16 (CUDA), float32 (CPU)
    """
    if DEVICE == "cuda":
        major, minor = torch.cuda.get_device_capability()
        if major >= 8:
            return torch.bfloat16
        else:
            return torch.float16
    return torch.float32
